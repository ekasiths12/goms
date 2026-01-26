/**
 * Filter Manager - Unified filter system with multi-select support
 * Handles all filter types: dropdown (with search), text, date, radio
 * Supports multi-select with tags/chips display
 * Auto-extracts options from data or accepts manual options
 */

class FilterManager {
    constructor(config) {
        this.containerId = config.containerId || 'filterControls';
        this.filters = config.filters || [];
        this.data = config.data || [];
        this.onFilterChange = config.onFilterChange || (() => {});
        this.debounceDelay = config.debounceDelay || 500;
        
        this.filterValues = {};
        this.filterTimer = null;
        this.container = null;
        
        // Initialize
        this.initialize();
    }
    
    /**
     * Initialize the filter manager
     */
    initialize() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`Filter container not found: ${this.containerId}`);
            return;
        }
        
        // Initialize filter values
        this.filters.forEach(filter => {
            if (filter.type === 'radio') {
                const defaultValue = filter.defaultValue || (filter.options && filter.options[0] ? (filter.options[0].value || filter.options[0]) : '');
                this.filterValues[filter.id] = defaultValue;
            } else if (filter.multiSelect) {
                this.filterValues[filter.id] = [];
            } else {
                this.filterValues[filter.id] = '';
            }
        });
        
        // Render filters
        this.render();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Apply initial filters if data exists
        if (this.data && this.data.length > 0) {
            this.applyFilters();
        }
        
        console.log('✅ FilterManager initialized');
    }
    
    /**
     * Render all filters
     */
    render() {
        if (!this.container) return;
        
        // Create filter controls structure
        const filterRow = document.createElement('div');
        filterRow.className = 'filter-row';
        
        this.filters.forEach(filter => {
            const filterGroup = this.createFilterGroup(filter);
            filterRow.appendChild(filterGroup);
        });
        
        // Clear existing content and add new
        this.container.innerHTML = '';
        this.container.appendChild(filterRow);
    }
    
    /**
     * Create a filter group element
     */
    createFilterGroup(filter) {
        const group = document.createElement('div');
        group.className = 'filter-group';
        group.dataset.filterId = filter.id;
        
        // Add label if provided
        if (filter.label) {
            const label = document.createElement('label');
            label.textContent = filter.label;
            group.appendChild(label);
        }
        
        // Create filter input based on type
        switch (filter.type) {
            case 'dropdown':
                group.appendChild(this.createDropdownFilter(filter));
                break;
            case 'text':
                group.appendChild(this.createTextFilter(filter));
                break;
            case 'date':
                group.appendChild(this.createDateFilter(filter));
                break;
            case 'radio':
                group.appendChild(this.createRadioFilter(filter));
                break;
        }
        
        return group;
    }
    
    /**
     * Create dropdown filter with search and multi-select
     */
    createDropdownFilter(filter) {
        const container = document.createElement('div');
        container.className = 'filter-container';
        
        // Main input
        const input = document.createElement('input');
        input.type = 'text';
        input.id = `filter_${filter.id}`;
        input.className = 'filter-select-enhanced';
        input.placeholder = filter.placeholder || `Select ${filter.label || filter.id}`;
        input.dataset.filterId = filter.id;
        input.dataset.multiSelect = filter.multiSelect ? 'true' : 'false';
        container.appendChild(input);
        
        // Selected items container (for multi-select tags)
        if (filter.multiSelect) {
            const selectedContainer = document.createElement('div');
            selectedContainer.className = 'selected-items';
            selectedContainer.id = `selected_${filter.id}`;
            container.appendChild(selectedContainer);
        }
        
        // Dropdown
        const dropdown = document.createElement('div');
        dropdown.id = `dropdown_${filter.id}`;
        dropdown.className = 'filter-dropdown';
        
        // Search input
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'filter-input-search';
        searchInput.placeholder = 'Type to search...';
        dropdown.appendChild(searchInput);
        
        // Options container
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'filter-options';
        dropdown.appendChild(optionsContainer);
        
        container.appendChild(dropdown);
        
        return container;
    }
    
    /**
     * Create text filter
     */
    createTextFilter(filter) {
        const input = document.createElement('input');
        input.type = 'text';
        input.id = `filter_${filter.id}`;
        input.className = 'filter-input';
        input.placeholder = filter.placeholder || `Enter ${filter.label || filter.id}`;
        input.dataset.filterId = filter.id;
        return input;
    }
    
    /**
     * Create date filter with auto-formatting
     */
    createDateFilter(filter) {
        const input = document.createElement('input');
        input.type = 'text';
        input.id = `filter_${filter.id}`;
        input.className = 'filter-input';
        input.placeholder = filter.placeholder || 'DD/MM/YY';
        input.dataset.filterId = filter.id;
        input.dataset.filterType = 'date';
        return input;
    }
    
    /**
     * Create radio button filter
     */
    createRadioFilter(filter) {
        const radioGroup = document.createElement('div');
        radioGroup.className = 'radio-group';
        
        filter.options.forEach((option, index) => {
            const radioOption = document.createElement('div');
            radioOption.className = 'radio-option';
            
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.id = `radio_${filter.id}_${index}`;
            radio.name = `radio_${filter.id}`;
            radio.value = option.value || option;
            radio.checked = (option.value || option) === (filter.defaultValue || filter.options[0]);
            radio.dataset.filterId = filter.id;
            
            const label = document.createElement('label');
            label.htmlFor = `radio_${filter.id}_${index}`;
            label.textContent = option.label || option;
            
            radioOption.appendChild(radio);
            radioOption.appendChild(label);
            radioGroup.appendChild(radioOption);
        });
        
        return radioGroup;
    }
    
    /**
     * Setup event listeners for all filters
     */
    setupEventListeners() {
        this.filters.forEach(filter => {
            switch (filter.type) {
                case 'dropdown':
                    this.setupDropdownListeners(filter);
                    break;
                case 'text':
                    this.setupTextListeners(filter);
                    break;
                case 'date':
                    this.setupDateListeners(filter);
                    break;
                case 'radio':
                    this.setupRadioListeners(filter);
                    break;
            }
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.filter-container')) {
                this.closeAllDropdowns();
            }
        });
    }
    
    /**
     * Setup dropdown filter listeners
     */
    setupDropdownListeners(filter) {
        const input = document.getElementById(`filter_${filter.id}`);
        const dropdown = document.getElementById(`dropdown_${filter.id}`);
        const searchInput = dropdown.querySelector('.filter-input-search');
        const optionsContainer = dropdown.querySelector('.filter-options');
        const isMultiSelect = filter.multiSelect === true;
        
        // Toggle dropdown on input click
        input.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeAllDropdowns();
            dropdown.classList.add('show');
            this.populateDropdownOptions(filter, '');
            if (searchInput) searchInput.value = '';
        });
        
        // Handle direct typing in main input (for single-select)
        if (!isMultiSelect) {
            input.addEventListener('input', (e) => {
                this.filterValues[filter.id] = e.target.value;
                input.dataset.selectedValue = '';
                this.triggerFilterUpdate();
            });
        }
        
        // Handle search input
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const searchTerm = e.target.value.toLowerCase();
                this.populateDropdownOptions(filter, searchTerm);
            });
            
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    const firstOption = optionsContainer.querySelector('.filter-option:not(.empty)');
                    if (firstOption) firstOption.click();
                } else if (e.key === 'Escape') {
                    dropdown.classList.remove('show');
                }
            });
        }
        
        // Handle option selection - click anywhere on the option
        if (optionsContainer) {
            optionsContainer.addEventListener('click', (e) => {
                const option = e.target.closest('.filter-option');
                if (!option || option.classList.contains('empty')) return;
                
                const value = option.dataset.value;
                // Get text from span or option itself
                const textSpan = option.querySelector('span');
                const text = textSpan ? textSpan.textContent.trim() : option.textContent.trim();
                
                if (isMultiSelect) {
                    this.toggleMultiSelectValue(filter, value, text);
                    // Refresh dropdown to show updated selection state
                    const currentSearch = searchInput ? searchInput.value : '';
                    this.populateDropdownOptions(filter, currentSearch);
                } else {
                    this.setSingleSelectValue(filter, value, text);
                    dropdown.classList.remove('show');
                }
                
                this.triggerFilterUpdate();
            });
        }
    }
    
    /**
     * Setup text filter listeners
     */
    setupTextListeners(filter) {
        const input = document.getElementById(`filter_${filter.id}`);
        if (!input) return;
        
        input.addEventListener('input', () => {
            this.filterValues[filter.id] = input.value;
            this.triggerFilterUpdate();
        });
    }
    
    /**
     * Setup date filter listeners
     */
    setupDateListeners(filter) {
        const input = document.getElementById(`filter_${filter.id}`);
        if (!input) return;
        
        // Auto-format date input
        input.addEventListener('input', () => {
            if (typeof formatDateInput === 'function') {
                formatDateInput(input);
            }
            this.filterValues[filter.id] = input.value;
            this.triggerFilterUpdate();
        });
    }
    
    /**
     * Setup radio filter listeners
     */
    setupRadioListeners(filter) {
        const radios = document.querySelectorAll(`input[name="radio_${filter.id}"]`);
        radios.forEach(radio => {
            radio.addEventListener('change', () => {
                if (radio.checked) {
                    this.filterValues[filter.id] = radio.value;
                    this.triggerFilterUpdate();
                }
            });
        });
    }
    
    /**
     * Populate dropdown options
     */
    populateDropdownOptions(filter, searchTerm = '') {
        const dropdown = document.getElementById(`dropdown_${filter.id}`);
        const optionsContainer = dropdown.querySelector('.filter-options');
        if (!optionsContainer) return;
        
        // Get options
        let options = this.getFilterOptions(filter);
        
        // Filter by search term
        if (searchTerm) {
            options = options.filter(opt => 
                opt.toLowerCase().includes(searchTerm)
            );
        }
        
        // Clear existing options
        optionsContainer.innerHTML = '';
        
        // Add options
        if (options.length === 0) {
            const emptyOption = document.createElement('div');
            emptyOption.className = 'filter-option empty';
            emptyOption.textContent = 'No matches found';
            optionsContainer.appendChild(emptyOption);
        } else {
            const isMultiSelect = filter.multiSelect === true;
            const selectedValues = isMultiSelect 
                ? (this.filterValues[filter.id] || [])
                : [this.filterValues[filter.id]];
            
            options.forEach(option => {
                const optionElement = document.createElement('div');
                optionElement.className = 'filter-option';
                optionElement.dataset.value = option;
                
                // No checkboxes - use color highlighting instead
                const text = document.createElement('span');
                text.textContent = option;
                optionElement.appendChild(text);
                
                // Highlight selected options with color
                if (selectedValues.includes(option)) {
                    optionElement.classList.add('selected');
                }
                
                optionsContainer.appendChild(optionElement);
            });
        }
    }
    
    /**
     * Get filter options (auto-extract or manual)
     */
    getFilterOptions(filter) {
        // If manual options provided, use them
        if (filter.options && Array.isArray(filter.options)) {
            return filter.options.map(opt => opt.value || opt);
        }
        
        // Auto-extract from data using customExtract function
        if (filter.customExtract && typeof filter.customExtract === 'function' && this.data.length > 0) {
            const uniqueValues = new Set();
            this.data.forEach(item => {
                const values = filter.customExtract(item);
                if (Array.isArray(values)) {
                    values.forEach(val => {
                        if (val !== null && val !== undefined && val !== '') {
                            uniqueValues.add(String(val));
                        }
                    });
                } else if (values !== null && values !== undefined && values !== '') {
                    uniqueValues.add(String(values));
                }
            });
            return Array.from(uniqueValues).sort();
        }
        
        // Otherwise, auto-extract from data using dataKey
        if (filter.dataKey && this.data.length > 0) {
            const uniqueValues = new Set();
            this.data.forEach(item => {
                const value = this.getNestedValue(item, filter.dataKey);
                if (value !== null && value !== undefined && value !== '') {
                    uniqueValues.add(String(value));
                }
            });
            return Array.from(uniqueValues).sort();
        }
        
        return [];
    }
    
    /**
     * Get nested value from object using dot notation
     */
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => {
            return current && current[key] !== undefined ? current[key] : null;
        }, obj);
    }
    
    /**
     * Toggle multi-select value
     */
    toggleMultiSelectValue(filter, value, text) {
        const currentValues = this.filterValues[filter.id] || [];
        const index = currentValues.indexOf(value);
        
        if (index > -1) {
            // Remove value
            currentValues.splice(index, 1);
        } else {
            // Add value
            currentValues.push(value);
        }
        
        this.filterValues[filter.id] = currentValues;
        this.updateMultiSelectDisplay(filter);
        
        // Update dropdown to reflect selection state
        const dropdown = document.getElementById(`dropdown_${filter.id}`);
        if (dropdown) {
            const option = dropdown.querySelector(`[data-value="${value}"]`);
            if (option) {
                if (index > -1) {
                    option.classList.remove('selected');
                } else {
                    option.classList.add('selected');
                }
            }
        }
    }
    
    /**
     * Set single-select value
     */
    setSingleSelectValue(filter, value, text) {
        this.filterValues[filter.id] = value;
        const input = document.getElementById(`filter_${filter.id}`);
        if (input) {
            input.value = text;
            input.dataset.selectedValue = value;
        }
    }
    
    /**
     * Update multi-select display (tags/chips)
     */
    updateMultiSelectDisplay(filter) {
        const input = document.getElementById(`filter_${filter.id}`);
        const selectedContainer = document.getElementById(`selected_${filter.id}`);
        const selectedValues = this.filterValues[filter.id] || [];
        
        if (!input || !selectedContainer) return;
        
        // Update input placeholder/text
        if (selectedValues.length === 0) {
            input.value = '';
            input.placeholder = filter.placeholder || `Select ${filter.label || filter.id}`;
        } else {
            input.value = `${selectedValues.length} selected`;
        }
        
        // Update tags
        selectedContainer.innerHTML = '';
        selectedValues.forEach(value => {
            const tag = document.createElement('div');
            tag.className = 'selected-item';
            tag.textContent = value;
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-btn';
            removeBtn.textContent = '×';
            removeBtn.onclick = () => {
                this.toggleMultiSelectValue(filter, value, value);
                this.triggerFilterUpdate();
            };
            
            tag.appendChild(removeBtn);
            selectedContainer.appendChild(tag);
        });
    }
    
    /**
     * Close all dropdowns
     */
    closeAllDropdowns() {
        document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
    
    /**
     * Trigger filter update (debounced)
     */
    triggerFilterUpdate() {
        if (this.filterTimer) {
            clearTimeout(this.filterTimer);
        }
        
        this.filterTimer = setTimeout(() => {
            this.applyFilters();
        }, this.debounceDelay);
    }
    
    /**
     * Apply filters to data
     */
    applyFilters() {
        const filtered = this.data.filter(item => {
            return this.filters.every(filter => {
                return this.matchesFilter(item, filter);
            });
        });
        
        this.onFilterChange(filtered, this.filterValues);
    }
    
    /**
     * Check if item matches a filter
     */
    matchesFilter(item, filter) {
        const filterValue = this.filterValues[filter.id];
        
        // Empty filter = match all
        if (!filterValue || 
            (Array.isArray(filterValue) && filterValue.length === 0) ||
            (typeof filterValue === 'string' && filterValue.trim() === '')) {
            return true;
        }
        
        // Custom filter function takes precedence
        if (filter.customFilter && typeof filter.customFilter === 'function') {
            return filter.customFilter(item, filterValue, this.filterValues);
        }
        
        const itemValue = this.getNestedValue(item, filter.dataKey || filter.id);
        const itemValueStr = String(itemValue || '').toLowerCase();
        
        switch (filter.type) {
            case 'dropdown':
                if (filter.multiSelect) {
                    // Multi-select: item value must be in selected array
                    return filterValue.includes(String(itemValue));
                } else {
                    // Single-select: exact match or contains
                    return itemValueStr.includes(String(filterValue).toLowerCase());
                }
                
            case 'text':
                return itemValueStr.includes(String(filterValue).toLowerCase());
                
            case 'date':
                if (!filterValue || filterValue.length !== 8) return true;
                const date = new Date(itemValue);
                if (isNaN(date.getTime())) return true;
                
                if (filter.rangeType === 'from') {
                    return isDateInRange(date, filterValue, 'from');
                } else if (filter.rangeType === 'to') {
                    return isDateInRange(date, filterValue, 'to');
                }
                return true;
                
            case 'radio':
                return String(itemValue) === String(filterValue);
                
            default:
                return true;
        }
    }
    
    /**
     * Get current filter values
     */
    getFilterValues() {
        return { ...this.filterValues };
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        this.filters.forEach(filter => {
            if (filter.type === 'radio') {
                const defaultValue = filter.defaultValue || (filter.options && filter.options[0] ? (filter.options[0].value || filter.options[0]) : '');
                this.filterValues[filter.id] = defaultValue;
                // Uncheck all radios
                document.querySelectorAll(`input[name="radio_${filter.id}"]`).forEach(radio => {
                    radio.checked = false;
                });
                // Check the default radio
                const defaultRadio = document.querySelector(`input[name="radio_${filter.id}"][value="${defaultValue}"]`);
                if (defaultRadio) {
                    defaultRadio.checked = true;
                } else {
                    // Fallback: check first radio
                    const firstRadio = document.querySelector(`input[name="radio_${filter.id}"]`);
                    if (firstRadio) {
                        firstRadio.checked = true;
                        this.filterValues[filter.id] = firstRadio.value;
                    }
                }
            } else if (filter.multiSelect) {
                this.filterValues[filter.id] = [];
                this.updateMultiSelectDisplay(filter);
            } else {
                this.filterValues[filter.id] = '';
                const input = document.getElementById(`filter_${filter.id}`);
                if (input) {
                    input.value = '';
                    input.dataset.selectedValue = '';
                }
            }
        });
        
        this.closeAllDropdowns();
        this.triggerFilterUpdate();
    }
    
    /**
     * Update data and refresh options
     */
    updateData(newData) {
        this.data = newData || [];
        
        // Refresh dropdown options for filters that auto-extract
        this.filters.forEach(filter => {
            if (filter.type === 'dropdown' && !filter.options) {
                // Options will be refreshed when dropdown is opened
            }
        });
        
        // Re-apply filters with new data
        this.applyFilters();
    }
    
    /**
     * Destroy filter manager
     */
    destroy() {
        if (this.filterTimer) {
            clearTimeout(this.filterTimer);
        }
        this.filters = [];
        this.data = [];
        this.filterValues = {};
        console.log('🗑️ FilterManager destroyed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FilterManager;
}
