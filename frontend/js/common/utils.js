/**
 * GOMS Common Utilities
 * Shared functions used across all pages
 * 
 * Function #1: Theme Management (toggleTheme, loadTheme)
 * Function #2: Formatting Utilities (formatDate, formatNumber, formatInteger, formatDateInput)
 * Function #4: Authentication Utilities (checkAuth, logout)
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
    },
    
    /**
     * Formatting Utilities
     */
    format: {
        date: function(dateString) {
            if (!dateString) return '';
            try {
                const date = new Date(dateString);
                // Format as DD/MM/YY like old Qt app
                const day = date.getDate().toString().padStart(2, '0');
                const month = (date.getMonth() + 1).toString().padStart(2, '0');
                const year = date.getFullYear().toString().slice(-2);
                return `${day}/${month}/${year}`;
            } catch (error) {
                return dateString;
            }
        },
        
        number: function(num) {
            if (num === null || num === undefined || isNaN(num)) return '0.00';
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num);
        },
        
        integer: function(num) {
            if (num === null || num === undefined || isNaN(num)) return '0';
            return parseInt(num).toString();
        },
        
        dateInput: function(input) {
            // Auto-format date input to DD/MM/YY format (like old Qt app)
            if (!input || !input.value) return;
            
            let text = input.value;
            // Remove any non-digit characters
            let digitsOnly = text.replace(/\D/g, '');
            
            // Format as DD/MM/YY
            let formatted = "";
            if (digitsOnly.length >= 1) {
                formatted += digitsOnly.slice(0, 2);
            }
            if (digitsOnly.length >= 3) {
                formatted += "/" + digitsOnly.slice(2, 4);
            }
            if (digitsOnly.length >= 5) {
                formatted += "/" + digitsOnly.slice(4, 6);
            }
            
            if (formatted !== text) {
                input.value = formatted;
            }
        }
    },
    
    /**
     * Authentication Utilities
     */
    auth: {
        check: function() {
            const isLoggedIn = localStorage.getItem('gms_logged_in');
            if (isLoggedIn !== 'true') {
                window.location.href = 'login.html';
                return false;
            }
            return true;
        },
        
        logout: function() {
            localStorage.removeItem('gms_logged_in');
            localStorage.removeItem('gms_username');
            window.location.href = 'login.html';
        },
        
        getUsername: function() {
            return localStorage.getItem('gms_username') || 'User';
        }
    }
};

// Global shortcuts for backward compatibility
window.toggleTheme = GOMS.theme.toggle;
window.loadTheme = GOMS.theme.load;
window.formatDate = GOMS.format.date;
window.formatNumber = GOMS.format.number;
window.formatInteger = GOMS.format.integer;
window.formatDateInput = GOMS.format.dateInput;
window.checkAuth = GOMS.auth.check;
window.logout = GOMS.auth.logout;