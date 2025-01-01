document.addEventListener('DOMContentLoaded', function() {
    const iframe = document.getElementById('trend-frame');
    
    function adjustIframeHeight() {
        if (iframe) {
            console.log('Adjusting iframe height');
            const viewportHeight = window.innerHeight;
            const navbarHeight = document.querySelector('.custom-navbar')?.offsetHeight || 0;
            
            const newHeight = viewportHeight - navbarHeight;
            console.log(`New iframe height: ${newHeight}px`);
            iframe.style.height = `${newHeight}px`;
        }
    }

    if (iframe) {
        console.log('Iframe found, setting up handlers');
        
        iframe.onload = function() {
            console.log('Iframe loaded');
            this.style.opacity = '1';
            adjustIframeHeight();
        };

        iframe.onerror = function() {
            console.error('Error loading iframe content');
        };
    }

    window.addEventListener('resize', adjustIframeHeight);
    adjustIframeHeight();
});
