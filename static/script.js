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
        console.log(data);
        const displayArea = document.getElementById('resultText');
        displayArea.innerHTML = '';
        
        if (data.results && data.results.length > 0) {
            data.results.forEach((item, index) => {
            let suffixParts = [];
            if (item.suffix_display.includes("+")) {
                suffixParts = item.suffix_display.split('+');
                for (let i = 0; i < suffixParts.length; i++) {
                if (suffixParts[i].includes("|")) {
                    const suffixPartSplit = suffixParts[i].split("|");
                    suffixParts = [...suffixParts.slice(0, i), ...suffixPartSplit];
                }
                }
            } else if (item.suffix_display.includes("|")) {
                suffixParts = item.suffix_display.split('|');
            }
            
            suffixParts[0] = item.normalized_root;
            
            const slide = document.createElement('div');
            slide.innerHTML = `
                <div class="analysis-container" style="margin-bottom: 15px;">
                <h3 style="margin-bottom: 15px; color: #444;">Çözümleme ${index + 1}:</h3>
                <div style="text-align: center; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
                    ${suffixParts.join('-')}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px;">
                    ${suffixParts.map(part => `
                    <div style="font-size: 20px; font-weight: bolder; width: ${300/suffixParts.length}%; text-align: center;">${part}</div>
                    `).join('')}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin: 5px;">
                    ${item.suffix_kinds.map(kind => `
                    <div style="font-size: 15px; font-weight: bold; width: ${300/suffixParts.length}%; padding: 0 10px; text-align: center;">${kind}</div>
                    `).join('')}
                </div>
                <p style="text-align: center; color: #555; font-style: italic; margin-top: 10px;">
                    ${item.sound_events.length > 0 ? 
                    `Bu kelimede <span style="font-weight: bold;">${item.sound_events.join(', ')}</span> ses olayları bulundu.` : 
                    "Ses Olayı Bulunamadı"}
                </p>
                ${/*
                <p style="font-size: 12px; color: #888; margin-top: 10px;">
                    ${item.analysis}
                </p>
                */""}
                </div>
            `;
            displayArea.appendChild(slide);
            });
        } else {
            displayArea.innerHTML = '<div><p style="text-align: center; color: #888;">Sonuç bulunamadı</p></div>';
        }
        document.getElementById('resultDiv').style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('resultText').innerHTML = '<p style="text-align: center; color: red;">Bir hata oluştu</p>';
    });
});


// Handle live suggestions as user types
const input = document.querySelector("#input");
const suggestionBox = document.querySelector("#suggestions");
const button = document.querySelector("#button");
input.addEventListener("input", async (e) => {
    const query = e.target.value;
    if (query) {
        const response = await fetch(`/suggest?q=${query}`);
        const suggestions = await response.json();
        updateSuggestions(suggestions);
    } else {
        clearSuggestions();
    }
});
button.addEventListener("click", () => {
    clearSuggestions();
});
function updateSuggestions(suggestions) {
    if (suggestions.length > 0) {
        suggestionBox.style.display = "block";
        suggestionBox.innerHTML = suggestions
            .map(suggestion => `<div class="suggestion-item">${suggestion}</div>`)
            .join("");
        addSuggestionListeners();
    } else {
        clearSuggestions();
    }
}
function clearSuggestions() {
    suggestionBox.style.display = "none";
    suggestionBox.innerHTML = "";
}
function addSuggestionListeners() {
    const items = document.querySelectorAll("#suggestions div");
    items.forEach(item => {
        item.addEventListener("click", () => {
            input.value = item.textContent;
            clearSuggestions();
            document.getElementById('inputForm').dispatchEvent(new Event('submit'));
        });
    });
}






// Slide navigation function
function moveSlide(direction) {
    const slides = document.querySelector('.slides');
    const currentScroll = slides.scrollLeft;
    const slideWidth = slides.clientWidth; // Width of one slide
    slides.scrollTo({
      left: currentScroll + (direction * slideWidth),
      behavior: 'smooth'
    });
  }
  
  // Optional: Disable buttons at scroll extremes
  document.querySelector('.slides').addEventListener('scroll', function() {
    const slides = this;
    const prevBtn = document.querySelector('.prev');
    const nextBtn = document.querySelector('.next');
    // Show/hide buttons based on scroll position
    prevBtn.style.display = slides.scrollLeft <= 10 ? 'none' : 'block';
    nextBtn.style.display = slides.scrollLeft >= (slides.scrollWidth - slides.clientWidth - 10) ? 'none' : 'block';
  });