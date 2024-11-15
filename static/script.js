document.getElementById('inputForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    fetch('/process', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            const displayArea = document.getElementById('resultText');
            displayArea.innerHTML = ''; // Clear previous results

            data.result.forEach(item => {
                // Declare suffixParts outside the if/else block
                let suffixParts = [];

                // Split suffix_display by "+" or "|" to get each part
                if (item.suffix_display.includes("+")) { 
                    suffixParts = item.suffix_display.split('+');
                    if (suffixParts[0].includes("|")) { 
                        suffixParts = suffixParts[0].split("|").concat(suffixParts.slice(1));
                    }
                } else if (item.suffix_display.includes("|")) { 
                    suffixParts = item.suffix_display.split('|');
                }
                
                // First Row: Display `suffix_display` as a single string without spaces
                displayArea.innerHTML += `
                    <div style="text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
                        ${suffixParts.join('-')}
                    </div>
                `;

                // Second Row: Display each suffix part with flexible spacing between them
                displayArea.innerHTML += `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px;">
                        ${suffixParts.map(part => `
                            <div style="font-size: 20px; font-weight: bolder; width: 133.33px;">${part}</div>
                        `).join('')}
                    </div>
                `;

                // Third Row: Display suffix kinds aligned below each part
                displayArea.innerHTML += `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px;">
                        ${item.suffix_kinds.map(kind => `
                            <div style="font-size: 15px; font-weight: bold; width: 133.33px;">${kind}</div>
                        `).join('')}
                    </div>
                `;

                // Fourth Row: Display sound changes or "Ses Olayı Bulunamadı"
                displayArea.innerHTML += `
                    <p style="text-align: center; color: #555; font-style: italic; margin-top: 10px;">
                        ${item.sound_events.length > 0 ? 
                            `Bu kelimede  <span style="font-weight: bold;">${item.sound_events.join(', ')}</span> ses olayları bulundu.` : 
                            "Ses Olayı Bulunamadı"}
                    </p>
                `;
                //displayArea.innerHTML += `
                //    <p>
                //        ${item.analysis}
                //    </p>
                //`;
            });

            document.getElementById('resultDiv').style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
});
