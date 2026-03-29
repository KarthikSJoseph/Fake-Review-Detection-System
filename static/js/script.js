let chart = null;

/* ------------------ TOGGLE UPLOAD MENU ------------------ */
function toggleUploadMenu() {
    const menu = document.getElementById("uploadMenu");
    menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

/* ------------------ HANDLE CSV UPLOAD ------------------ */
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    fetch("/upload_csv", {
        method: "POST",
        body: formData
    })
    .then(res => res.text())
    .then(html => {
        document.open();
        document.write(html);
        document.close();
    })
    .catch(err => {
        alert("Error uploading CSV");
        console.error(err);
    });
}

/* ------------------ HANDLE IMAGE UPLOAD ------------------ */
function uploadImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    fetch("/upload_image", {
        method: "POST",
        body: formData
    })
    .then(res => res.text())
    .then(html => {
        document.open();
        document.write(html);
        document.close();
    })
    .catch(err => {
        alert("Error uploading image");
        console.error(err);
    });
}

/* ------------------ ANALYZE REVIEWS ------------------ */
async function analyzeReviews() {
    const text = document.getElementById("reviewText").value.trim();

    if (!text) {
        alert("Please enter a review");
        return;
    }

    const reviews = text.split("\n").filter(r => r.trim());

    // 👉 Single review → redirect page
    if (reviews.length === 1) {
        try {
            const res = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: "review=" + encodeURIComponent(reviews[0])
            });

            const data = await res.json();

            if (data.analysis_id) {
                window.location.href = "/results/" + data.analysis_id;
            } else {
                alert("Error analyzing review");
            }
        } catch (err) {
            alert("Server error");
            console.error(err);
        }
        return;
    }

    // 👉 Multiple reviews → dashboard view
    let fakeCount = 0;
    let genuineCount = 0;

    const reviewList = document.getElementById("reviewList");
    reviewList.innerHTML = "";

    for (let review of reviews) {
        try {
            const res = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: "review=" + encodeURIComponent(review)
            });

            const data = await res.json();

            const div = document.createElement("div");
            div.classList.add("review-item");

            if (data.result === "Fake") {
                div.classList.add("fake");
                fakeCount++;
            } else {
                div.classList.add("genuine");
                genuineCount++;
            }

            div.innerHTML = `<strong>${data.result}</strong> - ${review}`;
            reviewList.appendChild(div);

        } catch (err) {
            console.error("Error analyzing:", review, err);
        }
    }

    // Stats update
    document.getElementById("totalCount").innerText = reviews.length;
    document.getElementById("fakeCount").innerText = fakeCount;
    document.getElementById("genuineCount").innerText = genuineCount;

    // Switch UI
    document.getElementById("inputView").classList.add("hidden");
    document.getElementById("resultsView").classList.remove("hidden");

    renderChart(fakeCount, genuineCount);
}

/* ------------------ CHART ------------------ */
function renderChart(fake, genuine) {
    const ctx = document.getElementById("pieChart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "pie",
        data: {
            labels: ["Fake", "Genuine"],
            datasets: [{
                data: [fake, genuine],
                backgroundColor: ["#ef4444", "#22c55e"]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: "bottom" }
            }
        }
    });
}

/* ------------------ GO BACK ------------------ */
function goBack() {
    document.getElementById("resultsView").classList.add("hidden");
    document.getElementById("inputView").classList.remove("hidden");
}

/* ------------------ CLOSE MENU OUTSIDE CLICK ------------------ */
document.addEventListener("click", function (event) {
    const menu = document.getElementById("uploadMenu");
    const btn = document.querySelector(".upload-icon");

    if (menu && btn && !menu.contains(event.target) && !btn.contains(event.target)) {
        menu.style.display = "none";
    }
});

/* ------------------ OPTIONAL POPUP SUPPORT ------------------ */
const addBtn = document.getElementById("addBtn");
const uploadPopup = document.getElementById("uploadPopup");
const closePopup = document.getElementById("closePopup");
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");

if (addBtn && uploadPopup) {
    addBtn.addEventListener("click", () => uploadPopup.classList.remove("hidden"));
}

if (closePopup) {
    closePopup.addEventListener("click", () => {
        uploadPopup.classList.add("hidden");
        uploadForm.reset();
    });
}

if (uploadForm) {
    uploadForm.addEventListener("submit", function (e) {
        e.preventDefault();

        if (!fileInput.files.length) {
            alert("Select a file");
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();

        const endpoint = file.name.endsWith(".csv") ? "/upload_csv" : "/upload_image";
        formData.append(file.name.endsWith(".csv") ? "file" : "image", file);

        fetch(endpoint, {
            method: "POST",
            body: formData
        })
        .then(res => res.text())
        .then(html => {
            document.getElementById("resultsView").classList.remove("hidden");
            document.getElementById("inputView").classList.add("hidden");
            document.body.insertAdjacentHTML("beforeend", html);
        })
        .catch(err => alert("Error: " + err));

        uploadPopup.classList.add("hidden");
        uploadForm.reset();
    });
}