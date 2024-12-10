// Global variables
let dagModal;
const refreshInterval = 300000; // 5 minutes in milliseconds

// Enhanced sanitization function
function sanitizeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize refresh button
    const refreshButton = document.getElementById('refreshDataButton');
    if (refreshButton) {
        refreshButton.addEventListener('click', handleRefreshClick);
    }

    // Initialize select all checkbox
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', handleSelectAll);
    }

    // Initialize individual subject checkboxes
    const subjectCheckboxes = document.querySelectorAll('.subject-area-checkbox:not(#selectAll)');
    subjectCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', handleSubjectCheckboxChange);
    });

    // Initialize Bootstrap dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl)
    });

    // Initially check all checkboxes and show all cards
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = true;
        handleSelectAll({ target: { checked: true } });
    }

    // Load initial data
    refreshData();
    
    // Set up automatic refresh interval
    setInterval(refreshData, refreshInterval);

    // Set up error handling
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        hideLoading();
    });
});

// Show DAG status details in new tab
async function showDagStatus(subject, status) {
    showLoading();
    try {
        const response = await fetch(`/dag_status?subject_area=${encodeURIComponent(subject)}&status=${encodeURIComponent(status)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }

        // Open new tab
        const newTab = window.open('', '_blank');
        
        // Create a new document safely
        newTab.document.open();
        newTab.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body></body></html>');
        newTab.document.close();

        // Get references to the new document elements
        const newDoc = newTab.document;
        const head = newDoc.head;
        const body = newDoc.body;

        // Add meta tags
        const meta = newDoc.createElement('meta');
        meta.setAttribute('http-equiv', 'Content-Security-Policy');
        meta.setAttribute('content', "default-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; script-src 'self' https://cdn.jsdelivr.net;");
        head.appendChild(meta);

        // Add title
        const title = newDoc.createElement('title');
        title.textContent = `${sanitizeHTML(subject)} - ${capitalizeFirst(sanitizeHTML(status))} DAGs`;
        head.appendChild(title);

        // Add CSS
        const cssLink1 = newDoc.createElement('link');
        cssLink1.rel = 'stylesheet';
        cssLink1.href = 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css';
        head.appendChild(cssLink1);

        const cssLink2 = newDoc.createElement('link');
        cssLink2.rel = 'stylesheet';
        cssLink2.href = '/static/css/styles.css';
        head.appendChild(cssLink2);

        // Create container
        const container = newDoc.createElement('div');
        container.className = 'container mt-4';

        // Add heading
        const heading = newDoc.createElement('h3');
        heading.textContent = `${sanitizeHTML(subject)} - ${capitalizeFirst(sanitizeHTML(status))} DAGs`;
        container.appendChild(heading);

        // Create table
        const tableResponsive = newDoc.createElement('div');
        tableResponsive.className = 'table-responsive';
        const table = newDoc.createElement('table');
        table.className = 'table table-striped';

        // Create table header
        const thead = newDoc.createElement('thead');
        const headerRow = newDoc.createElement('tr');
        ['DAG Name', 'Status', 'Start Time', 'End Time', 'Modified Time', 'Elapsed Time'].forEach(headerText => {
            const th = newDoc.createElement('th');
            th.textContent = headerText;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = newDoc.createElement('tbody');
        data.forEach(dag => {
            const row = newDoc.createElement('tr');
            
            // Create cells
            const createCell = (content, isStatus = false) => {
                const td = newDoc.createElement('td');
                if (isStatus) {
                    const span = newDoc.createElement('span');
                    span.className = `badge bg-${getStatusColor(content)}`;
                    span.textContent = sanitizeHTML(content);
                    td.appendChild(span);
                } else {
                    td.textContent = content;
                }
                return td;
            };

            // Add cells to row
            row.appendChild(createCell(sanitizeHTML(dag.dag_name)));
            row.appendChild(createCell(dag.status, true));
            row.appendChild(createCell(formatDateTime(dag.dag_start_time)));
            row.appendChild(createCell(formatDateTime(dag.dag_end_time)));
            row.appendChild(createCell(formatDateTime(dag.modified_ts)));
            row.appendChild(createCell(sanitizeHTML(dag.elapsed_time) || '-'));

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        tableResponsive.appendChild(table);
        container.appendChild(tableResponsive);
        body.appendChild(container);

        // Add Bootstrap JS
        const script = newDoc.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js';
        body.appendChild(script);

    } catch (error) {
        console.error('Error showing DAG status:', error);
        showError('Failed to load DAG details');
    } finally {
        hideLoading();
    }
}

// Handle select all checkbox
function handleSelectAll(event) {
    const subjectCheckboxes = document.querySelectorAll('.subject-area-checkbox:not(#selectAll)');
    subjectCheckboxes.forEach(checkbox => {
        checkbox.checked = event.target.checked;
    });
    updateVisibleCards();
}

// Handle individual subject checkbox changes
function handleSubjectCheckboxChange() {
    updateVisibleCards();
    updateSelectAllCheckbox();
}

// Update visible cards based on checkbox selection
function updateVisibleCards() {
    const selectedSubjects = Array.from(document.querySelectorAll('.subject-area-checkbox:not(#selectAll)'))
        .map(checkbox => checkbox.checked ? checkbox.value : null)
        .filter(value => value !== null)
        .map(value => sanitizeHTML(value));

    document.querySelectorAll('.subject-area-card').forEach(card => {
        const subjectArea = sanitizeHTML(card.dataset.subjectArea);
        card.style.display = selectedSubjects.length === 0 || selectedSubjects.includes(subjectArea) ? '' : 'none';
    });
}

// Update select all checkbox state
function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const subjectCheckboxes = document.querySelectorAll('.subject-area-checkbox:not(#selectAll)');
    const checkedCount = Array.from(subjectCheckboxes).filter(checkbox => checkbox.checked).length;
    
    if (selectAllCheckbox) {
        selectAllCheckbox.checked = checkedCount === subjectCheckboxes.length;
        selectAllCheckbox.indeterminate = checkedCount > 0 && checkedCount < subjectCheckboxes.length;
    }
}

// Refresh all data
function refreshData() {
    showLoading();
    try {
        const now = new Date();
        const lastRefreshElement = document.getElementById('lastRefreshTime');
        if (lastRefreshElement) {
            lastRefreshElement.textContent = now.toLocaleTimeString();
        }
        
        document.querySelectorAll('.subject-card').forEach(card => {
            const subject = sanitizeHTML(card.dataset.subject);
            if (subject) {
                updateSubjectStatusCounts(subject);
            }
        });
    } catch (error) {
        console.error('Error refreshing data:', error);
        showError('Failed to refresh data');
    } finally {
        hideLoading();
    }
}

// Handle refresh button click
function handleRefreshClick() {
    refreshData();
}

// Update status counts for a subject
async function updateSubjectStatusCounts(subject) {
    const statuses = ['success', 'running', 'failed', 'yet_to_start'];
    
    for (const status of statuses) {
        try {
            const response = await fetch(`/dag_status?subject_area=${encodeURIComponent(subject)}&status=${encodeURIComponent(status)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            const countElement = document.getElementById(`${sanitizeHTML(subject)}_${sanitizeHTML(status)}_count`);
            if (countElement) {
                countElement.textContent = data.length.toString();
            }
        } catch (error) {
            console.error(`Error fetching ${status} status for ${subject}:`, error);
        }
    }
}

// Utility Functions
function getStatusColor(status) {
    const sanitizedStatus = sanitizeHTML(status).toLowerCase();
    const colors = {
        'success': 'success',
        'running': 'primary',
        'failed': 'danger',
        'yet_to_start': 'warning'
    };
    return colors[sanitizedStatus] || 'secondary';
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    try {
        const sanitized = sanitizeHTML(dateString);
        const date = new Date(sanitized);
        return date.toLocaleString();
    } catch (error) {
        console.error('Error formatting date:', error);
        return '-';
    }
}

function capitalizeFirst(string) {
    if (!string) return '';
    const sanitized = sanitizeHTML(string);
    return sanitized.charAt(0).toUpperCase() + sanitized.slice(1).toLowerCase();
}

function showLoading() {
    const loader = document.getElementById('loadingIndicator');
    if (loader) {
        loader.style.display = 'block';
    }
}

function hideLoading() {
    const loader = document.getElementById('loadingIndicator');
    if (loader) {
        loader.style.display = 'none';
    }
}

function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger error-message mt-2';
    errorDiv.textContent = sanitizeHTML(message);
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(errorDiv, container.firstChild);
        
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
}
