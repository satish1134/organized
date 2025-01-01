document.addEventListener('DOMContentLoaded', function() {
    const iframe = document.getElementById('trend-frame');
    
    function adjustIframeHeight() {
        if (iframe) {
            console.log('Adjusting iframe height');
            const viewportHeight = window.innerHeight;
            const navbarHeight = document.querySelector('.custom-navbar')?.offsetHeight || 0;
            const dropdownHeight = document.querySelector('.dropdown-container')?.offsetHeight || 0;
            
            // Account for padding and margins
            const padding = 32; // 2rem (1rem top + 1rem bottom)
            const newHeight = viewportHeight - navbarHeight - dropdownHeight - padding;
            
            console.log(`Viewport Height: ${viewportHeight}px`);
            console.log(`Navbar Height: ${navbarHeight}px`);
            console.log(`Dropdown Height: ${dropdownHeight}px`);
            console.log(`New iframe height: ${newHeight}px`);
            
            // Set minimum height to prevent too small containers
            const minHeight = 300;
            iframe.style.height = `${Math.max(newHeight, minHeight)}px`;
            
            // Handle width for responsive behavior
            const viewportWidth = window.innerWidth;
            if (viewportWidth <= 600) {
                iframe.style.width = '100%';
                iframe.style.minWidth = '300px';
            } else {
                iframe.style.width = '100%';
            }
        }
    }

    if (iframe) {
        console.log('Iframe found, setting up handlers');
        
        // Set initial opacity to 0
        iframe.style.opacity = '0';
        iframe.style.transition = 'opacity 0.3s ease-in-out';
        
        iframe.onload = function() {
            console.log('Iframe loaded');
            // Fade in the iframe
            this.style.opacity = '1';
            adjustIframeHeight();
            
            // Try to prevent scrollbar flickering
            setTimeout(adjustIframeHeight, 100);
        };

        iframe.onerror = function() {
            console.error('Error loading iframe content');
            // You might want to show an error message to the user here
        };

        // Add debounced resize handler
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(adjustIframeHeight, 250);
        });
    }

    // Initial adjustment
    adjustIframeHeight();
    
    // Additional adjustment after a short delay to handle dynamic content
    setTimeout(adjustIframeHeight, 500);
});
