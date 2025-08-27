/**
 * Table Manager - Modular component for efficient table operations
 * Handles optimistic updates, partial data updates, and performance optimizations
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
        this.rowTemplate = options.rowTemplate || this.defaultRowTemplate;
        this.rowIdentifier = options.rowIdentifier || 'id';
        this.optimisticUpdates = options.optimisticUpdates !== false;
        
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
        
        console.log(`✅ TableManager initialized for ${this.tableId}`);
    }
    
    /**
     * Set the main data array
     */
    setData(data) {
        this.data = data || [];
        this.filteredData = [...this.data];
        this.currentPage = 1;
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
        
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
        const pageData = this.filteredData.slice(startIndex, endIndex);
        
        this.tableBody.innerHTML = '';
        
        if (pageData.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = '<td colspan="15" style="text-align: center; padding: 20px; color: var(--text-secondary);">No data found</td>';
            this.tableBody.appendChild(emptyRow);
            return;
        }
        
        pageData.forEach((item, index) => {
            const row = this.createRow(item, startIndex + index);
            this.tableBody.appendChild(row);
        });
        
        this.updatePagination();
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
     * Update pagination controls
     */
    updatePagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = Math.min(startIndex + this.itemsPerPage, this.filteredData.length);
        
        // Update pagination info
        const startElement = document.getElementById('paginationStart');
        const endElement = document.getElementById('paginationEnd');
        const totalElement = document.getElementById('paginationTotal');
        
        if (startElement) startElement.textContent = this.filteredData.length > 0 ? startIndex + 1 : 0;
        if (endElement) endElement.textContent = endIndex;
        if (totalElement) totalElement.textContent = this.filteredData.length;
        
        // Update button states
        const firstBtn = document.getElementById('firstPage');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        const lastBtn = document.getElementById('lastPage');
        
        if (firstBtn) firstBtn.disabled = this.currentPage <= 1;
        if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
        if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;
        if (lastBtn) lastBtn.disabled = this.currentPage >= totalPages;
        
        // Update page numbers
        this.updatePageNumbers(totalPages);
    }
    
    /**
     * Update page number buttons
     */
    updatePageNumbers(totalPages) {
        const pageNumbersSpan = document.getElementById('pageNumbers');
        if (!pageNumbersSpan) return;
        
        pageNumbersSpan.innerHTML = '';
        
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `pagination-btn ${i === this.currentPage ? 'active' : ''}`;
            pageBtn.textContent = i;
            pageBtn.onclick = () => this.goToPage(i);
            pageNumbersSpan.appendChild(pageBtn);
        }
    }
    
    /**
     * Go to specific page
     */
    goToPage(page) {
        const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
        if (page >= 1 && page <= totalPages) {
            this.currentPage = page;
            this.render();
        }
    }
    
    /**
     * Get selected row IDs
     */
    getSelectedRowIds() {
        const checkboxes = this.tableBody.querySelectorAll('.row-checkbox:checked');
        return Array.from(checkboxes).map(cb => cb.getAttribute('data-id'));
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
