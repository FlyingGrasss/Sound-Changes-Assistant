document.getElementById('inputForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/process', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('resultText').textContent = data.result;
        document.getElementById('resultDiv').style.display = 'block';
    })
    .catch(error => console.error('Error:', error));
});