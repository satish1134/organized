export const utils = {
    // Loading indicator functions
    showLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
            // Add fade-in effect
            loadingIndicator.style.opacity = '0';
            setTimeout(() => loadingIndicator.style.opacity = '1', 10);
        }
    },

    hideLoading() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            // Add fade-out effect
            loadingIndicator.style.opacity = '0';
            setTimeout(() => {
                loadingIndicator.classList.add('d-none');
                loadingIndicator.style.opacity = '1';
            }, 300);
        }
    },

    // Enhanced timestamp formatting
    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        const date = moment(timestamp);
        const now = moment();
        const diff = now.diff(date, 'hours');

        if (diff < 24) {
            return date.fromNow(); // e.g., "2 hours ago"
        }
        return date.format('YYYY-MM-DD HH:mm:ss');
    },

    // Enhanced elapsed time calculation
    calculateElapsedTime(startTime, endTime) {
        if (!startTime || !endTime) return '';
        const start = moment(startTime);
        const end = moment(endTime);
        const duration = moment.duration(end.diff(start));

        if (duration.asSeconds() < 60) {
            return Math.round(duration.asSeconds()) + ' seconds';
        } else if (duration.asMinutes() < 60) {
            return Math.round(duration.asMinutes()) + ' minutes';
        } else {
            const hours = Math.floor(duration.asHours());
            const minutes = Math.round(duration.asMinutes() % 60);
            return `${hours} hours ${minutes} minutes`;
        }
    },

    // Enhanced notification system
    showNotification(message, type = 'info') {
        // Create container if it doesn't exist
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        // Create notification element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';

        // Add icon based on notification type
        const icon = this.getNotificationIcon(type);
        
        alertDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <div class="flex-grow-1">${this.sanitizeHTML(message)}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        container.appendChild(alertDiv);

        // Add slide-in animation
        alertDiv.style.transform = 'translateX(100%)';
        setTimeout(() => {
            alertDiv.style.transform = 'translateX(0)';
        }, 10);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.style.transform = 'translateX(100%)';
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    },

    // Get notification icon based on type
    getNotificationIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'danger': 'fas fa-exclamation-circle'
        };
        return icons[type] || icons.info;
    },

    // Enhanced modal handling
    initializeModal(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement, {
                keyboard: true,
                backdrop: true,
                focus: true
            });

            // Add animation classes
            modalElement.addEventListener('show.bs.modal', () => {
                modalElement.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    modalElement.style.transform = 'scale(1)';
                }, 10);
            });

            return modal;
        }
        return null;
    },

    showModal(modalInstance) {
        if (modalInstance) {
            modalInstance.show();
        } else {
            console.error('Modal instance not found');
        }
    },

    hideModal(modalInstance) {
        if (modalInstance) {
            modalInstance.hide();
        }
    },

    // Enhanced status color utility
    getStatusColor(status) {
        const colors = {
            'success': 'success',
            'running': 'primary',
            'failed': 'danger',
            'yet_to_start': 'warning',
            'pending': 'info'
        };
        return colors[status.toLowerCase()] || 'secondary';
    },

    // Enhanced sanitization utility
    sanitizeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    // Add smooth scroll utility
    smoothScroll(targetId) {
        const target = document.getElementById(targetId);
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    },

    // Add copy to clipboard utility
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copied to clipboard!', 'success');
        }).catch(err => {
            this.showNotification('Failed to copy text', 'danger');
            console.error('Failed to copy:', err);
        });
    },

    // Set last refresh time
    setLastRefreshTime() {
        const lastRefreshElement = document.getElementById('lastRefreshTime');
        if (lastRefreshElement) {
            const time = moment().tz('America/New_York');
            lastRefreshElement.textContent = time.format('HH:mm:ss') + ' EST';
        }
    },

    // Initialize last refresh time (only once)
    startLastRefreshTimeUpdate() {
        this.setLastRefreshTime(); // Only set once when page loads
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            animation: true,
            delay: { show: 100, hide: 100 }
        });
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl, {
            animation: true,
            trigger: 'hover'
        });
    });

    // Add navbar scroll effect
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
            } else {
                navbar.style.boxShadow = '5px 5px 15px rgba(0,0,0,0.2)';
            }
        });
    }

    // Initialize last refresh time (only once)
    utils.startLastRefreshTimeUpdate();

    // Add global close handler for modals
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            });
        }
    });
});

// Make utils available globally
window.utils = utils;

// Add error handling
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    utils.hideLoading();
    utils.showNotification('An error occurred. Please try again.', 'danger');
});
