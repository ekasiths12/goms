/**
 * Hierarchical Table Manager - Base component for tables with parent-child relationships
 * Supports flat tables (no hierarchy) and hierarchical tables (with expand/collapse)
 * 
 * Phase 1: Foundation - Basic table rendering, row selection, sorting, pagination
 */
class HierarchicalTableManager {
    constructor(tableId, options = {}) {
        this.tableId = tableId;
        this.tableBody = document.getElementById(tableId + 'Body');
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 50;
        
        // Hierarchy configuration
        this.hierarchical = options.hierarchical || false;
        this.parentKey = options.parentKey || 'parent_id';
        this.childKey = options.childKey || 'id';
        this.expandedRows = new Set(); // Track expanded parent rows
        
        // Row template and configuration
        this.rowTemplate = options.rowTemplate || this.defaultRowTemplate;
        this.rowIdentifier = options.rowIdentifier || 'id';
        this.parentRowTemplate = options.parentRowTemplate || null;
        this.childRowTemplate = options.childRowTemplate || null;
        
        // Selection
        this.selectedRows = new Set();
        this.onSelectionChange = options.onSelectionChange || (() => {});
        
        // Sorting
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.sortableColumns = options.sortableColumns || [];
        
        // Pagination
        this.paginationComponent = null;
        this.paginationContainerId = options.paginationContainerId || 'paginationContainer';
        /** When true, data is one page from the server; total count comes from setServerSideTotal(total). */
        this.serverSidePagination = options.serverSidePagination || false;
        /** Total record count from server (used when serverSidePagination is true). */
        this.serverSideTotal = 0;
        /** Callback when user requests a page (page number). Page should refetch with offset and call setData + setServerSideTotal. */
        this.onPageChange = options.onPageChange || null;

        // Action buttons configuration
        this.actionButtons = options.actionButtons || [];
        
        // Callbacks
        this.onDataUpdate = options.onDataUpdate || (() => {});
        this.onRowUpdate = options.onRowUpdate || (() => {});
        
        // Custom render: when set, render() calls customRender(pageData) instead of building rows (for pages that keep their own row markup)
        this.customRender = options.customRender || null;
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the table manager
     */
    initialize() {
        if (!this.tableBody) {
            console.error(`Table body not found: ${this.tableId}Body`);
            return;
        }

        // Initialize PaginationComponent if container exists (retry a few times in case DOM is still settling)
        const tryInitializePagination = () => {
            const container = document.getElementById(this.paginationContainerId);
            if (container) {
                this.initializePagination();
            }
        };

        tryInitializePagination();
        setTimeout(tryInitializePagination, 100);
        setTimeout(tryInitializePagination, 500);
        
        console.log(`✅ HierarchicalTableManager initialized for ${this.tableId}`);
    }
    
    /**
     * Initialize PaginationComponent
     */
    initializePagination() {
        if (typeof PaginationComponent === 'undefined') {
            console.error(`❌ PaginationComponent class is not defined! Make sure pagination.js is loaded before hierarchical-table-manager.js`);
            return false;
        }

        const container = document.getElementById(this.paginationContainerId);
        if (!container) {
            console.warn(`Pagination container not found: ${this.paginationContainerId}. Pagination will not be available.`);
            return false;
        }

        if (this.paginationComponent) {
            return true;
        }

        const onPageChangeHandler = this.serverSidePagination && this.onPageChange
            ? (page) => {
                this.currentPage = page;
                this.onPageChange(page);
            }
            : (page) => {
                this.currentPage = page;
                this.render();
            };

        this.paginationComponent = new PaginationComponent({
            containerId: this.paginationContainerId,
            currentPage: this.currentPage,
            itemsPerPage: this.itemsPerPage,
            dataLength: this.getPaginationDataLength(),
            onPageChange: onPageChangeHandler
        });

        return true;
    }
    
    /**
     * Set the main data array. When serverSidePagination is true, data is one page; call setServerSideTotal(total) after this to update pagination.
     */
    setData(data) {
        this.data = data || [];
        this.filteredData = [...this.data];
        if (!this.serverSidePagination) {
            this.currentPage = 1;
        }
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.getPaginationDataLength());
            if (!this.serverSidePagination) {
                this.paginationComponent.reset();
            } else {
                this.paginationComponent.update();
            }
        }
        this.render();
        this.onDataUpdate(this.data);
    }

    /**
     * Set total record count from server (for server-side pagination). Call after setData(pageItems).
     */
    setServerSideTotal(total) {
        this.serverSideTotal = Math.max(0, parseInt(total, 10) || 0);
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.serverSideTotal);
            this.paginationComponent.update();
        }
    }
    
    /**
     * Apply filters to data
     */
    applyFilters(filters) {
        // This will be implemented based on FilterManager integration
        // For now, just set filteredData to data
        this.filteredData = [...this.data];
        this.currentPage = 1;
        
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.getPaginationDataLength());
            this.paginationComponent.reset();
        }
        
        this.render();
    }
    
    /**
     * Render the table
     */
    render() {
        if (!this.tableBody) return;

        const page = this.paginationComponent ? this.paginationComponent.getCurrentPage() : this.currentPage;

        let pageData;
        let startIndex;
        if (this.serverSidePagination) {
            pageData = this.filteredData;
            startIndex = (page - 1) * this.itemsPerPage;
        } else {
            const paginationData = this.hierarchical ? this.getParentRows(this.filteredData) : this.filteredData;
            startIndex = (page - 1) * this.itemsPerPage;
            const endIndex = Math.min(startIndex + this.itemsPerPage, paginationData.length);
            pageData = paginationData.slice(startIndex, endIndex);
        }
        
        if (this.customRender && typeof this.customRender === 'function') {
            this.customRender(pageData);
        } else {
            this.tableBody.innerHTML = '';
            if (pageData.length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="100%" style="text-align: center; padding: 20px; color: var(--text-secondary);">No data found</td>';
                this.tableBody.appendChild(emptyRow);
            } else {
                if (this.hierarchical) {
                    this.renderHierarchicalTable(pageData, startIndex);
                } else {
                    this.renderFlatTable(pageData, startIndex);
                }
            }
        }
        
        // Update pagination component if it exists
        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.getPaginationDataLength());
            if (this.paginationComponent.getCurrentPage() !== page) {
                this.paginationComponent.goToPage(page);
            } else {
                this.paginationComponent.update();
            }
        }
    }
    
    /**
     * Render flat table (no hierarchy)
     */
    renderFlatTable(pageData, startIndex) {
        pageData.forEach((item, index) => {
            const row = this.createRow(item, startIndex + index);
            this.tableBody.appendChild(row);
        });
    }
    
    /**
     * Render hierarchical table (with parent-child relationships)
     */
    renderHierarchicalTable(pageData, startIndex) {
        // Note: for hierarchical pagination, pageData is expected to contain only parent rows.
        const parentRows = pageData;
        const childMap = this.buildChildMap(this.filteredData);
        
        // Render parent rows and their children
        parentRows.forEach((parent, parentIndex) => {
            const row = this.createParentRow(parent, startIndex + parentIndex);
            this.tableBody.appendChild(row);
            
            // Render children if parent is expanded
            if (this.expandedRows.has(parent[this.rowIdentifier])) {
                const children = childMap.get(parent[this.rowIdentifier]) || [];
                children.forEach((child, childIndex) => {
                    const childRow = this.createChildRow(child, startIndex + parentIndex, childIndex);
                    this.tableBody.appendChild(childRow);
                });
            }
        });
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
        
        // Attach event listeners
        this.attachRowEventListeners(row, item);

        // Sync checkbox checked state (supports templates that don’t set `checked`)
        this.syncRowCheckboxState(row, item[this.rowIdentifier]);
        
        return row;
    }
    
    /**
     * Create a parent row (for hierarchical tables)
     */
    createParentRow(item, index) {
        const row = document.createElement('tr');
        row.className = 'parent-row';
        row.setAttribute('data-row-id', item[this.rowIdentifier]);
        row.setAttribute('data-index', index);
        
        if (this.parentRowTemplate) {
            row.innerHTML = this.parentRowTemplate(item, index, this.expandedRows.has(item[this.rowIdentifier]));
        } else {
            row.innerHTML = this.defaultParentRowTemplate(item, index);
        }
        
        // Attach event listeners
        this.attachRowEventListeners(row, item);

        // Sync checkbox checked state
        this.syncRowCheckboxState(row, item[this.rowIdentifier]);
        
        return row;
    }
    
    /**
     * Create a child row (for hierarchical tables)
     */
    createChildRow(item, parentIndex, childIndex) {
        const row = document.createElement('tr');
        row.className = 'child-row';
        row.setAttribute('data-row-id', item[this.rowIdentifier]);
        row.setAttribute('data-parent-id', item[this.parentKey]);
        
        if (this.childRowTemplate) {
            row.innerHTML = this.childRowTemplate(item, parentIndex, childIndex);
        } else {
            row.innerHTML = this.defaultChildRowTemplate(item, parentIndex, childIndex);
        }
        
        // Attach event listeners
        this.attachRowEventListeners(row, item);

        // Sync checkbox checked state
        this.syncRowCheckboxState(row, item[this.rowIdentifier]);
        
        return row;
    }

    /**
     * Sync checkbox UI for a row with `selectedRows`
     */
    syncRowCheckboxState(rowElement, rowId) {
        const checkbox = rowElement.querySelector('.row-checkbox');
        if (!checkbox) return;
        checkbox.checked = this.selectedRows.has(rowId);
    }
    
    /**
     * Attach event listeners to a row
     */
    attachRowEventListeners(row, item) {
        // Checkbox selection
        const checkbox = row.querySelector('.row-checkbox');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.handleRowSelection(item[this.rowIdentifier], e.target.checked);
            });
        }
        
        // Expand/collapse for parent rows
        const expandBtn = row.querySelector('.expand-btn, .collapse-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', () => {
                this.toggleRowExpansion(item[this.rowIdentifier]);
            });
        }
        
        // Action buttons
        this.actionButtons.forEach(buttonConfig => {
            const actionBtn = row.querySelector(`[data-action="${buttonConfig.action}"]`);
            if (actionBtn) {
                actionBtn.addEventListener('click', () => {
                    if (buttonConfig.handler) {
                        buttonConfig.handler(item, row);
                    }
                });
            }
        });
    }
    
    /**
     * Default row template (for flat tables)
     */
    defaultRowTemplate(item, index) {
        return `
            <td class="checkbox-wrapper">
                <input type="checkbox" class="row-checkbox" data-id="${item[this.rowIdentifier]}">
            </td>
            <td>${item[this.rowIdentifier]}</td>
            <td>Data</td>
        `;
    }
    
    /**
     * Default parent row template (for hierarchical tables)
     */
    defaultParentRowTemplate(item, index) {
        const isExpanded = this.expandedRows.has(item[this.rowIdentifier]);
        return `
            <td class="checkbox-wrapper">
                <input type="checkbox" class="row-checkbox" data-id="${item[this.rowIdentifier]}">
            </td>
            <td>
                <button class="expand-btn ${isExpanded ? 'expanded' : ''}">${isExpanded ? '−' : '+'}</button>
            </td>
            <td>${item[this.rowIdentifier]}</td>
            <td>Parent Data</td>
        `;
    }
    
    /**
     * Default child row template (for hierarchical tables)
     */
    defaultChildRowTemplate(item, parentIndex, childIndex) {
        return `
            <td class="checkbox-wrapper">
                <input type="checkbox" class="row-checkbox" data-id="${item[this.rowIdentifier]}">
            </td>
            <td></td>
            <td>${item[this.rowIdentifier]}</td>
            <td>Child Data</td>
        `;
    }
    
    /**
     * Handle row selection
     */
    handleRowSelection(rowId, checked) {
        if (checked) {
            this.selectedRows.add(rowId);
        } else {
            this.selectedRows.delete(rowId);
        }
        
        this.onSelectionChange(this.getSelectedRows());
    }

    /**
     * Select or deselect all currently rendered rows (current page)
     */
    selectAll(checked) {
        if (!this.tableBody) return;
        const checkboxes = this.tableBody.querySelectorAll('.row-checkbox');
        checkboxes.forEach(cb => {
            cb.checked = checked;
            const row = cb.closest('tr');
            const rowId = row?.getAttribute('data-row-id');
            if (!rowId) return;
            if (checked) this.selectedRows.add(this.coerceId(rowId));
            else this.selectedRows.delete(this.coerceId(rowId));
        });
        this.onSelectionChange(this.getSelectedRows());
    }

    /**
     * Clear selection (all pages)
     */
    clearSelection() {
        this.selectedRows.clear();
        if (this.tableBody) {
            const checkboxes = this.tableBody.querySelectorAll('.row-checkbox');
            checkboxes.forEach(cb => (cb.checked = false));
        }
        this.onSelectionChange([]);
    }
    
    /**
     * Get selected row IDs
     */
    getSelectedRowIds() {
        return Array.from(this.selectedRows);
    }
    
    /**
     * Get selected rows data
     */
    getSelectedRows() {
        return this.getSelectedRowIds()
            .map(id => this.data.find(item => item[this.rowIdentifier] === id))
            .filter(row => row !== undefined);
    }

    /**
     * Get full data array (unfiltered)
     */
    getData() {
        return this.data;
    }

    /**
     * Find a row object by its identifier
     */
    getRowById(rowId) {
        const id = this.coerceId(rowId);
        return this.data.find(item => item && this.coerceId(item[this.rowIdentifier]) === id) || null;
    }

    /**
     * Update a single row (data + UI if present)
     */
    updateRow(rowId, updates) {
        const id = this.coerceId(rowId);
        const row = this.getRowById(id);
        if (!row) return false;

        Object.assign(row, updates || {});

        const rowEl = this.getRowElementById(id);
        if (rowEl) {
            this.onRowUpdate(rowEl, updates || {});
        }

        return true;
    }

    /**
     * Update multiple rows by IDs
     */
    updateRows(rowIds, updates) {
        if (!Array.isArray(rowIds)) return 0;
        let updated = 0;
        rowIds.forEach(id => {
            if (this.updateRow(id, updates)) updated += 1;
        });
        return updated;
    }

    /**
     * Remove rows by IDs (data + selection), then re-render
     */
    removeRows(rowIds) {
        if (!Array.isArray(rowIds) || rowIds.length === 0) return 0;
        const idSet = new Set(rowIds.map(id => this.coerceId(id)));

        const before = this.data.length;
        this.data = this.data.filter(item => !idSet.has(this.coerceId(item?.[this.rowIdentifier])));
        this.filteredData = this.filteredData.filter(item => !idSet.has(this.coerceId(item?.[this.rowIdentifier])));

        // Clear selection for removed rows
        idSet.forEach(id => this.selectedRows.delete(id));

        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.getPaginationDataLength());
        }

        this.render();
        return before - this.data.length;
    }

    /**
     * Add a new row to the table (append), then re-render
     */
    addRow(newRow) {
        if (!newRow) return false;
        this.data.push(newRow);
        this.filteredData.push(newRow);

        if (this.paginationComponent) {
            this.paginationComponent.updateDataLength(this.getPaginationDataLength());
        }

        this.render();
        return true;
    }

    /**
     * Get the DOM row element for an ID, if currently rendered
     */
    getRowElementById(rowId) {
        if (!this.tableBody) return null;
        const id = this.coerceId(rowId);
        return this.tableBody.querySelector(`tr[data-row-id="${CSS.escape(String(id))}"]`);
    }

    /**
     * Coerce IDs to a consistent type for Sets/comparisons.
     * Fabric Invoices uses numeric IDs, but DOM attributes are strings.
     */
    coerceId(id) {
        // Keep numbers as numbers when possible; otherwise use string
        if (id == null) return id;
        const n = Number(id);
        return Number.isFinite(n) && String(n) === String(id).trim() ? n : String(id);
    }
    
    /**
     * Toggle row expansion (for hierarchical tables)
     */
    toggleRowExpansion(rowId) {
        if (this.expandedRows.has(rowId)) {
            this.expandedRows.delete(rowId);
        } else {
            this.expandedRows.add(rowId);
        }
        
        // Re-render to show/hide children
        this.render();
    }
    
    /**
     * Sort table by column
     */
    sort(column, direction = null) {
        if (!this.sortableColumns.includes(column)) {
            return;
        }
        
        // Toggle direction if same column
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = direction || 'asc';
        }
        
        // Sort filtered data
        this.filteredData.sort((a, b) => {
            let aVal = this.getNestedValue(a, column);
            let bVal = this.getNestedValue(b, column);
            
            // Handle null/undefined
            if (aVal == null) aVal = '';
            if (bVal == null) bVal = '';
            
            // Compare
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.sortDirection === 'asc') {
                return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
            } else {
                return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
            }
        });
        
        // Reset to first page
        this.currentPage = 1;
        if (this.paginationComponent) {
            this.paginationComponent.reset();
        }
        
        this.render();
    }
    
    /**
     * Get nested value from object (e.g., 'customer.short_name')
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, prop) => current?.[prop], obj);
    }
    
    /**
     * Go to specific page
     */
    goToPage(page) {
        if (this.paginationComponent) {
            this.paginationComponent.goToPage(page);
        } else {
            const totalPages = Math.ceil(this.filteredData.length / this.itemsPerPage);
            if (page >= 1 && page <= totalPages) {
                this.currentPage = page;
                this.render();
            }
        }
    }
    
    /**
     * Get current page
     */
    getCurrentPage() {
        if (this.paginationComponent) {
            return this.paginationComponent.getCurrentPage();
        }
        return this.currentPage;
    }

    /**
     * For pagination: how many "top-level" items exist?
     * - Flat tables: total filtered rows
     * - Hierarchical tables: total parent rows
     */
    getPaginationDataLength() {
        if (this.serverSidePagination) return this.serverSideTotal;
        if (!this.hierarchical) return this.filteredData.length;
        return this.getParentRows(this.filteredData).length;
    }

    /**
     * Parent rows are rows with no parentKey (null/undefined/empty)
     */
    getParentRows(data) {
        const pk = this.parentKey;
        return (data || []).filter(item => item && (item[pk] == null || item[pk] === ''));
    }

    /**
     * Build a map: parentId -> [childRows]
     */
    buildChildMap(data) {
        const childMap = new Map();
        const pk = this.parentKey;
        (data || []).forEach(item => {
            if (!item) return;
            const parentId = item[pk];
            if (parentId == null || parentId === '') return;
            if (!childMap.has(parentId)) childMap.set(parentId, []);
            childMap.get(parentId).push(item);
        });
        return childMap;
    }
}
