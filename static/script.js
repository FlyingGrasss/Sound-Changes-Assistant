// Handle form submission for the analysis
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
                console.log(item); // Log the item for debugging

                // Split suffix_display by both "|" and "+" in one step using a regular expression
                let suffixParts = item.suffix_display.split(/[+|]/);

                console.log(suffixParts); // ["yap", "tık", "lar", "ımız"] for input "yap|tık+lar+ımız"

                // Join the parts with hyphens
                const formattedSuffix = suffixParts.join('-');

                console.log(formattedSuffix); // "yap-tık-lar-ımız" for input "yap|tık+lar+ımız"

                if (item.suffix_kinds[0] == "Fiil") {
                    displayArea.innerHTML += `
                    <div style="text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
                        Kelimenin Kökü: ${item.normalized_root}
                    </div>
                `;
                } else {
                    suffixParts[0] = item.normalized_root
                }
                
                // First Row: Display `suffix_display` as a single string without spaces
                displayArea.innerHTML += `
                    <div style="text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
                        ${suffixParts.join('-') || item.root}
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

// Handle live suggestions as user types
const input = document.querySelector("#input");
const suggestionBox = document.querySelector("#suggestions");
const button = document.querySelector("#button");
input.addEventListener("input", async (e) => {
    const query = e.target.value;

    if (query) {
        // Fetch suggestions dynamically from the backend
        const response = await fetch(`/suggest?q=${query}`);
        const suggestions = await response.json();
        updateSuggestions(suggestions);
    } else {
        // Clear suggestions if the input is empty
        clearSuggestions();
    }
});
button.addEventListener("click", () => {
    clearSuggestions();
});
function updateSuggestions(suggestions) {
    // If there are suggestions, show the suggestion box
    if (suggestions.length > 0) {
        suggestionBox.style.display = "block";
        suggestionBox.innerHTML = suggestions
            .map(suggestion => `<div>${suggestion}</div>`)
            .join("");
        addSuggestionListeners();
    } else {
        clearSuggestions();
    }
}

function clearSuggestions() {
    // Hide the suggestion box and clear its content
    suggestionBox.style.display = "none";
    suggestionBox.innerHTML = "";
}

function addSuggestionListeners() {
    const items = document.querySelectorAll("#suggestions div");
    items.forEach(item => {
        item.addEventListener("click", () => {
            input.value = item.textContent;
            clearSuggestions();
        });
    });
}



