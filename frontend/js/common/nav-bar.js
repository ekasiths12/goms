/**
 * Navigation Bar Renderer
 * Renders the navigation bar HTML structure for all pages
 */

// Version number - update this when you need to increment the version
const NAV_VERSION = 'GOMSv2.10';

/**
 * Render navigation bar
 * @param {string} activeTab - The active tab name (e.g., 'fabric-invoices', 'stitching-records')
 */
function renderNavBar(activeTab = '') {
    const navBar = document.querySelector('.nav-bar');
    if (!navBar) {
        console.warn('Navigation bar container (.nav-bar) not found');
        return;
    }
    
    // Get username from localStorage (if available)
    const username = localStorage.getItem('gms_username') || 'User';
    
    navBar.innerHTML = `
        <ul class="nav-tabs">
            <li><a href="fabric-invoices.html" class="nav-tab ${activeTab === 'fabric-invoices' ? 'active' : ''}">Fabric Invoices</a></li>
            <li><a href="stitching-records.html" class="nav-tab ${activeTab === 'stitching-records' ? 'active' : ''}">Stitching Records</a></li>
            <li><a href="packing-lists.html" class="nav-tab ${activeTab === 'packing-lists' ? 'active' : ''}">Packing Lists</a></li>
            <li><a href="group-bills.html" class="nav-tab ${activeTab === 'group-bills' ? 'active' : ''}">Group Bills</a></li>
            <li><a href="dashboard.html" class="nav-tab ${activeTab === 'dashboard' ? 'active' : ''}">Dashboard</a></li>
        </ul>
        <div class="nav-user">
            <span class="version-indicator">${NAV_VERSION}</span>
            <button onclick="toggleTheme()" class="theme-toggle" id="themeToggle">
                <span class="icon" id="themeIcon">🌙</span>
                <span id="themeText">Dark</span>
            </button>
            <span id="currentUser">Welcome, ${username}</span>
            <button onclick="logout()" class="logout-btn">Logout</button>
        </div>
    `;
    
    // Load theme after rendering (if loadTheme function exists)
    if (typeof loadTheme === 'function') {
        loadTheme();
    }
}
