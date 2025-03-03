document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initFileUpload();
  initCreditMeter();
  initFormValidation();
  initCharts();
  // Optionally: initTooltips(); initDataTables(); if needed.
  // Automatically fade out flash messages after 3 seconds
  setTimeout(() => {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach((msg) => {
      msg.classList.add('fade-out');
    });
  }, 3000);
});

function initSidebar() {
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('href') === currentPath) {
      item.classList.add('active');
    }
  });
}

function initFileUpload() {
  const dropZone = document.querySelector('.upload-dropzone');
  const fileInput = document.querySelector('#file-upload');
  
  if (!dropZone || !fileInput) return;

  // Drag & Drop events
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

function initCreditMeter() {
  const meter = document.querySelector('.meter-progress');
  const creditCountEl = document.querySelector('.credit-count');
  if (!meter || !creditCountEl) return;
  
  const credits = parseInt(creditCountEl.textContent);
  const percentage = (credits / 20) * 100;
  meter.style.width = `${Math.min(percentage, 100)}%`;
}

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

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

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

function initCharts() {
  const ctx = document.getElementById('scanChart');
  if (ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Scans per Month',
          data: [12, 19, 3, 5, 2, 3],
          backgroundColor: 'rgba(37, 99, 235, 0.2)',
          borderColor: 'rgba(37, 99, 235, 1)',
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

// Compare button functionality
document.addEventListener('click', function(e) {
  if (e.target && e.target.classList.contains('compare-btn')) {
    const docId = e.target.dataset.docId;
    console.log('Comparing document:', docId);
    // Implement AJAX call or redirect logic for document comparison.
  }
});
