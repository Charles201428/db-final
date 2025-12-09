// Use the current origin to work with both localhost and 127.0.0.1
const API_URL = `${window.location.origin}/api`;

function fillExample(query) {
    document.getElementById('queryInput').value = query;
    document.getElementById('queryInput').focus();
}

function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    if (typeof num === 'number') {
        return num.toLocaleString('en-US', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
        });
    }
    return num;
}

function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function renderResponse(response) {
    const responseSection = document.getElementById('responseSection');
    
    if (!response.success) {
        responseSection.innerHTML = `
            <div class="message error">
                <strong>Error:</strong> ${response.error || response.message || 'An error occurred'}
            </div>
        `;
        return;
    }
    
    let html = '';
    
    // Show message
    if (response.message) {
        const messageClass = response.success ? 'success' : 'error';
        html += `<div class="message ${messageClass}">${response.message}</div>`;
    }
    
    // Show data
    if (response.data && response.data.length > 0) {
        const data = response.data;
        const keys = Object.keys(data[0]);
        
        html += '<table class="data-table">';
        html += '<thead><tr>';
        keys.forEach(key => {
            const header = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            html += `<th>${header}</th>`;
        });
        html += '</tr></thead>';
        html += '<tbody>';
        
        data.forEach(row => {
            html += '<tr>';
            keys.forEach(key => {
                let value = row[key];
                if (key.includes('price') && typeof value === 'number') {
                    value = '$' + formatNumber(value);
                } else if (key.includes('volume') && typeof value === 'number') {
                    value = formatNumber(value);
                } else if (key.includes('date') || key.includes('obs_date')) {
                    value = formatDate(value);
                } else if (typeof value === 'number') {
                    value = formatNumber(value);
                } else if (value === null) {
                    value = 'N/A';
                }
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
    } else if (response.message && !response.data) {
        html += '<div class="empty-state">';
        html += '<p>No data returned for this query.</p>';
        html += '</div>';
    }
    
    responseSection.innerHTML = `<div class="response-content">${html}</div>`;
}

function showLoading() {
    const responseSection = document.getElementById('responseSection');
    responseSection.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <span>Processing your query...</span>
        </div>
    `;
}

async function submitQuery() {
    const queryInput = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a query');
        return;
    }
    
    // Disable button and show loading
    submitBtn.disabled = true;
    showLoading();
    
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        const data = await response.json();
        renderResponse(data);
    } catch (error) {
        renderResponse({
            success: false,
            error: `Failed to connect to server: ${error.message}. Make sure the Flask server is running.`
        });
    } finally {
        submitBtn.disabled = false;
    }
}

// Allow Enter key to submit (Ctrl+Enter or Cmd+Enter)
document.getElementById('queryInput').addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        submitQuery();
    }
});

// Initialize - check if server is running
async function checkServer() {
    try {
        const response = await fetch(`${window.location.origin}/health`);
        if (response.ok) {
            console.log('Server is running');
        }
    } catch (error) {
        console.warn('Server not responding. Make sure Flask app is running on port 5000.');
    }
}

checkServer();

