# Frontend Code Refactoring - Common Components

## Executive Summary

This document addresses the massive code duplication in frontend HTML files. Analysis shows **~11,000+ lines of duplicated code** across themes, tables, sorting, filters, and common behaviors that should be extracted into reusable components.

**Status**: Phase 1 (CSS Extraction), Navigation Bar refactoring, and JavaScript Utilities (Functions #1-2) completed. Remaining work focuses on additional JavaScript utilities, filters, pagination, and table management.

---

## ✅ Completed Work

### Phase 1: CSS Extraction (COMPLETED)
- ✅ Created `frontend/css/common.css` with theme variables, base styles, and navigation styles
- ✅ Updated all HTML pages to use `common.css`
- ✅ Removed ~160 lines of duplicated CSS from each page
- ✅ Version indicator system implemented (GOMSv2.003)

### Navigation Bar Refactoring (COMPLETED)
- ✅ Created `frontend/js/common/nav-bar.js` to render navigation bar dynamically
- ✅ Removed duplicated navigation HTML from all pages (~20 lines per page)
- ✅ Version indicator centralized in `nav-bar.js`
- ✅ All pages now use `renderNavBar()` function

### JavaScript Utilities - Function #1: Theme Management (COMPLETED)
- ✅ Created `frontend/js/common/utils.js` with `GOMS.theme.toggle()` and `GOMS.theme.load()`
- ✅ Removed duplicate `toggleTheme()` and `loadTheme()` functions from all 6 pages (~50 lines per page)
- ✅ Added `utils.js` to all pages in `<head>` section
- ✅ Special handling for dashboard to preserve chart color updates
- ✅ Version updated to GOMSv2.004

### JavaScript Utilities - Function #2: Formatting Utilities (COMPLETED)
- ✅ Added `GOMS.format.date()`, `GOMS.format.number()`, `GOMS.format.integer()`, and `GOMS.format.dateInput()` to `utils.js`
- ✅ Removed duplicate formatting functions from all relevant pages (~60 lines per page)
- ✅ Fixed script loading order (moved scripts to `<head>` section)
- ✅ All functions exposed as global shortcuts for backward compatibility
- ✅ Version updated to GOMSv2.006

---

## 1. JavaScript Function Duplication

### Issue
**13+ common functions duplicated across all pages**

| Function | Instances | Lines Saved | Status |
|----------|-----------|-------------|--------|
| `toggleTheme()` | 6 | ~30 lines each | ✅ Completed (Function #1) |
| `loadTheme()` | 6 | ~20 lines each | ✅ Completed (Function #1) |
| `formatDate()` | 5 | ~15 lines each | ✅ Completed (Function #2) |
| `formatNumber()` | 5 | ~10 lines each | ✅ Completed (Function #2) |
| `formatDateInput()` | 4 | ~25 lines each | ✅ Completed (Function #2) |
| `formatInteger()` | 3 | ~8 lines each | ✅ Completed (Function #2) |
| `getApiBaseUrl()` | 5 | ~40 lines each | ⏳ Pending (Function #3) |
| `checkAuth()` | 5 | ~10 lines each | ⏳ Pending (Function #4) |
| `logout()` | 5 | ~5 lines each | ⏳ Pending (Function #4) |
| `goToPage()` | 4 | ~10 lines each | ⏳ Pending (Function #6) |
| `updatePaginationControls()` | 4 | ~50 lines each | ⏳ Pending (Function #6) |
| `getTotalPages()` | 4 | ~5 lines each | ⏳ Pending (Function #6) |
| `isDateInRange()` | 2 | ~20 lines each | ⏳ Pending (Function #5) |

**Total**: ~250-300 lines duplicated per file

### Solution

**Create `frontend/js/common/utils.js`**:
```javascript
/**
 * GOMS Common Utilities
 * Shared functions used across all pages
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
                html.removeAttribute('data-theme');
                localStorage.setItem('theme', 'dark');
                themeIcon.textContent = '🌙';
                themeText.textContent = 'Dark';
            } else {
                html.setAttribute('data-theme', 'light');
                localStorage.setItem('theme', 'light');
                themeIcon.textContent = '☀️';
                themeText.textContent = 'Light';
            }
            
            // Update charts if they exist
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
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = String(date.getFullYear()).slice(-2);
                return `${day}/${month}/${year}`;
            } catch (error) {
                return dateString;
            }
        },
        
        number: function(num) {
            if (num === null || num === undefined || isNaN(num)) return '0.00';
            return parseFloat(num).toFixed(2);
        },
        
        integer: function(num) {
            if (num === null || num === undefined || isNaN(num)) return '0';
            return parseInt(num).toString();
        },
        
        currency: function(amount) {
            if (amount === null || amount === undefined) return '0.00';
            return parseFloat(amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        },
        
        dateInput: function(input) {
            // Auto-format date input to DD/MM/YY format
            let text = input.value;
            let digitsOnly = text.replace(/\D/g, '');
            
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
            
            // Local development
            if (hostname === 'localhost' || hostname === '127.0.0.1') {
                if (port === '3000' || port === '5000') {
                    return 'http://localhost:8000';
                }
                return 'http://localhost:8000';
            }
            
            // Railway deployment
            if (hostname.includes('railway.app') || hostname.includes('up.railway.app')) {
                return `https://${hostname}`;
            }
            
            // Other deployments
            const origin = window.location.origin;
            if (protocol === 'https:') {
                return origin;
            } else {
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
```

**Update HTML files**:
```html
<script src="js/common/utils.js"></script>
<script>
    // Page-specific code only
    // Remove all duplicated functions
</script>
```

**Impact**: Reduces each HTML file by ~250-300 lines

---

## 2. Filter Behavior Duplication

### Issue
Filter setup and behavior duplicated across pages:
- Event listener setup
- Filter clearing
- Date input formatting
- Filter application logic

### Solution

**Create `frontend/js/common/filter-manager.js`** with multi-select support (see Section 11.7 for full implementation).

**Impact**: Reduces each page by ~100-150 lines

---

## 3. Pagination Duplication

### Issue
Pagination HTML and JavaScript duplicated:
- Pagination HTML structure
- `goToPage()`, `updatePaginationControls()`, `getTotalPages()` functions

### Solution

**Create `frontend/js/common/pagination.js`** (see Section 4 in original document for full implementation).

**Impact**: Reduces each page by ~80-100 lines

---

## 4. Page Initialization Pattern

### Issue
Similar initialization pattern duplicated:
- Theme loading
- Auth checking
- Data loading
- Filter setup
- Table initialization

### Solution

**Create `frontend/js/common/page-initializer.js`** (see Section 6 in original document for full implementation).

**Impact**: Reduces each page by ~50-80 lines

---

## 5. Table Structure Analysis & Refactoring Strategy

### Detailed Table Structure Comparison

After careful inspection of all main pages, here's the comprehensive breakdown:

#### 5.1 Fabric Invoices (`fabric-invoices.html`)
- **Structure**: Flat table (no nesting)
- **Layers**: 1 level (single row per invoice line)
- **Expand/Collapse**: None
- **Row Classes**: Standard `data-table` rows
- **Selection**: Checkbox-based row selection
- **Implementation**: Uses `TableManager` class from `table-manager.js`
- **Special Features**: 
  - Enhanced filter dropdowns with search
  - Bulk actions (assign location, tax invoice, commission sale)
  - Inline editing capabilities

#### 5.2 Stitching Records (`stitching-records.html`)
- **Structure**: 2-level hierarchy (parent-child)
- **Layers**: 
  - Level 1: Parent rows (stitching records) - `treeview-parent`
  - Level 2: Child rows (multi-fabrics and lining) - `treeview-child`
- **Expand/Collapse**: 
  - Function: `toggleRecordExpansion(recordId)`
  - Indicator: `expand-indicator` (▶/▼)
  - Child rows hidden by default (`display: none`)
- **Row Classes**: 
  - `treeview-parent` for main records
  - `treeview-child` for fabric/lining details
- **Selection**: Checkbox-based, tracks by index
- **Implementation**: Custom treeview rendering
- **Special Features**:
  - Multi-fabric support (garment_fabrics)
  - Lining fabric support (lining_fabrics)
  - Expandable only if has multi-fabrics or lining

#### 5.3 Packing Lists (`packing-lists.html`)
- **Structure**: 3-level hierarchy
- **Layers**:
  - Level 1: Parent rows (packing list summary) - `parent-row`
  - Level 2: Child rows (stitching records) - `child-row`
  - Level 3: Secondary fabric rows - `secondary-fabric-row`
  - Level 3: Lining fabric rows - `lining-fabric-row`
- **Expand/Collapse**:
  - Function: `toggleExpansion(packingListId)`
  - Indicator: `expand-indicator` (▶/▼)
  - Child rows use `.expanded` class (hidden by default)
- **Row Classes**:
  - `parent-row` for packing list summaries
  - `child-row` for stitching record lines
  - `secondary-fabric-row` for additional fabrics
  - `lining-fabric-row` for lining fabrics
- **Selection**: Checkbox-based by packing list ID
- **Implementation**: Custom HTML string building
- **Special Features**:
  - Filters child rows (stitching records) within parent
  - Billing status filter (billed/unbilled)
  - Client-side filtering (filters loaded data in memory)

#### 5.4 Group Bills (`group-bills.html`)
- **Structure**: 4-level hierarchy (most complex)
- **Layers**:
  - Level 1: Parent rows (group bill summary) - `parent-row group-bill-row`
  - Level 2: Child rows (Fabric Invoice Summary, Stitching Invoice Summary) - `child-row`
  - Level 3: Detail rows (fabric details, stitching details) - `detail-row`, `sub-child-row`
  - Level 4: Secondary fabric rows - `secondary-fabric-row`
  - Level 4: Lining fabric rows - `lining-fabric-row`
- **Expand/Collapse**:
  - Multiple functions:
    - `toggleGroupExpansion(groupId)` - expands/collapses all child rows
    - `toggleFabricExpansion(groupId)` - expands/collapses fabric details
    - `toggleStitchingExpansion(groupId)` - expands/collapses stitching details
  - Indicators: `expand-indicator` (▶/▼)
  - Child rows hidden by default (`display: none`)
- **Row Classes**:
  - `parent-row group-bill-row` for group bill summaries
  - `child-row fabric-summary-row` for fabric invoice summaries
  - `child-row stitching-summary-row` for stitching invoice summaries
  - `detail-row fabric-detail-row` for fabric invoice details
  - `detail-row stitching-detail-row` for stitching invoice details
  - `detail-row secondary-fabric-row` for secondary fabrics
  - `detail-row lining-fabric-row` for lining fabrics
- **Selection**: Checkbox-based by group ID
- **Implementation**: Custom DOM element creation
- **Special Features**:
  - Can toggle between group bills and commission sales (flat table)
  - Commission sales mode: Simple flat table, no nesting
  - Multiple expand levels (group → fabric/stitching → details → secondary/lining)

### 5.5 Filter Implementation Comparison

#### Fabric Invoices
- **Type**: Server-side filtering (via API)
- **Method**: Enhanced dropdowns with search functionality
- **Filters**: 
  - Customer (enhanced dropdown)
  - Fabric Invoice (enhanced dropdown)
  - Tax Invoice (enhanced dropdown)
  - Item Code (enhanced dropdown)
  - Delivery Note (enhanced dropdown)
  - Location (enhanced dropdown)
  - Date From/To (text input with auto-format)
  - Stock Status (radio buttons: inStock/noStock)
- **Implementation**: `initializeEnhancedFilters()`, `applyFilters()` calls API
- **Special**: Auto-populates dropdown options from loaded data

#### Stitching Records
- **Type**: Server-side filtering (via API)
- **Method**: Simple text inputs
- **Filters**:
  - PL Number (text input)
  - Serial Number (text input)
  - Fabric Name (text input)
  - Customer (text input)
  - Date From/To (text input with auto-format)
  - Delivery Status (radio buttons: all/delivered/undelivered)
- **Implementation**: `loadStitchingData()` builds query params
- **Special**: Default filter set to "undelivered"

#### Packing Lists
- **Type**: Client-side filtering (filters loaded data in memory)
- **Method**: Simple text inputs
- **Filters**:
  - PL# (text input)
  - Serial# (text input)
  - Fabric (text input)
  - Customer (text input)
  - Tax Inv# (text input)
  - Fabric Inv (text input)
  - Fabric DN (text input)
  - Date From/To (text input)
  - Billing Status (radio buttons: all/billed/unbilled)
- **Implementation**: `filterData()` filters `packingListData` array
- **Special**: Filters both parent and child rows (checks if any line matches)

#### Group Bills
- **Type**: Server-side filtering (via API)
- **Method**: Simple text inputs
- **Filters**:
  - Customer (text input)
  - Group Number (text input)
  - Date From/To (text input with auto-format)
- **Implementation**: `loadGroupBillsData()` builds query params
- **Special**: Can toggle between group bills and commission sales views

### 5.6 Refactoring Strategy for Tables

#### Create Hierarchical Table Manager

**Create `frontend/js/common/hierarchical-table-manager.js`** (see Section 11.6 in original document for full implementation).

#### Page-Specific Table Configurations

- **Stitching Records** (2-level): `StitchingTableManager` extends `HierarchicalTableManager`
- **Packing Lists** (3-level): `PackingListTableManager` extends `HierarchicalTableManager`
- **Group Bills** (4-level): `GroupBillTableManager` extends `HierarchicalTableManager`
- **Fabric Invoices**: Keep using existing `TableManager` (flat table)

### 5.7 Refactoring Strategy for Filters

#### Unified Filter Manager with Standardized Behavior and Multi-Select

**IMPORTANT**: All filters will work the same way across all pages with:
- **Standardized UI**: Enhanced dropdowns with search (like Fabric Invoices)
- **Multi-select capability**: Users can select multiple values for each filter
- **Unified behavior**: Same interaction pattern on all pages
- **Client-side filtering**: All pages will filter loaded data in memory (for consistency)

**Create `frontend/js/common/filter-manager.js`** (see Section 11.7 in original document for full implementation with multi-select support).

### 5.8 Migration Plan for Tables

1. **Phase 1**: Create `HierarchicalTableManager` base class
2. **Phase 2**: Create page-specific subclasses:
   - `StitchingTableManager` (2-level)
   - `PackingListTableManager` (3-level)
   - `GroupBillTableManager` (4-level)
3. **Phase 3**: Migrate one page at a time:
   - Start with Stitching Records (simplest hierarchy)
   - Then Packing Lists
   - Finally Group Bills (most complex)
4. **Phase 4**: Keep Fabric Invoices using existing `TableManager` (flat table)

### 5.9 Migration Plan for Filters

**IMPORTANT**: All pages will use the same standardized filter system with multi-select.

1. **Phase 1**: Create unified `FilterManager` with multi-select support
2. **Phase 2**: Convert all pages to use enhanced dropdowns with multi-select:
   - **Fabric Invoices**: Already has enhanced dropdowns - add multi-select
   - **Stitching Records**: Convert text inputs to enhanced dropdowns with multi-select
   - **Packing Lists**: Convert text inputs to enhanced dropdowns with multi-select
   - **Group Bills**: Convert text inputs to enhanced dropdowns with multi-select
3. **Phase 3**: Standardize filter configurations:
   - All filters use the same UI pattern
   - All filters support multi-select
   - All filters have search functionality
   - Date filters remain as text inputs (with auto-format)
   - Radio button filters remain as radio buttons

---

## 6. Implementation Checklist

### ✅ Phase 1: Extract CSS (COMPLETED)
- [x] Create `frontend/css/common.css`
- [x] Move all theme CSS variables
- [x] Move navigation styles
- [x] Update all HTML files to include `common.css`
- [x] Remove duplicated CSS from HTML files
- [x] Test all pages for styling issues

### ✅ Phase 1.5: Navigation Bar (COMPLETED)
- [x] Create `frontend/js/common/nav-bar.js`
- [x] Update all HTML pages to use nav-bar.js
- [x] Remove duplicated navigation HTML
- [x] Test navigation bar on all pages

### Phase 2: Extract JavaScript Utilities (IN PROGRESS)
- [x] Create `frontend/js/common/utils.js`
- [x] Move theme functions (Function #1: ✅ COMPLETED)
- [x] Move formatting functions (Function #2: ✅ COMPLETED)
- [ ] Move API utilities (Function #3: getApiBaseUrl)
- [ ] Move auth utilities (Function #4: checkAuth, logout)
- [ ] Move date utilities (Function #5: isDateInRange, parseDDMMYY, formatForAPI)
- [x] Update all HTML files to include `utils.js`
- [x] Remove duplicated theme and formatting functions from HTML files
- [x] Test all pages for functionality (Functions #1-2)

### Phase 3: Create Components (PENDING)
- [ ] Create `frontend/js/common/filter-manager.js` with multi-select
- [ ] Create `frontend/js/common/pagination.js`
- [ ] Create `frontend/js/common/page-initializer.js`
- [ ] Create `frontend/js/common/hierarchical-table-manager.js`
- [ ] Refactor one page as proof of concept
- [ ] Test thoroughly
- [ ] Refactor remaining pages one by one

### Phase 4: Standardize Filters (PENDING)
- [ ] Convert all pages to use enhanced dropdowns with multi-select
- [ ] Standardize filter configurations
- [ ] Ensure all filters support multi-select
- [ ] Test filter behavior on all pages

### Phase 5: Cleanup (PENDING)
- [ ] Remove all remaining duplicated code
- [ ] Ensure all pages use common components
- [ ] Update documentation
- [ ] Final testing

---

## 7. Expected Results

### Before Refactoring
- `fabric-invoices.html`: 4953 lines
- `stitching-records.html`: 2540 lines
- `packing-lists.html`: 2078 lines
- `group-bills.html`: 2376 lines
- `dashboard.html`: 2172+ lines
- **Total**: ~14,000 lines (with massive duplication)

### After Refactoring (Target)
- `fabric-invoices.html`: ~600 lines (88% reduction)
- `stitching-records.html`: ~500 lines (80% reduction)
- `packing-lists.html`: ~500 lines (76% reduction)
- `group-bills.html`: ~600 lines (75% reduction)
- `dashboard.html`: ~800 lines (63% reduction)
- **Total**: ~3,000 lines

### New Common Files
- `css/common.css`: ~173 lines (✅ Created)
- `js/common/nav-bar.js`: ~47 lines (✅ Created)
- `js/common/utils.js`: ~128 lines (✅ Partially Created - Functions #1-2 completed, Functions #3-5 pending)
- `js/common/filter-manager.js`: ~400 lines (Pending - with multi-select)
- `js/common/pagination.js`: ~150 lines (Pending)
- `js/common/hierarchical-table-manager.js`: ~200 lines (Pending)
- `js/common/page-initializer.js`: ~100 lines (Pending)
- **Total**: ~1,370 lines

### Net Result
- **Before**: ~14,000 lines (duplicated)
- **After**: ~4,370 lines (no duplication)
- **Reduction**: 69% code reduction
- **Maintainability**: Significantly improved
- **Consistency**: All pages use same components

---

## 8. Benefits

1. **Single Source of Truth**: Theme, styles, and behaviors defined once
2. **Easier Maintenance**: Fix bugs in one place, affects all pages
3. **Consistency**: All pages behave the same way
4. **Faster Development**: New pages can reuse components
5. **Smaller File Sizes**: Reduced HTML file sizes improve load times
6. **Better Performance**: Shared CSS/JS files can be cached
7. **Multi-Select Filters**: Enhanced user experience with multi-select capability

---

## 9. Migration Strategy

1. **Start with one page** (e.g., `packing-lists.html`) as proof of concept
2. **Extract JavaScript utilities** - test thoroughly
3. **Create components** - refactor one page completely
4. **Apply to other pages** - one at a time
5. **Test each migration** - don't break existing functionality

---

## Notes

- Keep old code commented during migration for easy rollback
- Test each page after refactoring
- Update browser cache if needed
- Document any page-specific customizations
- **Table hierarchies are complex** - test expand/collapse thoroughly
- **All filters will work the same way** - standardized enhanced dropdowns with multi-select
- **Multi-select is required** - users must be able to select multiple values for each filter
- **Client-side filtering** - all pages filter loaded data in memory for consistency
- **Filter options auto-populate** - from the loaded data, no need for separate API calls
