// ------------------ Global Chart ------------------
let chart;

// ------------------ Toggle Upload Menu ------------------
function toggleUploadMenu() {
  const menu = document.getElementById("uploadMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// ------------------ Handle CSV Upload ------------------
function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  fetch("/upload_csv", {
    method: "POST",
    body: formData
  })
  .then(response => response.text())
  .then(html => {
    // Replace page content with uploaded results
    document.open();
    document.write(html);
    document.close();
  })
  .catch(error => {
    alert("Error uploading CSV");
    console.error(error);
  });
}

// ------------------ Handle Image Upload ------------------
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
    // Replace page content with uploaded results
    document.open();
    document.write(html);
    document.close();
  })
  .catch(error => {
    alert("Error uploading image");
    console.error(error);
  });
}

// ------------------ Analyze Reviews ------------------
async function analyzeReviews() {
  const text = document.getElementById("reviewText").value.trim();
  if (!text) {
    alert("Please enter a review");
    return;
  }

  const reviews = text.split("\n").filter(r => r.trim());

  const reviewList = document.getElementById("reviewList");
  reviewList.innerHTML = "";

  let fakeCount = 0;
  let genuineCount = 0;

  for (let review of reviews) {
    const response = await fetch("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "review=" + encodeURIComponent(review)
    });

    const data = await response.json();

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

  // Show results, hide input
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
      plugins: {
        legend: { position: "bottom" }
      }
    }
  });
}

// ------------------ Go Back to Input ------------------
function goBack() {
  document.getElementById("resultsView").classList.add("hidden");
  document.getElementById("inputView").classList.remove("hidden");
  document.getElementById("reviewText").value = ""; // optional: clear textarea
  document.getElementById("reviewList").innerHTML = "";
  document.getElementById("totalCount").innerText = 0;
  document.getElementById("fakeCount").innerText = 0;
  document.getElementById("genuineCount").innerText = 0;

  if (chart) {
    chart.destroy();
    chart = null;
  }
}

// ------------------ Popup Toggle (CSV/Image) ------------------
const addBtn = document.getElementById("addBtn");
const uploadPopup = document.getElementById("uploadPopup");
const closePopup = document.getElementById("closePopup");
const uploadForm = document.getElementById("uploadForm");
const fileInput = document.getElementById("fileInput");

addBtn.addEventListener("click", () => uploadPopup.classList.remove("hidden"));
closePopup.addEventListener("click", () => {
  uploadPopup.classList.add("hidden");
  uploadForm.reset();
});

// ------------------ Handle Upload Form Submit ------------------
uploadForm.addEventListener("submit", function(e) {
  e.preventDefault();
  if (!fileInput.files.length) { alert("Select a file"); return; }

  const file = fileInput.files[0];
  const formData = new FormData();

  if (file.name.endsWith(".csv")) {
    formData.append("file", file);
    fetch("/upload_csv", { method: "POST", body: formData })
      .then(res => res.text())
      .then(html => { document.open(); document.write(html); document.close(); })
      .catch(err => alert("Error: " + err));
  } else {
    formData.append("image", file);
    fetch("/upload_image", { method: "POST", body: formData })
      .then(res => res.text())
      .then(html => { document.open(); document.write(html); document.close(); })
      .catch(err => alert("Error: " + err));
  }

  uploadPopup.classList.add("hidden");
  uploadForm.reset();
});

// ------------------ Close Upload Menu on Outside Click ------------------
document.addEventListener("click", function(event) {
  const menu = document.getElementById("uploadMenu");
  if (menu && !menu.contains(event.target) && event.target.id !== "addBtn") {
    menu.style.display = "none";
  }
});