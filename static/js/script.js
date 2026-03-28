// -------------------- GLOBAL VARIABLES --------------------
let pieChart = null;

// -------------------- CHART.JS PIE CHART --------------------
function renderPieChart(fake, genuine) {
    const ctx = document.getElementById('pieChart').getContext('2d');

    if (pieChart) {
        pieChart.destroy();
    }

    pieChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Fake Reviews', 'Genuine Reviews'],
            datasets: [{
                data: [fake, genuine],
                backgroundColor: ['#FF4C4C', '#4CAF50'],
                borderColor: ['#fff', '#fff'],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// -------------------- BLOCKCHAIN TABLE --------------------
function populateBlockchain(chain) {
    const tableBody = document.getElementById('blockchainBody');
    tableBody.innerHTML = '';

    chain.forEach(block => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${block.index}</td>
            <td>${new Date(parseFloat(block.timestamp) * 1000).toLocaleString()}</td>
            <td>${block.data ? JSON.stringify(block.data) : 'N/A'}</td>
            <td>${block.previous_hash}</td>
            <td>${block.hash}</td>
        `;
        tableBody.appendChild(row);
    });
}

// -------------------- AJAX PREDICT --------------------
async function predictReview(review) {
    const formData = new FormData();
    formData.append('review', review);

    const response = await fetch('/api/predict', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

// -------------------- HANDLE REVIEW FORM --------------------
document.getElementById('reviewForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const reviewInput = document.getElementById('reviewInput');
    const review = reviewInput.value.trim();
    if (!review) return;

    const result = await predictReview(review);
    alert(`Result: ${result.result}\nConfidence: ${result.confidence}%`);

    reviewInput.value = '';
    // Optionally, refresh blockchain table
    fetchBlockchain();
});

// -------------------- HANDLE CSV UPLOAD --------------------
document.getElementById('csvUploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/upload_csv', {
        method: 'POST',
        body: formData
    });

    const html = await response.text();
    document.getElementById('resultsContainer').innerHTML = html;
    fileInput.value = '';
    fetchBlockchain();
});

// -------------------- HANDLE IMAGE UPLOAD --------------------
document.getElementById('imageUploadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('imageFile');
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    const response = await fetch('/upload_image', {
        method: 'POST',
        body: formData
    });

    const html = await response.text();
    document.getElementById('resultsContainer').innerHTML = html;
    fileInput.value = '';
    fetchBlockchain();
});

// -------------------- FETCH BLOCKCHAIN --------------------
async function fetchBlockchain() {
    const response = await fetch('/blockchain_table');
    const html = await response.text();

    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const tableBody = doc.getElementById('blockchainBody');

    if (tableBody) {
        document.getElementById('blockchainBody').innerHTML = tableBody.innerHTML;
    }
}

// -------------------- ON PAGE LOAD --------------------
document.addEventListener('DOMContentLoaded', () => {
    const fake = parseInt(document.getElementById('totalFake')?.innerText || '0');
    const genuine = parseInt(document.getElementById('totalGenuine')?.innerText || '0');
    renderPieChart(fake, genuine);

    // Initial blockchain load
    fetchBlockchain();
});