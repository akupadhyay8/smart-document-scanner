// When the page finishes loading, set up all the interactive components!
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();             // Highlight the current navigation item.
  initFileUpload();          // Set up the file upload area (drag & drop, preview).
  initCreditMeter();         // Update the credit meter to show remaining scans.
  initFormValidation();      // Enable real-time validation on form fields.
  initDailyScansChart();     // Draw the line chart for daily scan totals.
  initCreditUsageChart();    // Draw the bar chart for scans (credits used) per user.
  initUserScansChart();      // Draw the line chart showing each user's daily scans.
  initMatchStatsChart();     // Draw the pie chart for document match statistics.
  
  // Automatically fade out flash messages after 3 seconds to keep the UI clean.
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(msg => msg.classList.add('fade-out'));
  }, 3000);
  
  // Listen for clicks on "compare" buttons to eventually handle document comparisons.
  document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('compare-btn')) {
      const docId = e.target.dataset.docId;
      console.log('Comparing document:', docId);
      // TODO: Implement AJAX call or redirection for document comparison here.
    }
  });
  
  // Toggle the "Common Topics" panel when the Avg. Match card is clicked.
  const avgMatchCard = document.getElementById('avgMatchCard');
  const topicsPanel = document.getElementById('commonTopicsPanel');
  if (avgMatchCard && topicsPanel) {
    avgMatchCard.addEventListener('click', () => {
      topicsPanel.style.display = (topicsPanel.style.display === 'none' || topicsPanel.style.display === '') ? 'block' : 'none';
    });
  }
});

// Navigation: Highlight the active sidebar link based on the current URL.
function initSidebar() {
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    }
  });
}

// File Upload Setup: Manage drag & drop and file selection with a preview.
function initFileUpload() {
  const dropZone = document.querySelector('.upload-dropzone');
  const fileInput = document.querySelector('#file-upload');
  if (!dropZone || !fileInput) return;
  
  // When a file is dragged over the drop zone, add a visual cue.
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });
  
  // Remove the visual cue when the file leaves or is dropped.
  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });
  
  // Handle dropped files: we create a new DataTransfer object so the file input can be updated.
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      const dataTransfer = new DataTransfer();
      for (const file of dt.files) {
         dataTransfer.items.add(file);
      }
      fileInput.files = dataTransfer.files;
      showFilePreview(fileInput.files[0]);
    }
  });
  
  // If a file is chosen via the file dialog, show its preview.
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      showFilePreview(fileInput.files[0]);
    }
  });
  
  // Display a preview of the selected file.
  function showFilePreview(file) {
    const preview = document.querySelector('#file-preview');
    preview.innerHTML = `
      <div class="file-preview-card fade-in">
        <div class="file-icon">${getFileIcon(file.name)}</div>
        <div class="file-info">
          <h4>${file.name}</h4>
          <p>${formatFileSize(file.size)}</p>
        </div>
      </div>
    `;
  }
}

// Credit Meter: Update the visual meter based on the user's current credits.
function initCreditMeter() {
  const meter = document.querySelector('.meter-progress');
  const creditCountEl = document.querySelector('.credit-count');
  if (!meter || !creditCountEl) return;
  const credits = parseInt(creditCountEl.textContent);
  const percentage = (credits / 20) * 100;
  meter.style.width = `${Math.min(percentage, 100)}%`;
}

// Form Validation: Check user input in real time and provide feedback.
function initFormValidation() {
  document.querySelectorAll('.input-field').forEach(input => {
    input.addEventListener('input', () => {
      validateInput(input);
    });
  });
}

// Validate an input field and update its parent element's style accordingly.
function validateInput(input) {
  const parent = input.closest('.form-group');
  if (!parent) return;
  parent.classList.remove('valid', 'invalid');
  if (input.validity.valid) {
    parent.classList.add('valid');
  } else {
    parent.classList.add('invalid');
  }
}

// Utility Functions for File Details
// Returns an icon based on the file extension.
function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const icons = {
    txt: '📄',
    csv: '📊'
    // You can add more file type icons here.
  };
  return icons[ext] || '📁';
}

