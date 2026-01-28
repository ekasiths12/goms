/**
 * Pagination Component
 * Reusable pagination component that handles rendering and state management
 */

class PaginationComponent {
    constructor(config) {
        this.containerId = config.containerId || 'paginationContainer';
        this.currentPage = config.currentPage || 1;
        this.itemsPerPage = config.itemsPerPage || 50;
        this.dataLength = config.dataLength || 0;
        this.onPageChange = config.onPageChange || (() => {});
        this.infoId = config.infoId || 'paginationInfo';
        this.firstPageId = config.firstPageId || 'firstPage';
        this.prevPageId = config.prevPageId || 'prevPage';
        this.nextPageId = config.nextPageId || 'nextPage';
        this.lastPageId = config.lastPageId || 'lastPage';
        this.pageNumbersId = config.pageNumbersId || 'pageNumbers';
        
        this.container = null;
        this.maxVisiblePages = config.maxVisiblePages || 5;
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the pagination component
     */
    initialize() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`Pagination container not found: ${this.containerId}`);
            return;
        }
        
        this.render();
        this.setupEventListeners();
        this.update();
    }
    
    /**
     * Render pagination HTML
     */
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="pagination-controls">
                <div class="pagination-info">
                    <span id="${this.infoId}">Showing 0 of 0 records</span>
                </div>
                <div class="pagination-buttons">
                    <button class="pagination-btn" id="${this.firstPageId}">First</button>
                    <button class="pagination-btn" id="${this.prevPageId}">Previous</button>
                    <div id="${this.pageNumbersId}" class="page-numbers"></div>
                    <button class="pagination-btn" id="${this.nextPageId}">Next</button>
                    <button class="pagination-btn" id="${this.lastPageId}">Last</button>
                </div>
            </div>
        `;
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const firstBtn = document.getElementById(this.firstPageId);
        const prevBtn = document.getElementById(this.prevPageId);
        const nextBtn = document.getElementById(this.nextPageId);
        const lastBtn = document.getElementById(this.lastPageId);
        
        if (firstBtn) {
            firstBtn.addEventListener('click', () => this.goToPage(1));
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.goToPage(this.currentPage - 1));
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.goToPage(this.currentPage + 1));
        }
        
        if (lastBtn) {
            lastBtn.addEventListener('click', () => this.goToPage(this.getTotalPages()));
        }
    }
    
    /**
     * Get total number of pages
     */
    getTotalPages() {
        return Math.ceil(this.dataLength / this.itemsPerPage);
    }
    
    /**
     * Go to a specific page
     */
    goToPage(page) {
        const totalPages = this.getTotalPages();
        if (page < 1 || page > totalPages || page === this.currentPage) {
            return;
        }
        
        this.currentPage = page;
        this.update();
        
        if (this.onPageChange) {
            this.onPageChange(page);
        }
    }
    
    /**
     * Update pagination controls
     */
    update() {
        const totalPages = this.getTotalPages();
        const startRecord = this.dataLength > 0 ? (this.currentPage - 1) * this.itemsPerPage + 1 : 0;
        const endRecord = Math.min(this.currentPage * this.itemsPerPage, this.dataLength);
        
        // Update pagination info
        const paginationInfo = document.getElementById(this.infoId);
        if (paginationInfo) {
            paginationInfo.textContent = `Showing ${startRecord} to ${endRecord} of ${this.dataLength} records`;
        }
        
        // Update button states
        const firstPageBtn = document.getElementById(this.firstPageId);
        const prevPageBtn = document.getElementById(this.prevPageId);
        const nextPageBtn = document.getElementById(this.nextPageId);
        const lastPageBtn = document.getElementById(this.lastPageId);
        
        if (firstPageBtn) firstPageBtn.disabled = this.currentPage === 1;
        if (prevPageBtn) prevPageBtn.disabled = this.currentPage === 1;
        if (nextPageBtn) nextPageBtn.disabled = this.currentPage >= totalPages || totalPages === 0;
        if (lastPageBtn) lastPageBtn.disabled = this.currentPage >= totalPages || totalPages === 0;
        
        // Update page numbers
        this.updatePageNumbers(totalPages);
    }
    
    /**
     * Update page number buttons
     */
    updatePageNumbers(totalPages) {
        const pageNumbersContainer = document.getElementById(this.pageNumbersId);
        if (!pageNumbersContainer) return;
        
        pageNumbersContainer.innerHTML = '';
        
        if (totalPages === 0) {
            return;
        }
        
        // Calculate which page numbers to show
        let startPage = Math.max(1, this.currentPage - Math.floor(this.maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + this.maxVisiblePages - 1);
        
        // Adjust if we're near the end
        if (endPage - startPage < this.maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - this.maxVisiblePages + 1);
        }
        
        // Add first page and ellipsis if needed
        if (startPage > 1) {
            const firstBtn = this.createPageButton(1);
            pageNumbersContainer.appendChild(firstBtn);
            
            if (startPage > 2) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'pagination-ellipsis';
                ellipsis.textContent = '...';
                pageNumbersContainer.appendChild(ellipsis);
            }
        }
        
        // Add page number buttons
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = this.createPageButton(i);
            pageNumbersContainer.appendChild(pageBtn);
        }
        
        // Add last page and ellipsis if needed
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'pagination-ellipsis';
                ellipsis.textContent = '...';
                pageNumbersContainer.appendChild(ellipsis);
            }
            
            const lastBtn = this.createPageButton(totalPages);
            pageNumbersContainer.appendChild(lastBtn);
        }
    }
    
    /**
     * Create a page number button
     */
    createPageButton(pageNumber) {
        const button = document.createElement('button');
        button.className = 'pagination-btn';
        if (pageNumber === this.currentPage) {
            button.classList.add('active');
        }
        button.textContent = pageNumber;
        button.addEventListener('click', () => this.goToPage(pageNumber));
        return button;
    }
    
    /**
     * Update data length and refresh
     */
    updateDataLength(newLength) {
        this.dataLength = newLength;
        
        // Reset to page 1 if current page is beyond available pages
        const totalPages = this.getTotalPages();
        if (this.currentPage > totalPages && totalPages > 0) {
            this.currentPage = totalPages;
        } else if (totalPages === 0) {
            this.currentPage = 1;
        }
        
        this.update();
    }
    
    /**
     * Reset to first page
     */
    reset() {
        this.currentPage = 1;
        this.update();
    }
    
    /**
     * Get current page
     */
    getCurrentPage() {
        return this.currentPage;
    }
    
    /**
     * Get items per page
     */
    getItemsPerPage() {
        return this.itemsPerPage;
    }
    
    /**
     * Get paginated data slice
     */
    getPaginatedData(data) {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        return data.slice(startIndex, endIndex);
    }
    
    /**
     * Destroy pagination component
     */
    destroy() {
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}
