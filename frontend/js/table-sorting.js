/**
 * Table Sorting Utility
 * Reusable sorting functionality for all data tables
 */

class TableSorter {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.table = document.getElementById(tableId);
        this.options = {
            sortableClass: 'sortable-header',
            ascClass: 'sort-asc',
            descClass: 'sort-desc',
            dataAttribute: 'data-sort',
            ...options
        };
        
        this.currentSortColumn = null;
        this.currentSortDirection = 'asc';
        this.originalData = [];
        this.dataGetter = null;
        
        this.init();
    }
    
    init() {
        if (!this.table) {
            console.error(`Table with ID '${this.tableId}' not found`);
            return;
        }
        
        this.setupHeaders();
        console.log(`✅ TableSorter initialized for table: ${this.tableId}`);
    }
    
    setupHeaders() {
        const headers = this.table.querySelectorAll(`th.${this.options.sortableClass}`);
        console.log(`🔍 Found ${headers.length} sortable headers for table: ${this.tableId}`);
        
        headers.forEach(header => {
            const column = header.getAttribute(this.options.dataAttribute);
            console.log(`🔍 Header: ${header.textContent.trim()} -> column: ${column}`);
            
            header.addEventListener('click', (e) => {
                e.preventDefault();
                console.log(`🖱️ Header clicked: ${header.textContent.trim()} (${column})`);
                if (column) {
                    this.sort(column);
                } else {
                    console.error(`❌ No data-sort attribute found for header: ${header.textContent.trim()}`);
                }
            });
        });
    }
    
    setData(data, dataGetter = null) {
        this.originalData = [...data];
        this.dataGetter = dataGetter;
        console.log(`💾 Stored ${this.originalData.length} records for sorting`);
    }
    
    sort(column) {
        console.log(`🔄 Sorting table by column: ${column}`);
        
        // Clear previous sort indicators
        this.clearSortIndicators();
        
        // Determine sort direction
        if (this.currentSortColumn === column) {
            // Toggle direction if same column
            this.currentSortDirection = this.currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            // New column, start with ascending
            this.currentSortDirection = 'asc';
            this.currentSortColumn = column;
        }
        
        // Add sort indicator to clicked header
        const header = this.table.querySelector(`[${this.options.dataAttribute}="${column}"]`);
        if (header) {
            header.classList.add(`sort-${this.currentSortDirection}`);
        }
        
        // Sort the data
        const sortedData = this.sortData(column, this.currentSortDirection);
        
        // Trigger custom event for data update
        const event = new CustomEvent('tableSorted', {
            detail: {
                column: column,
                direction: this.currentSortDirection,
                data: sortedData
            }
        });
        this.table.dispatchEvent(event);
        
        return sortedData;
    }
    
    clearSortIndicators() {
        const headers = this.table.querySelectorAll(`.${this.options.sortableClass}`);
        headers.forEach(header => {
            header.classList.remove(this.options.ascClass, this.options.descClass);
        });
    }
    
    sortData(column, direction) {
        if (!this.originalData || this.originalData.length === 0) {
            console.log('⚠️ No data to sort');
            return [];
        }
        
        console.log(`🔄 Sorting ${this.originalData.length} records by ${column} in ${direction} order`);
        
        // Create a copy of the data to sort
        const sortedData = [...this.originalData];
        
        sortedData.sort((a, b) => {
            let aValue = this.getValueForSorting(a, column);
            let bValue = this.getValueForSorting(b, column);
            
            // Handle null/undefined values
            if (aValue === null || aValue === undefined) aValue = '';
            if (bValue === null || bValue === undefined) bValue = '';
            
            // Convert to strings for comparison
            aValue = String(aValue).toLowerCase();
            bValue = String(bValue).toLowerCase();
            
            let comparison = 0;
            
            // Handle different data types
            if (this.isDateColumn(column)) {
                // Date comparison
                const dateA = new Date(aValue);
                const dateB = new Date(bValue);
                comparison = dateA - dateB;
            } else if (this.isNumericColumn(column)) {
                // Numeric comparison
                comparison = parseFloat(aValue) - parseFloat(bValue);
            } else {
                // String comparison
                comparison = aValue.localeCompare(bValue);
            }
            
            return direction === 'asc' ? comparison : -comparison;
        });
        
        console.log(`✅ Sorted data by ${column} in ${direction} order`);
        return sortedData;
    }
    
    getValueForSorting(item, column) {
        // Use custom data getter if provided
        if (this.dataGetter && typeof this.dataGetter === 'function') {
            return this.dataGetter(item, column);
        }
        
        // Default implementation - access property directly
        return item[column] || '';
    }
    
    isDateColumn(column) {
        const dateColumns = ['date', 'created_at', 'updated_at', 'invoice_date', 'registration_date'];
        return dateColumns.includes(column);
    }
    
    isNumericColumn(column) {
        const numericColumns = [
            'quantity', 'price', 'total', 'amount', 'count', 'id',
            'yards_sent', 'yards_consumed', 'unit_price', 'pending'
        ];
        return numericColumns.includes(column);
    }
    
    getCurrentSort() {
        return {
            column: this.currentSortColumn,
            direction: this.currentSortDirection
        };
    }
    
    reset() {
        this.currentSortColumn = null;
        this.currentSortDirection = 'asc';
        this.clearSortIndicators();
    }
}

// Global table sorter instances
window.tableSorters = {};

// Utility function to create table sorter
window.createTableSorter = function(tableId, options = {}) {
    if (window.tableSorters[tableId]) {
        console.warn(`TableSorter for '${tableId}' already exists`);
        return window.tableSorters[tableId];
    }
    
    const sorter = new TableSorter(tableId, options);
    window.tableSorters[tableId] = sorter;
    return sorter;
};

// Utility function to get table sorter
window.getTableSorter = function(tableId) {
    return window.tableSorters[tableId];
};
