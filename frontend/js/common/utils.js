/**
 * GOMS Common Utilities
 * Shared functions used across all pages
 * 
 * Function #1: Theme Management (toggleTheme, loadTheme)
 * Function #2: Formatting Utilities (formatDate, formatNumber, formatInteger, formatDateInput)
 * Function #3: API Utilities (getApiBaseUrl)
 * Function #4: Authentication Utilities (checkAuth, logout)
 * Function #5: Date Utilities (isDateInRange, parseDDMMYY, formatForAPI)
 * Function #6: Pagination Utilities (getTotalPages, goToPage, updatePaginationControls)
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
     * API Utilities
     */
    api: {
        getBaseUrl: function() {
            const hostname = window.location.hostname;
            const port = window.location.port;
            const protocol = window.location.protocol;
            
            console.log('🔍 getApiBaseUrl debug:', { hostname, port, protocol });
            
            // Local development - Flask backend runs on port 8000
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                // If frontend is on port 3000, backend should be on 8000
                if (port === '3000') {
                    return 'http://localhost:8000';
                }
                // If frontend is on port 5000, backend is on 8000
                if (port === '5000') {
                    return 'http://localhost:8000';
                }
                // Default to port 8000 for local development
                return 'http://localhost:8000';
            }
            
            // Railway deployment - force HTTPS
            if (hostname.includes('railway.app') || hostname.includes('up.railway.app')) {
                // Force HTTPS for Railway
                const httpsUrl = `https://${hostname}`;
                console.log('🚀 Using Railway HTTPS URL:', httpsUrl);
                return httpsUrl;
            }
            
            // Other deployments - use same protocol and domain, but prefer HTTPS
            const origin = window.location.origin;
            if (protocol === 'https:') {
                return origin;
            } else {
                // Force HTTPS for production
                return origin.replace('http://', 'https://');
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
    },
    
    /**
     * Date Utilities
     */
    date: {
        isInRange: function(date, filterDate, type) {
            if (!filterDate || filterDate.length !== 8 || filterDate.split('/').length !== 3) {
                return true;
            }
            
            try {
                const [day, month, year] = filterDate.split('/');
                const fullYear = year.length === 2 ? (parseInt(year) < 50 ? '20' + year : '19' + year) : year;
                const filterDateObj = new Date(`${fullYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`);
                
                if (type === 'from') {
                    return date >= filterDateObj;
                } else {
                    return date <= filterDateObj;
                }
            } catch (error) {
                return true;
            }
        },
        
        parseDDMMYY: function(dateString) {
            // Convert DD/MM/YY to Date object
            if (!dateString || dateString.length !== 8 || dateString.split('/').length !== 3) {
                return null;
            }
            
            try {
                const [day, month, year] = dateString.split('/');
                const fullYear = year.length === 2 ? (parseInt(year) < 50 ? '20' + year : '19' + year) : year;
                return new Date(`${fullYear}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`);
            } catch (error) {
                return null;
            }
        },
        
        formatForAPI: function(dateString) {
            // Convert DD/MM/YY to YYYY-MM-DD for API
            const date = this.parseDDMMYY(dateString);
            if (!date) return null;
            
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }
    },
    
    /**
     * Pagination Utilities
     * Note: These functions require page-specific variables (currentPage, itemsPerPage, dataArray)
     * They are designed to be called with the appropriate context
     */
    pagination: {
        getTotalPages: function(dataLength, itemsPerPage) {
            return Math.ceil(dataLength / itemsPerPage);
        },
        
        goToPage: function(page, totalPages, onPageChange) {
            if (page < 1 || page > totalPages) {
                return;
            }
            if (onPageChange) {
                onPageChange(page);
            }
        },
        
        updateControls: function(options) {
            // options: { currentPage, dataLength, itemsPerPage, paginationInfoId, firstPageId, prevPageId, nextPageId, lastPageId, pageNumbersId, onPageChange }
            const {
                currentPage,
                dataLength,
                itemsPerPage,
                paginationInfoId = 'paginationInfo',
                firstPageId = 'firstPage',
                prevPageId = 'prevPage',
                nextPageId = 'nextPage',
                lastPageId = 'lastPage',
                pageNumbersId = 'pageNumbers',
                onPageChange
            } = options;
            
            const totalPages = Math.ceil(dataLength / itemsPerPage);
            const startRecord = (currentPage - 1) * itemsPerPage + 1;
            const endRecord = Math.min(currentPage * itemsPerPage, dataLength);
            
            // Update pagination info
            const paginationInfo = document.getElementById(paginationInfoId);
            if (paginationInfo) {
                paginationInfo.textContent = `Showing ${startRecord} to ${endRecord} of ${dataLength} records`;
            }
            
            // Update button states
            const firstPageBtn = document.getElementById(firstPageId);
            const prevPageBtn = document.getElementById(prevPageId);
            const nextPageBtn = document.getElementById(nextPageId);
            const lastPageBtn = document.getElementById(lastPageId);
            
            if (firstPageBtn) firstPageBtn.disabled = currentPage === 1;
            if (prevPageBtn) prevPageBtn.disabled = currentPage === 1;
            if (nextPageBtn) nextPageBtn.disabled = currentPage === totalPages;
            if (lastPageBtn) lastPageBtn.disabled = currentPage === totalPages;
            
            // Update page numbers
            const pageNumbersContainer = document.getElementById(pageNumbersId);
            if (pageNumbersContainer) {
                pageNumbersContainer.innerHTML = '';
                
                const maxVisiblePages = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
                let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
                
                if (endPage - startPage + 1 < maxVisiblePages) {
                    startPage = Math.max(1, endPage - maxVisiblePages + 1);
                }
                
                for (let i = startPage; i <= endPage; i++) {
                    const pageBtn = document.createElement('button');
                    pageBtn.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
                    pageBtn.textContent = i;
                    pageBtn.onclick = () => {
                        if (onPageChange) {
                            onPageChange(i);
                        }
                    };
                    pageNumbersContainer.appendChild(pageBtn);
                }
            }
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
window.getApiBaseUrl = GOMS.api.getBaseUrl;
window.checkAuth = GOMS.auth.check;
window.logout = GOMS.auth.logout;
window.isDateInRange = GOMS.date.isInRange;
window.parseDDMMYY = GOMS.date.parseDDMMYY;
window.formatForAPI = GOMS.date.formatForAPI;