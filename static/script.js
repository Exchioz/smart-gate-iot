function refreshPage() {
    location.reload();
}
var timeInSeconds = 120;

function updateCountdown() {
    var countdownElement = document.getElementById('countdown');

    var minutes = Math.floor(timeInSeconds / 60);
    var seconds = timeInSeconds % 60;

    if (timeInSeconds < 0) {
        var countdownText = 'QR Code Expired!';
        document.getElementById('refreshButton').disabled = false;
    } else {
        var countdownText = `${minutes} menit ${seconds} detik`;

        timeInSeconds--;
        setTimeout(updateCountdown, 1000);
    }
    countdownElement.textContent = countdownText;
}
updateCountdown();