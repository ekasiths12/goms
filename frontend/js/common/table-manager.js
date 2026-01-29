/**
 * Table Manager - Modular component for efficient table operations
 * Handles optimistic updates, partial data updates, and performance optimizations
 * Uses PaginationComponent for pagination functionality
 */
class TableManager {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.tableBody = document.getElementById(tableId + 'Body');
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 50;
        this.onDataUpdate = options.onDataUpdate || (() => {});
        this.onRowUpdate = options.onRowUpdate || (() => {});
        this.onSelectionChange = options.onSelectionChange || (() => {});
        this.rowTemplate = options.rowTemplate || this.defaultRowTemplate;
        this.rowIdentifier = options.rowIdentifier || 'id';
        this.optimisticUpdates = options.optimisticUpdates !== false;
        
        // Pagination component
        this.paginationComponent = null;
        this.paginationContainerId = options.paginationContainerId || 'paginationContainer';
        
        // Performance tracking
        this.lastUpdateTime = 0;
        this.updateQueue = [];
        this.isUpdating = false;
        
        // Initialize
        this.initialize();
    }
    
    initialize() {
        if (!this.tableBody) {
            console.error(`Table body not found: ${this.tableId}Body`);
            return;
        }
        
        console.log(`🔍 Checking for pagination container: ${this.paginationContainerId}`);
        
        // Initialize PaginationComponent if container exists
        // Try multiple times to ensure DOM is ready
        const tryInitializePagination = () => {
            const container = document.getElementById(this.paginationContainerId);
            if (container) {
                console.log(`✅ Pagination container found: ${this.paginationContainerId}`);
                this.initializePagination();
            } else {
                console.warn(`⚠️ Pagination container not found: ${this.paginationContainerId}. Will retry...`);
            }
        };
        
        // Try immediately
        tryInitializePagination();
        
        // Also try after a short delay
        setTimeout(tryInitializePagination, 100);
        
        // And try after a longer delay as fallback
        setTimeout(tryInitializePagination, 500);
        
        console.log(`✅ TableManager initialized for ${this.tableId}`);
    }
    
    /**
     * Initialize PaginationComponent
     */
    initializePagination() {
        console.log(`🔍 initializePagination() called for container: ${this.paginationContainerId}`);
        
        // Check if PaginationComponent class is available
        if (typeof PaginationComponent === 'undefined') {
            console.error(`❌ PaginationComponent class is not defined! Make sure pagination.js is loaded before table-manager.js`);
            return false;
        }
        
        const container = document.getElementById(this.paginationContainerId);
        if (!container) {
            console.warn(`⚠️ Pagination container not found: ${this.paginationContainerId}. Will retry when data is loaded.`);
            return false;
        }
        
        // Don't re-initialize if already exists
        if (this.paginationComponent) {
            console.log(`ℹ️ PaginationComponent already initialized for ${this.paginationContainerId}`);
            return true;
        }
        
        console.log(`🔄 Creating PaginationComponent for container: ${this.paginationContainerId}`);
        console.log(`   - Current page: ${this.currentPage}`);
        console.log(`   - Items per page: ${this.itemsPerPage}`);
        console.log(`   - Data length: ${this.filteredData.length}`);
        
        try {
            this.paginationComponent = new PaginationComponent({
                containerId: this.paginationContainerId,
                currentPage: this.currentPage,
                itemsPerPage: this.itemsPerPage,
                dataLength: this.filteredData.length, // Use current filtered data length
                onPageChange: (page) => {
                    console.log(`📄 Page changed to: ${page}`);
                    this.currentPage = page;
                    // Re-render with new page
                    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
                    const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
                    const pageData = this.filteredData.slice(startIndex, endIndex);
                    
                    this.tableBody.innerHTML = '';
                    if (pageData.length === 0) {
                        const emptyRow = document.createElement('tr');
                        emptyRow.innerHTML = '<td colspan="15" style="text-align: center; padding: 20px; color: var(--text-secondary);">No data found</td>';
                        this.tableBody.appendChild(emptyRow);
                    } else {
                        pageData.forEach((item, index) => {
                            const row = this.createRow(item, startIndex + index);
                            this.tableBody.appendChild(row);
                        });
                    }
                }
            });
            
            console.log(`✅ PaginationComponent created successfully`);
            console.log(`   - Container element:`, container);
            console.log(`   - Container innerHTML length:`, container.innerHTML ? container.innerHTML.length : 0);
            return true;
        } catch (error) {
            console.error(`❌ Error initializing PaginationComponent:`, error);
            console.error(`   - Error stack:`, error.stack);
            return false;
        }
    }
    
    /**
     * Set the main data array
     */
    setData(data) {
        this.data = data || [];
        this.filteredData = [...this.data];
        this.currentPage = 1;
        
        // Ensure pagination is initialized (in case it wasn't ready before)
        if (!this.paginationComponent) {
            console.log(`🔄 Attempting to initialize pagination in setData()...`);
            const initialized = this.initializePagination();
            if (!initialized) {
                console.warn(`⚠️ Pagination initialization failed. Will retry on next render.`);
            }
        }
        
        // Update pagination component if it exists
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.filteredData.length);
            this.paginationComponent.reset();
        }
        
        this.render();
        this.onDataUpdate(this.data);
    }
    
    /**
     * Get current data
     */
    getData() {
        return this.data;
    }
    
    /**
     * Get filtered data
     */
    getFilteredData() {
        return this.filteredData;
    }
    
    /**
     * Apply filters to data
     */
    applyFilters(filters = {}) {
        this.filteredData = this.data.filter(item => {
            return Object.keys(filters).every(key => {
                const filterValue = filters[key];
                if (!filterValue || filterValue === '') return true;
                
                const itemValue = this.getNestedValue(item, key);
                if (typeof itemValue === 'string') {
                    return itemValue.toLowerCase().includes(filterValue.toLowerCase());
                }
                return itemValue == filterValue;
            });
        });
        
        this.currentPage = 1;
        this.render();
    }
    
    /**
     * Get nested object value using dot notation
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : '';
        }, obj);
    }
    
    /**
     * Update a single row optimistically
     */
    updateRow(rowId, updates) {
        const rowIndex = this.findRowIndex(rowId);
        if (rowIndex === -1) return false;
        
        // Update data
        this.data[rowIndex] = { ...this.data[rowIndex], ...updates };
        
        // Update filtered data if it exists
        const filteredIndex = this.filteredData.findIndex(item => 
            item[this.rowIdentifier] == rowId
        );
        if (filteredIndex !== -1) {
            this.filteredData[filteredIndex] = { ...this.filteredData[filteredIndex], ...updates };
        }
        
        // Update UI immediately
        this.updateRowInUI(rowId, updates);
        
        return true;
    }
    
    /**
     * Update multiple rows optimistically
     */
    updateRows(rowIds, updates) {
        const updatedRows = [];
        
        rowIds.forEach(rowId => {
            if (this.updateRow(rowId, updates)) {
                updatedRows.push(rowId);
            }
        });
        
        return updatedRows;
    }
    
    /**
     * Add new row
     */
    addRow(rowData) {
        this.data.unshift(rowData);
        this.filteredData.unshift(rowData);
        this.render();
    }
    
    /**
     * Remove row
     */
    removeRow(rowId) {
        const dataIndex = this.findRowIndex(rowId);
        if (dataIndex !== -1) {
            this.data.splice(dataIndex, 1);
        }
        
        const filteredIndex = this.filteredData.findIndex(item => 
            item[this.rowIdentifier] == rowId
        );
        if (filteredIndex !== -1) {
            this.filteredData.splice(filteredIndex, 1);
        }
        
        this.render();
    }
    
    /**
     * Remove multiple rows
     */
    removeRows(rowIds) {
        rowIds.forEach(rowId => this.removeRow(rowId));
    }
    
    /**
     * Find row index in data array
     */
    findRowIndex(rowId) {
        return this.data.findIndex(item => item[this.rowIdentifier] == rowId);
    }
    
    /**
     * Update row in UI without full re-render
     */
    updateRowInUI(rowId, updates) {
        const rowElement = this.tableBody.querySelector(`[data-row-id="${rowId}"]`);
        if (!rowElement) return;
        
        // Update specific cells based on updates
        Object.keys(updates).forEach(key => {
            const cell = rowElement.querySelector(`[data-field="${key}"]`);
            if (cell) {
                const newValue = this.formatCellValue(key, updates[key]);
                cell.innerHTML = newValue;
            }
        });
        
        // Call custom row update handler
        this.onRowUpdate(rowElement, updates);
    }
    
    /**
     * Format cell value for display
     */
    formatCellValue(field, value) {
        if (value === null || value === undefined) return '';
        
        switch (field) {
            case 'invoice_date':
            case 'date':
                return this.formatDate(value);
            case 'unit_price':
            case 'price':
            case 'total':
            case 'cost':
                return this.formatNumber(value);
            case 'yards_sent':
            case 'yards_consumed':
            case 'total_used':
            case 'pending':
            case 'quantity':
                return this.formatNumber(value);
            default:
                return String(value);
        }
    }
    
    /**
     * Format date as DD/MM/YY
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear().toString().slice(-2);
        return `${day}/${month}/${year}`;
    }
    
    /**
     * Format number with 2 decimal places
     */
    formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num || 0);
    }
    
    /**
     * Render the table
     */
    render() {
        if (!this.tableBody) return;
        
        // Get current page from PaginationComponent if available, otherwise use internal
        const page = this.paginationComponent ? this.paginationComponent.getCurrentPage() : this.currentPage;
        const startIndex = (page - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
        const pageData = this.filteredData.slice(startIndex, endIndex);
        
        this.tableBody.innerHTML = '';
        
        if (pageData.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = '<td colspan="15" style="text-align: center; padding: 20px; color: var(--text-secondary);">No data found</td>';
            this.tableBody.appendChild(emptyRow);
        } else {
            pageData.forEach((item, index) => {
                const row = this.createRow(item, startIndex + index);
                this.tableBody.appendChild(row);
            });
        }
        
        // Update pagination component if it exists
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.filteredData.length);
            // Sync current page if it changed
            if (this.paginationComponent.getCurrentPage() !== page) {
                this.paginationComponent.goToPage(page);
            } else {
                this.paginationComponent.update();
            }
        } else {
            // Try to initialize pagination if it doesn't exist yet
            console.log(`🔄 Attempting to initialize pagination in render()...`);
            const initialized = this.initializePagination();
            if (initialized && this.paginationComponent) {
                this.paginationComponent.updateDataLength(this.filteredData.length);
                this.paginationComponent.update();
            } else {
                // Fallback: Update old pagination controls if PaginationComponent not available
                this.updatePagination();
            }
        }
    }
    
    /**
     * Create a table row
     */
    createRow(item, index) {
        const row = document.createElement('tr');
        row.setAttribute('data-row-id', item[this.rowIdentifier]);
        row.setAttribute('data-index', index);
        
        if (this.rowTemplate) {
            row.innerHTML = this.rowTemplate(item, index);
        } else {
            row.innerHTML = this.defaultRowTemplate(item, index);
        }
        
        return row;
    }
    
    /**
     * Default row template
     */
    defaultRowTemplate(item, index) {
        return `
            <td class="checkbox-wrapper">
                <input type="checkbox" class="row-checkbox" data-id="${item[this.rowIdentifier]}">
            </td>
            <td data-field="date">${this.formatDate(item.invoice_date || item.date)}</td>
            <td data-field="short_name">${item.customer?.short_name || ''}</td>
            <td data-field="invoice_number">${item.invoice_number || ''}</td>
            <td data-field="tax_invoice_number">${item.tax_invoice_number || ''}</td>
            <td data-field="item_name">${item.item_name || ''}</td>
            <td data-field="color">${item.color || ''}</td>
            <td data-field="delivery_note">${item.delivery_note || ''}</td>
            <td data-field="yards_sent">${this.formatNumber(item.yards_sent || item.quantity)}</td>
            <td data-field="total_used">${this.formatNumber(item.total_used || 0)}</td>
            <td data-field="pending">${this.formatNumber(item.pending_yards || 0)}</td>
            <td data-field="unit_price">${this.formatNumber(item.unit_price || 0)}</td>
            <td data-field="total">${this.formatNumber((item.yards_sent || item.quantity) * (item.unit_price || 0))}</td>
            <td data-field="delivered_location">${item.delivered_location || ''}</td>
            <td>Actions</td>
        `;
    }
    
    /**
     * Update pagination controls (legacy method - kept for backward compatibility)
     * This is now handled by PaginationComponent, but kept as fallback
     */
    updatePagination() {
        // This method is deprecated - PaginationComponent handles this now
        // Kept for backward compatibility if PaginationComponent is not available
        console.warn('TableManager.updatePagination() is deprecated. Use PaginationComponent instead.');
    }
    
    /**
     * Go to specific page
     */
    goToPage(page) {
        if (this.paginationComponent) {
            this.paginationComponent.goToPage(page);
            // onPageChange callback will handle rendering
        } else {
            // Fallback if PaginationComponent not available
            const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
            if (page >= 1 && page <= totalPages) {
                this.currentPage = page;
                this.render();
            }
        }
    }
    
    /**
     * Get current page (for compatibility)
     */
    getCurrentPage() {
        if (this.paginationComponent) {
            return this.paginationComponent.getCurrentPage();
        }
        return this.currentPage;
    }
    
    /**
     * Get selected row IDs
     */
    getSelectedRowIds() {
        const checkboxes = this.tableBody.querySelectorAll('.row-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.getAttribute('data-id'));
    }
    
    /**
     * Get selected rows data
     */
    getSelectedRows() {
        const selectedIds = this.getSelectedRowIds();
        return selectedIds.map(id => this.getRowById(id)).filter(row => row !== null);
    }
    
    /**
     * Select all rows
     */
    selectAll(checked) {
        const checkboxes = this.tableBody.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => cb.checked = checked);
    }
    
    /**
     * Clear all selections
     */
    clearSelection() {
        const checkboxes = this.tableBody.querySelectorAll('.row-checkbox:checked');
        checkboxes.forEach(cb => cb.checked = false);
        this.onSelectionChange(this.getSelectedRows());
    }
    
    /**
     * Batch update multiple operations
     */
    batchUpdate(operations) {
        operations.forEach(op => {
            switch (op.type) {
                case 'update':
                    this.updateRow(op.rowId, op.data);
                    break;
                case 'remove':
                    this.removeRow(op.rowId);
                    break;
                case 'add':
                    this.addRow(op.data);
                    break;
            }
        });
    }
    
    /**
     * Refresh data from server (when needed)
     */
    async refreshData(fetchFunction) {
        if (typeof fetchFunction === 'function') {
            try {
                const newData = await fetchFunction();
                this.setData(newData);
                return true;
            } catch (error) {
                console.error('Error refreshing data:', error);
                return false;
            }
        }
        return false;
    }
    
    /**
     * Get current page data
     */
    getCurrentPageData() {
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
        return this.filteredData.slice(startIndex, endIndex);
    }
    
    /**
     * Get row by ID
     */
    getRowById(rowId) {
        return this.data.find(item => item[this.rowIdentifier] == rowId);
    }
    
    /**
     * Get rows by IDs
     */
    getRowsByIds(rowIds) {
        return this.data.filter(item => rowIds.includes(item[this.rowIdentifier]));
    }
    
    /**
     * Destroy the table manager
     */
    destroy() {
        this.data = [];
        this.filteredData = [];
        this.tableBody = null;
        console.log(`🗑️ TableManager destroyed for ${this.tableId}`);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TableManager;
}
