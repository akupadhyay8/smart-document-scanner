document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initFileUpload();
  initCreditMeter();
  initFormValidation();
  initDailyScansChart(); // Initialize analytics chart if present.
  
  // Automatically fade out flash messages after 3 seconds.
  setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach((msg) => {
      msg.classList.add('fade-out');
    });
  }, 3000);
  
  // Attach compare button event listener.
  document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('compare-btn')) {
      const docId = e.target.dataset.docId;
      console.log('Comparing document:', docId);
      // Implement AJAX call or redirect logic for document comparison.
    }
  });
});

// Highlight the active navigation item.
function initSidebar() {
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    }
  });
}

// Handle drag & drop file upload preview.
function initFileUpload() {
  const dropZone = document.querySelector('.upload-dropzone');
  const fileInput = document.querySelector('#file-upload');
  
  if (!dropZone || !fileInput) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    fileInput.files = dt.files;
    handleFileSelect();
  }, false);

  fileInput.addEventListener('change', handleFileSelect, false);

  function handleFileSelect() {
    const files = fileInput.files;
    if (files.length > 0) {
      showFilePreview(files[0]);
    }
  }

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

// Initialize credit meter based on user's current credits.
function initCreditMeter() {
  const meter = document.querySelector('.meter-progress');
  const creditCountEl = document.querySelector('.credit-count');
  if (!meter || !creditCountEl) return;
  
  const credits = parseInt(creditCountEl.textContent);
  const percentage = (credits / 20) * 100;
  meter.style.width = `${Math.min(percentage, 100)}%`;
}

// Validate form inputs.
function initFormValidation() {
  document.querySelectorAll('.input-field').forEach(input => {
    input.addEventListener('input', () => {
      validateInput(input);
    });
  });
}

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

// Utility function to get file icon based on extension.
function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const icons = {
    txt: '📄',
    csv: '📊',
    doc: '📑',
    pdf: '📘'
  };
  return icons[ext] || '📁';
}

// Utility function to format file size.
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Show and hide a loading overlay during async operations.
function showLoading() {
  document.querySelector('.loading-overlay').classList.add('active');
}

function hideLoading() {
  document.querySelector('.loading-overlay').classList.remove('active');
}

document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => showLoading());
});
window.addEventListener('beforeunload', () => hideLoading());

// Initialize the daily scans chart using Chart.js.
function initDailyScansChart() {
  const canvas = document.getElementById('dailyScansChart');
  if (!canvas) return;
  
  // The daily scans data is stored in a data attribute (as JSON).
  const dailyScansData = JSON.parse(canvas.dataset.scans);
  const labels = dailyScansData.map(item => item.scan_date);
  const scans = dailyScansData.map(item => item.scans);
  
  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
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
          beginAtZero: true
        }
      }
    }
  });
}
