let chart;

// Toggle the upload menu for CSV or image
function toggleUploadMenu() {
  const menu = document.getElementById("uploadMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// Handle CSV upload
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
    console.error(err);
    alert("Error uploading CSV file");
  });
}

// Handle image upload
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
    console.error(err);
    alert("Error uploading image");
  });
}

// Analyze reviews from textarea
async function analyzeReviews() {
  const text = document.getElementById("reviewText").value.trim();
  if (!text) { alert("Please enter a review"); return; }

  const reviews = text.split("\n").filter(r => r.trim());

  let fakeCount = 0;
  let genuineCount = 0;
  const reviewList = document.getElementById("reviewList");
  reviewList.innerHTML = "";

  for (let review of reviews) {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "review=" + encodeURIComponent(review)
    });

    const data = await response.json();

    // Display each review
    const div = document.createElement("div");
    div.classList.add("review-item");
    div.innerHTML = `<strong>${data.result}</strong> - ${review}`;

    if (data.result === "Fake") {
      div.classList.add("fake");
      fakeCount++;
    } else {
      div.classList.add("genuine");
      genuineCount++;
    }

    reviewList.appendChild(div);
  }

  // Update stats
  document.getElementById("totalCount").innerText = reviews.length;
  document.getElementById("fakeCount").innerText = fakeCount;
  document.getElementById("genuineCount").innerText = genuineCount;

  // Show results view
  document.getElementById("inputView").classList.add("hidden");
  document.getElementById("resultsView").classList.remove("hidden");

  // Render pie chart
  const ctx = document.getElementById("pieChart").getContext("2d");
  if (chart) chart.destroy();

  chart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: ["Fake", "Genuine"],
      datasets: [{
        data: [fakeCount, genuineCount],
        backgroundColor: ["#ef4444", "#22c55e"]
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } }
    }
  });
}

// Go back to input view from results
function goBack() {
  document.getElementById("resultsView").classList.add("hidden");
  document.getElementById("inputView").classList.remove("hidden");
}