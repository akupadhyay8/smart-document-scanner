document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initFileUpload();
  initCreditMeter();
  initFormValidation();
  initDailyScansChart();
  initCreditUsageChart();
  initUserScansChart();
  initMatchStatsChart();
  
  // Fade out flash messages after 3 seconds
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(msg => msg.classList.add('fade-out'));
  }, 3000);
  
  // Compare button click listener
  document.addEventListener('click', function(e) {
    if (e.target && e.target.classList.contains('compare-btn')) {
      const docId = e.target.dataset.docId;
      console.log('Comparing document:', docId);
      // TODO: Implement AJAX call or redirection for comparison
    }
  });
  
  // Toggle common topics panel on Avg. Match card click
  const avgMatchCard = document.getElementById('avgMatchCard');
  const topicsPanel = document.getElementById('commonTopicsPanel');
  if (avgMatchCard && topicsPanel) {
    avgMatchCard.addEventListener('click', () => {
      topicsPanel.style.display = (topicsPanel.style.display === 'none' || topicsPanel.style.display === '') ? 'block' : 'none';
    });
  }
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
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });
  
  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      // Create a new DataTransfer object and add the dropped files.
      const dataTransfer = new DataTransfer();
      for (const file of dt.files) {
         dataTransfer.items.add(file);
      }
      fileInput.files = dataTransfer.files;
      showFilePreview(fileInput.files[0]);
    }
  });
  
  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      showFilePreview(fileInput.files[0]);
    }
  });
  
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

function initCreditUsageChart() {
  const creditCanvas = document.getElementById('creditUsageChart');
  if (creditCanvas) {
    const usageData = JSON.parse(creditCanvas.dataset.usage);
    const userLabels = usageData.map(item => item.name);
    const creditUsed = usageData.map(item => item.credit_used); // Expect property credit_used from backend
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

function initUserScansChart() {
  const canvas = document.getElementById('userScansChart');
  if (!canvas) return;
  const rawData = JSON.parse(canvas.dataset.userScans);
  console.log("User Scans Data:", rawData); // Debug: Check data
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

// New Function: Initialize the Match Stats Pie Chart.
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
            'rgba(239, 68, 68, 0.6)'   // redish for unsuccessful
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

function getRandomColor() {
  return '#' + Math.floor(Math.random()*16777215).toString(16);
}

window.addEventListener('beforeunload', () => {
  const overlay = document.querySelector('.loading-overlay');
  if (overlay) overlay.classList.remove('active');
});

document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', () => {
    document.querySelector('.loading-overlay').classList.add('active');
  });
});
