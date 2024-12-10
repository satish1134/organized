const packageParser = {
    init() {
        this.setupEventListeners();
        this.loadInitialPackages(); // Changed to separate initial load function
        this.formatAllTimestamps();
        this.setupNotificationRefresh();
    },

    setupEventListeners() {
        // Refresh button click handler
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refreshPackages());
        }

        // Package search handler
        const searchInput = document.getElementById('packageSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterPackages(e.target.value));
        }
    },

    async loadInitialPackages() {
        try {
            const response = await fetch('/api/check_package_versions');
            if (!response.ok) throw new Error('Failed to fetch package updates');
            
            const data = await response.json();
            this.renderInitialPackages(data.packages);
            this.updateLastChecked();
        } catch (error) {
            console.error('Error loading initial packages:', error);
            // Only show notification if no packages are visible
            if (!document.querySelector('.package-card')) {
                this.showNotification('Failed to load packages', 'danger');
            }
        }
    },
    

    renderInitialPackages(packages) {
        if (!packages || !Array.isArray(packages)) return;

        const packageList = document.querySelector('.package-list');
        if (!packageList) return;

        // Clear existing content
        packageList.innerHTML = '';

        // Create and append package cards
        packages.forEach(pkg => {
            const card = this.createPackageCard(pkg);
            packageList.appendChild(card);
        });

        this.sortPackageCards();
    },

    createPackageCard(pkg) {
        const card = document.createElement('div');
        card.className = 'package-card';
        card.setAttribute('data-package', pkg.name);
        card.setAttribute('data-timestamp', pkg.last_update);

        card.innerHTML = `
            <div class="card mb-3">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h3 class="card-title h5 mb-0">
                        ${pkg.name}
                        ${pkg.has_update ? '<span class="badge bg-warning text-dark ms-2">Update Available</span>' : ''}
                    </h3>
                    <div class="package-actions">
                        <a href="${pkg.link}" target="_blank" class="btn btn-sm btn-primary" rel="noopener noreferrer">
                            <i class="fas fa-external-link-alt"></i> PyPI
                        </a>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="version-info">
                                <i class="fas fa-code-branch text-primary"></i>
                                <strong>Version:</strong>
                                <span class="current-version">${pkg.version || 'Unknown'}</span>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="version-info">
                                <i class="fas fa-clock text-primary"></i>
                                <strong>Last Updated:</strong>
                                <span class="last-update" data-timestamp="${pkg.last_update}">${pkg.last_update}</span>
                            </div>
                        </div>
                        <div class="col-12">
                            <div class="status-info">
                                <i class="fas fa-info-circle text-primary"></i>
                                <strong>Status:</strong>
                                <span class="badge version-status ${this.getStatusClass(pkg.status)}">${pkg.status}</span>
                            </div>
                        </div>
                        ${pkg.description ? `
                        <div class="col-12">
                            <small class="text-muted package-description">${this.escapeHtml(pkg.description)}</small>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;

        return card;
    },

    async refreshPackages() {
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.classList.add('loading');
            refreshBtn.disabled = true;
        }

        try {
            const response = await fetch('/api/check_package_versions');
            if (!response.ok) throw new Error('Failed to fetch package updates');
            
            const data = await response.json();
            this.updatePackageCards(data.packages);
            this.updateLastChecked();
            this.sortPackageCards();
            this.showNotification('Package information updated successfully', 'success');
        } catch (error) {
            console.error('Error refreshing packages:', error);
            this.showNotification('Failed to update package information', 'danger');
        } finally {
            if (refreshBtn) {
                refreshBtn.classList.remove('loading');
                refreshBtn.disabled = false;
            }
        }
    },

    sortPackageCards() {
        const packageList = document.querySelector('.package-list');
        if (!packageList) return;

        const cards = Array.from(packageList.getElementsByClassName('package-card'));
        if (cards.length === 0) return;

        cards.sort((a, b) => {
            const timeA = new Date(a.getAttribute('data-timestamp'));
            const timeB = new Date(b.getAttribute('data-timestamp'));
            return timeB - timeA; // Sort in descending order (newest first)
        });

        // Clear and reappend in sorted order
        packageList.innerHTML = '';
        cards.forEach(card => packageList.appendChild(card));
    },

    updatePackageCards(packages) {
        if (!packages || !Array.isArray(packages)) return;

        packages.forEach(pkg => {
            const card = document.querySelector(`.package-card[data-package="${pkg.name}"]`);
            if (card) {
                this.updatePackageCard(card, pkg);
            } else {
                // If card doesn't exist, create it
                const newCard = this.createPackageCard(pkg);
                document.querySelector('.package-list').appendChild(newCard);
            }
        });
    },

    updatePackageCard(card, pkg) {
        if (!card) return;

        // Update version information
        const currentVersion = card.querySelector('.current-version');
        const lastUpdate = card.querySelector('.last-update');
        const statusBadge = card.querySelector('.version-status');

        if (currentVersion) {
            const oldVersion = currentVersion.textContent;
            const newVersion = pkg.version || 'Unknown';
            currentVersion.textContent = newVersion;

            // Highlight if version changed
            if (oldVersion !== newVersion) {
                card.classList.add('package-updated');
                setTimeout(() => card.classList.remove('package-updated'), 2000);
            }
        }

        if (lastUpdate) {
            lastUpdate.setAttribute('data-timestamp', pkg.last_update);
            lastUpdate.textContent = pkg.last_update;
        }

        // Update status badge
        if (statusBadge) {
            statusBadge.className = `badge version-status ${this.getStatusClass(pkg.status)}`;
            statusBadge.textContent = pkg.status;
        }

        // Update update badge
        const updateBadge = card.querySelector('.badge-warning');
        if (pkg.has_update) {
            if (!updateBadge) {
                const badge = document.createElement('span');
                badge.className = 'badge bg-warning text-dark ms-2';
                badge.textContent = 'Update Available';
                card.querySelector('.card-title').appendChild(badge);
            }
        } else if (updateBadge) {
            updateBadge.remove();
        }

        // Update description if it exists
        const descriptionDiv = card.querySelector('.package-description');
        if (descriptionDiv && pkg.description) {
            descriptionDiv.textContent = pkg.description;
        }

        // Update data-timestamp attribute
        card.setAttribute('data-timestamp', pkg.last_update);
    },

    getStatusClass(status) {
        switch (status) {
            case 'Recent': return 'bg-success';
            case 'Active': return 'bg-info';
            case 'Stable': return 'bg-primary';
            default: return 'bg-secondary';
        }
    },

    filterPackages(searchTerm) {
        const cards = document.querySelectorAll('.package-card');
        const noResultsElement = document.getElementById('noPackagesFound');
        let hasVisibleCards = false;

        if (cards.length === 0) {
            if (noResultsElement) {
                noResultsElement.style.display = 'none';
            }
            return;
        }

        cards.forEach(card => {
            const packageName = card.getAttribute('data-package').toLowerCase();
            const isVisible = packageName.includes(searchTerm.toLowerCase());
            card.style.display = isVisible ? 'block' : 'none';
            if (isVisible) hasVisibleCards = true;
        });

        if (noResultsElement) {
            if (searchTerm && !hasVisibleCards) {
                noResultsElement.textContent = 'No matching packages found.';
                noResultsElement.style.display = 'block';
            } else {
                noResultsElement.style.display = 'none';
            }
        }
    },

    formatAllTimestamps() {
        document.querySelectorAll('.last-update, .notification-time').forEach(el => 
            this.formatTimestamp(el)
        );
    },

    formatTimestamp(element) {
        const timestamp = element.getAttribute('data-timestamp');
        if (!timestamp) return;
    
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) return;
    
            const formatter = new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: 'America/New_York'
            });
    
            const formattedDate = formatter.format(date);
            const [datePart, timePart] = formattedDate.split(', ');
            const [month, day, year] = datePart.split('/');
            const formattedTime = `${year}-${month}-${day} ${timePart} EST`;
            
            element.textContent = formattedTime;
            
            element.title = new Intl.DateTimeFormat('en-US', {
                dateStyle: 'full',
                timeStyle: 'long',
                timeZone: 'America/New_York'
            }).format(date);
    
        } catch (error) {
            console.error('Error formatting timestamp:', error);
            element.textContent = timestamp;
        }
    },

    updateLastChecked() {
        const lastCheckedElement = document.getElementById('lastCheckedTime');
        if (lastCheckedElement) {
            const now = new Date();
            const formatter = new Intl.DateTimeFormat('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false,
                timeZone: 'America/New_York'
            });
            lastCheckedElement.textContent = `${formatter.format(now)} EST`; 
        }               
    },

    setupNotificationRefresh() {
        this.refreshNotifications();
        setInterval(() => this.refreshNotifications(), 120000);
    },

    async refreshNotifications() {
        try {
            const response = await fetch('/api/notifications');
            if (!response.ok) throw new Error('Failed to fetch notifications');
            
            const data = await response.json();
            this.updateNotificationPanel(data.notifications);
        } catch (error) {
            console.error('Error refreshing notifications:', error);
        }
    },

    updateNotificationPanel(notifications) {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;

        notificationList.innerHTML = notifications && notifications.length > 0 
            ? notifications.map(notification => `
                <div class="alert alert-${notification.type || 'info'} alert-dismissible fade show">
                    <div class="notification-content">
                        <strong>${this.escapeHtml(notification.package_name)}</strong>: 
                        ${this.escapeHtml(notification.message)}
                        <br>
                        <small class="text-muted notification-time" data-timestamp="${notification.timestamp}">
                            ${notification.timestamp}
                        </small>
                    </div>
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `).join('')
            : `<div class="text-center text-muted p-3">
                <i class="fas fa-bell-slash"></i>
                No notifications at this time
               </div>`;

        notificationList.querySelectorAll('.notification-time').forEach(el => 
            this.formatTimestamp(el)
        );
    },

    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${this.escapeHtml(message)}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        const container = document.getElementById('toastContainer') || document.body;
        container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    },

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    packageParser.init();
});

export { packageParser };