// Converts a file size in bytes to a human-readable format.
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Chart Initializations using Chart.js
// Draw a line chart for daily scans.
function initDailyScansChart() {
  const dailyCanvas = document.getElementById('dailyScansChart');
  if (dailyCanvas) {
    const dailyData = JSON.parse(dailyCanvas.dataset.scans);
    const labels = dailyData.map(item => item.scan_date);
    const scans = dailyData.map(item => parseFloat(item.scans));
    const maxScans = Math.max(...scans);
    const suggestedMax = maxScans + 5;
    const ctx1 = dailyCanvas.getContext('2d');
    new Chart(ctx1, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Daily Scans',
          data: scans,
          backgroundColor: 'rgba(37, 99, 235, 0.2)',
          borderColor: 'rgba(37, 99, 235, 1)',
          borderWidth: 2,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            suggestedMax: suggestedMax
          }
        }
      }
    });
  }
}

// Draw a bar chart showing how many scans (credits used) each user has performed.
function initCreditUsageChart() {
  const creditCanvas = document.getElementById('creditUsageChart');
  if (creditCanvas) {
    const usageData = JSON.parse(creditCanvas.dataset.usage);
    const userLabels = usageData.map(item => item.name);
    const creditUsed = usageData.map(item => item.credit_used); // using property 'credit_used'
    const ctx2 = creditCanvas.getContext('2d');
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: userLabels,
        datasets: [{
          label: 'Scans (Credits Used)',
          data: creditUsed,
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } }
      }
    });
  }
}

// Draw a line chart that shows daily scan counts for each user.
function initUserScansChart() {
  const canvas = document.getElementById('userScansChart');
  if (!canvas) return;
  const rawData = JSON.parse(canvas.dataset.userScans);
  console.log("User Scans Data:", rawData); // Debug: Log data for troubleshooting
  if (!rawData || rawData.length === 0) {
    canvas.parentElement.innerHTML = '<p style="padding:1rem; text-align:center;">No data available for User Daily Scans.</p>';
    return;
  }
  const dataByUser = {};
  rawData.forEach(item => {
    if (!dataByUser[item.user_name]) {
      dataByUser[item.user_name] = [];
    }
    dataByUser[item.user_name].push({ x: item.scan_date, y: item.scans });
  });
  const datasets = [];
  for (const user in dataByUser) {
    dataByUser[user].sort((a, b) => new Date(a.x) - new Date(b.x));
    datasets.push({
      label: user,
      data: dataByUser[user],
      fill: false,
      borderColor: getRandomColor(),
      tension: 0.1
    });
  }
  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: { datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { type: 'time', time: { unit: 'day' }, title: { display: true, text: 'Date' } },
        y: { beginAtZero: true, title: { display: true, text: 'Scan Count' } }
      },
      plugins: {
        tooltip: {
          callbacks: {
            title: function(context) {
              return context[0].parsed.x;
            },
            label: function(context) {
              return context.dataset.label + ': ' + context.parsed.y;
            }
          }
        }
      }
    }
  });
}

// Draw a pie chart showing match statistics: successful vs. unsuccessful matches.
function initMatchStatsChart() {
  const matchCanvas = document.getElementById('matchStatsChart');
  if (matchCanvas) {
    const matchData = JSON.parse(matchCanvas.dataset.match);
    const labels = ['Successful Matches', 'Unsuccessful Matches'];
    const data = [matchData.successful, matchData.unsuccessful];
    const ctx = matchCanvas.getContext('2d');
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: [
            'rgba(34, 197, 94, 0.6)', // greenish for successful
            'rgba(239, 68, 68, 0.6)'  // reddish for unsuccessful
          ],
          borderColor: [
            'rgba(34, 197, 94, 1)',
            'rgba(239, 68, 68, 1)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }
}

// Helper function: Generate a random hex color (useful for chart lines).
function getRandomColor() {
  return '#' + Math.floor(Math.random() * 16777215).toString(16);
}

// When the user is about to leave the page, remove the loading overlay.
window.addEventListener('beforeunload', () => {
  const overlay = document.querySelector('.loading-overlay');
  if (overlay) overlay.classList.remove('active');
});

// Show a loading overlay when any form on the page is submitted.
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    document.querySelector('.loading-overlay').classList.add('active');
  });
});
