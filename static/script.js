const API_URL = `${window.location.origin}/api`;


function fillExample(query) {
  const input = document.getElementById('queryInput');
  if (!input) return;
  input.value = query;
  input.focus();
}

function formatNumber(num) {
  if (num === null || num === undefined) return 'N/A';
  if (typeof num === 'number') {
    return num.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  return num;
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function setLoading(isLoading) {
  const btn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const spinner = document.getElementById('btnSpinner');

  if (!btn) return;

  btn.disabled = isLoading;

  if (spinner) {
    spinner.classList.toggle('d-none', !isLoading);
  }
  if (btnText) {
    btnText.textContent = isLoading ? 'Processing...' : 'Query';
  }
}

function showLoading() {
  const responseSection = document.getElementById('responseSection');
  if (!responseSection) return;

  responseSection.innerHTML = `
    <div class="d-flex align-items-center gap-2 text-muted">
      <div class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></div>
      <span>Processing your query...</span>
    </div>
  `;
}

// ----------------- rendering ----------------

function renderResponse(response) {
  const responseSection = document.getElementById('responseSection');
  if (!responseSection) return;

  if (!response) {
    responseSection.innerHTML = `
      <div class="alert alert-danger mb-0">
        Empty response from server.
      </div>
    `;
    return;
  }

  // Error state
  if (!response.success) {
    responseSection.innerHTML = `
      <div class="alert alert-danger mb-2">
        <strong>Error:</strong> ${response.error || response.message || 'An error occurred'}
      </div>
    `;
    return;
  }

  let html = '';

  // Message
  if (response.message) {
    html += `
      <div class="alert alert-success py-2 mb-3">
        ${response.message}
      </div>
    `;
  }


  if (response.sql) {
    html += `
      <div class="mb-3">
        <div class="fw-semibold mb-1">Generated SQL</div>
        <pre class="bg-dark text-light p-2 rounded small mb-0" style="white-space: pre-wrap; word-break: break-word;">
${response.sql}
        </pre>
      </div>
    `;
  }


  const data = response.data;
  if (Array.isArray(data) && data.length > 0) {
    const keys = Object.keys(data[0]);

    html += `
      <div class="fw-semibold mb-2">
        Results (${data.length} row${data.length === 1 ? '' : 's'})
      </div>
      <div class="table-responsive">
        <table class="table table-striped table-hover table-sm align-middle mb-0">
          <thead>
            <tr>
              ${keys
                .map((key) => {
                  const header = key
                    .replace(/_/g, ' ')
                    .replace(/\b\w/g, (l) => l.toUpperCase());
                  return `<th scope="col">${header}</th>`;
                })
                .join('')}
            </tr>
          </thead>
          <tbody>
            ${data
              .map((row) => {
                return `
                  <tr>
                    ${keys
                      .map((key) => {
                        let value = row[key];

                        if (key.includes('price') && typeof value === 'number') {
                          value = '$' + formatNumber(value);
                        } else if (key.includes('volume') && typeof value === 'number') {
                          value = formatNumber(value);
                        } else if (
                          key.includes('date') ||
                          key.includes('obs_date')
                        ) {
                          value = formatDate(value);
                        } else if (typeof value === 'number') {
                          value = formatNumber(value);
                        } else if (value === null || value === undefined) {
                          value = 'N/A';
                        }

                        return `<td>${value}</td>`;
                      })
                      .join('')}
                  </tr>
                `;
              })
              .join('')}
          </tbody>
        </table>
      </div>
    `;
  } else {
    html += `
      <p class="text-muted mb-0">No data returned for this query.</p>
    `;
  }

  responseSection.innerHTML = html;
}


async function submitQuery() {
  const queryInput = document.getElementById('queryInput');
  if (!queryInput) return;

  const query = queryInput.value.trim();
  if (!query) {
    alert('Please enter a query');
    return;
  }

  setLoading(true);
  showLoading();

  try {
    const response = await fetch(`${API_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query }),
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      renderResponse({
        success: false,
        error:
          (data && data.error) ||
          `Server returned HTTP ${response.status}`,
      });
      return;
    }

    renderResponse(data);
  } catch (error) {
    renderResponse({
      success: false,
      error: `Failed to connect to server: ${error.message}. Make sure the Flask server is running.`,
    });
  } finally {
    setLoading(false);
  }
}


document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('queryInput');
  const healthIndicator = document.getElementById('healthIndicator');

  if (input) {
    input.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        submitQuery();
      }
    });
  }

  // Health check
  fetch(`${window.location.origin}/health`)
    .then((res) => {
      if (!res.ok) throw new Error();
      if (healthIndicator) {
        healthIndicator.textContent = 'Server online';
        healthIndicator.classList.remove('text-muted');
        healthIndicator.classList.add('text-success');
      }
    })
    .catch(() => {
      if (healthIndicator) {
        healthIndicator.textContent = 'Server unavailable';
        healthIndicator.classList.remove('text-muted');
        healthIndicator.classList.add('text-danger');
      }
      console.warn('Server not responding. Make sure Flask app is running.');
    });
});
