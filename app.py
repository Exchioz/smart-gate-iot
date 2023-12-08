from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import string
import random
import cv2
import numpy as np
import pyzbar.pyzbar as pyzbar
from flask_socketio import SocketIO,emit
import threading
from datetime import datetime
import time
import urllib.request
from flask import Flask
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
mysql = MySQL(app)
socketio = SocketIO(app)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'gaiot'

urlesp32cam = 'http://192.168.1.41'
urlesp32 = 'http://192.168.1.38'

with app.app_context():
    cursor = mysql.connection.cursor()
    cursor.execute("SET GLOBAL event_scheduler = ON")
    mysql.connection.commit()

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

latest_qr_code = None
@socketio.on('get_qr_code')
def get_latest_qr_code():
    socketio.emit('latest_qr_code', {'data': latest_qr_code})

def move_servo():
    requests.get(urlesp32+'/open-gate')

def qr_code_detection():
    #cap = cv2.VideoCapture(0)
    font = cv2.FONT_HERSHEY_PLAIN
    prev=""
    data=""

    while True:
        img_resp=urllib.request.urlopen(urlesp32cam+'/cam-mid.jpg')
        imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
        frame=cv2.imdecode(imgnp,-1)
        #_, frame = cap.read()

        decodedObjects = pyzbar.decode(frame)
        for obj in decodedObjects:
            data = obj.data.decode('utf-8')
            if prev == data:
                pass
            else:
                print("Data: ", data)
                user_id = check_token_in_database(data)
                if check_token_in_database(data):
                    global latest_qr_code
                    latest_qr_code = data
                    socketio.emit('alert', {'message': 'QR Code Detected!'})
                    threading.Thread(target=move_servo).start()
                    add_to_activity(user_id)
                prev=data
            cv2.putText(frame, str(data), (50, 50), font, 2,
                        (255, 0, 0), 3)

        cv2.imshow("Live Transmission", frame)

        key = cv2.waitKey(1)
        if key == 27:
            break

    cv2.destroyAllWindows()

def check_token_in_database(token):
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT id FROM users WHERE token = '{token}'")
        result = cursor.fetchone()
        return result[0] if result else None
    
def add_to_activity(user_id):
    with app.app_context():
        cursor = mysql.connection.cursor()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(f"INSERT INTO activity (user_id, scanned_time) VALUES ({user_id}, '{current_time}')")
        mysql.connection.commit()
        time.sleep(5)
        
class EventScheduler:
    def __init__(self, db):
        self.db = db
    
    def schedule_token_cleanup_by_id(self, user_id):
        event_name = f"delete_tokens_user_{user_id}"

        check_event_query = f"SHOW EVENTS LIKE '{event_name}'"
        cursor = self.db.cursor()
        cursor.execute(check_event_query)

        result = cursor.fetchall()

        if not result:
            sql = f"CREATE EVENT {event_name} \
                    ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 2 MINUTE \
                    ON COMPLETION PRESERVE \
                    DO \
                    BEGIN \
                        UPDATE users SET token = NULL WHERE id = '{user_id}'; \
                        IF (SELECT token FROM users WHERE id = '{user_id}') IS NULL THEN \
                            DROP EVENT {event_name}; \
                        END IF; \
                    END"
            cursor.execute(sql)
            self.db.commit()

    def delete_token_and_event(self, user_id):
        event_name = f"delete_tokens_user_{user_id}"
        delete_event_query = f"DROP EVENT IF EXISTS {event_name}"
        self.db.cursor().execute(delete_event_query)

        update_token_query = f"UPDATE users SET token = NULL WHERE id = {user_id}"
        self.db.cursor().execute(update_token_query)
        self.db.commit()
    
    def generate_unique_token():
        N = 15
        res = ''.join(random.choices(string.ascii_letters, k=N))
        return str(res)


@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return redirect(url_for('index'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/index')
def index():
    if 'loggedin' in session:
        user_id = session['id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT token FROM users WHERE id = {user_id}")
        token = cursor.fetchone()['token']

        if token is not None:
            mysql.connection.cursor().execute(f"UPDATE users SET token = NULL WHERE id = {user_id}")
            event_scheduler = EventScheduler(mysql.connection)
            event_scheduler.delete_token_and_event(user_id)
            mysql.connection.commit()

        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_details = cursor.fetchone()

        if user_details:
            return render_template('index.html', user_details=user_details)
        else:
            return 'Error: User details not found!'
    else:
        return redirect(url_for('login'))

@app.route('/qr_code')
def qr_code():
    if 'loggedin' in session:
        user_id = session['id']
        token = EventScheduler.generate_unique_token()

        update_query = f"UPDATE users SET token = '{token}' WHERE id = '{user_id}'"
        mysql.connection.cursor().execute(update_query)

        event_scheduler = EventScheduler(mysql.connection)
        event_scheduler.schedule_token_cleanup_by_id(user_id)

        mysql.connection.commit()
        return render_template('qr_code.html', token=token)
    else:
        return redirect(url_for('login'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    qr_thread = threading.Thread(target=qr_code_detection)
    qr_thread.start()
    socketio.run(app)
