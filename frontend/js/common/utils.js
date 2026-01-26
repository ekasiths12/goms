/**
 * GOMS Common Utilities
 * Shared functions used across all pages
 * 
 * Function #1: Theme Management (toggleTheme, loadTheme)
 */

const GOMS = {
    /**
     * Theme Management
     */
    theme: {
        toggle: function() {
            const html = document.documentElement;
            const themeIcon = document.getElementById('themeIcon');
            const themeText = document.getElementById('themeText');
            
            if (html.getAttribute('data-theme') === 'light') {
                // Switch to dark theme
                html.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
                if (themeIcon) themeIcon.textContent = '🌙';
                if (themeText) themeText.textContent = 'Dark';
            } else {
                // Switch to light theme
                html.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                if (themeIcon) themeIcon.textContent = '☀️';
                if (themeText) themeText.textContent = 'Light';
            }
            
            // Update any charts if they exist
            if (window.charts) {
                setTimeout(() => {
                    Object.values(window.charts).forEach(chart => {
                        if (chart && chart.update) {
                            chart.update('none');
                        }
                    });
                }, 100);
            }
        },
        
        load: function() {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            const html = document.documentElement;
            const themeIcon = document.getElementById('themeIcon');
            const themeText = document.getElementById('themeText');
            
            if (savedTheme === 'light') {
                html.setAttribute('data-theme', 'light');
                if (themeIcon) themeIcon.textContent = '☀️';
                if (themeText) themeText.textContent = 'Light';
            } else {
                html.removeAttribute('data-theme');
                if (themeIcon) themeIcon.textContent = '🌙';
                if (themeText) themeText.textContent = 'Dark';
            }
        }
    }
};

// Global shortcuts for backward compatibility
window.toggleTheme = GOMS.theme.toggle;
window.loadTheme = GOMS.theme.load;
