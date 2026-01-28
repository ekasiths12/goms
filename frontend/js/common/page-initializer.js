/**
 * Page Initializer
 * Handles common page initialization patterns:
 * - Theme loading
 * - Auth checking
 * - Navigation bar rendering
 * - Data loading coordination
 * - Filter setup coordination
 */

class PageInitializer {
    constructor(config) {
        this.activeTab = config.activeTab || '';
        this.onAuthSuccess = config.onAuthSuccess || (() => {});
        this.onAuthFailure = config.onAuthFailure || (() => {});
        this.loadTheme = config.loadTheme !== false; // Default true
        this.checkAuth = config.checkAuth !== false; // Default true
        this.renderNav = config.renderNav !== false; // Default true
    }
    
    /**
     * Initialize page with common setup
     */
    async initialize() {
        console.log(`🔄 Initializing page: ${this.activeTab || 'default'}`);
        
        // Load theme immediately to prevent flashing
        if (this.loadTheme && typeof loadTheme === 'function') {
            loadTheme();
        }
        
        // Render navigation bar
        if (this.renderNav && typeof renderNavBar === 'function') {
            renderNavBar(this.activeTab);
        }
        
        // Check authentication
        if (this.checkAuth) {
            if (typeof checkAuth === 'function') {
                const isAuthenticated = checkAuth();
                if (!isAuthenticated) {
                    if (this.onAuthFailure) {
                        this.onAuthFailure();
                    }
                    return false;
                }
            }
        }
        
        // Call success callback
        if (this.onAuthSuccess) {
            await this.onAuthSuccess();
        }
        
        return true;
    }
    
    /**
     * Initialize page on window load
     */
    static onLoad(config) {
        window.addEventListener('load', async () => {
            const initializer = new PageInitializer(config);
            await initializer.initialize();
        });
    }
    
    /**
     * Initialize page on DOM content loaded
     */
    static onDOMReady(config) {
        document.addEventListener('DOMContentLoaded', async () => {
            const initializer = new PageInitializer(config);
            await initializer.initialize();
        });
    }
    
    /**
     * Initialize page immediately (for inline scripts)
     */
    static async init(config) {
        const initializer = new PageInitializer(config);
        return await initializer.initialize();
    }
}

// Export for use in modules (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PageInitializer, PaginationComponent };
}
