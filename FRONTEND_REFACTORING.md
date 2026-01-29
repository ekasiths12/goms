# Frontend Code Refactoring - Common Components

## Executive Summary

This document addresses the massive code duplication in frontend HTML files. Analysis shows **~11,000+ lines of duplicated code** across themes, tables, sorting, filters, and common behaviors that should be extracted into reusable components.

**Status**: Phase 1 (CSS Extraction), Navigation Bar refactoring, JavaScript Utilities (Functions #1-6), Filter Manager component completed, all filter migrations completed (Fabric Invoices, Packing Lists, Stitching Records, Group Bills, and Dashboard), and pagination refactoring completed (all pages now use PaginationComponent and PageInitializer). Remaining work focuses on hierarchical table management.

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

### JavaScript Utilities - Function #3: API Utilities (COMPLETED)
- ✅ Added `GOMS.api.getBaseUrl()` to `utils.js`
- ✅ Removed duplicate `getApiBaseUrl()` functions from all 5 pages (~40 lines per page)
- ✅ Handles localhost (ports 3000, 5000, default 8000), Railway deployment (HTTPS), and other deployments
- ✅ Function exposed as global shortcut `window.getApiBaseUrl`
- ✅ Version updated to GOMSv2.008

### JavaScript Utilities - Function #4: Authentication Utilities (COMPLETED)
- ✅ Added `GOMS.auth.check()`, `GOMS.auth.logout()`, and `GOMS.auth.getUsername()` to `utils.js`
- ✅ Removed duplicate `checkAuth()` and `logout()` functions from all 5 pages (~15 lines per page)
- ✅ All functions exposed as global shortcuts for backward compatibility
- ✅ Version updated to GOMSv2.007

### JavaScript Utilities - Function #5: Date Utilities (COMPLETED)
- ✅ Added `GOMS.date.isInRange()`, `GOMS.date.parseDDMMYY()`, and `GOMS.date.formatForAPI()` to `utils.js`
- ✅ Removed duplicate `isDateInRange()` function from packing-lists.html (~20 lines)
- ✅ All functions exposed as global shortcuts for backward compatibility
- ✅ Version updated to GOMSv2.009

### JavaScript Utilities - Function #6: Pagination Utilities (COMPLETED)
- ✅ Added `GOMS.pagination.getTotalPages()`, `GOMS.pagination.goToPage()`, and `GOMS.pagination.updateControls()` to `utils.js`
- ✅ Updated pagination functions in packing-lists.html, group-bills.html, and stitching-records.html to use utilities
- ✅ Created wrapper functions that use page-specific variables with generic utilities
- ✅ All pagination functions now use centralized logic
- ✅ Version updated to GOMSv2.009

### Phase 3: Filter Manager Component (COMPLETED)
- ✅ Created `frontend/js/common/filter-manager.js` (~720 lines) with comprehensive filter management
- ✅ Implemented multi-select support with tags/chips UI (no checkboxes, color highlighting instead)
- ✅ Added support for dropdown, text, date, and radio filter types
- ✅ Implemented auto-extract options from data using `dataKey` or `customExtract` functions
- ✅ Added client-side filtering with debouncing (500ms)
- ✅ Added custom filter functions for hierarchical data (parent + child lines)
- ✅ Converted all text filters to dropdowns on packing-lists.html (except date filters)
- ✅ All filters now support multi-select capability
- ✅ Universal implementation - works on any page using FilterManager
- ✅ Updated `frontend/css/common.css` with filter styles and multi-select tag styles
- ✅ Tested on Packing Lists page as proof of concept
- ✅ Version updated to GOMSv2.011

### Phase 4: Fabric Invoices Filter Migration (COMPLETED)
- ✅ Migrated Fabric Invoices page to FilterManager
- ✅ Converted from server-side filtering to client-side filtering for consistency
- ✅ All dropdown filters (Customer, Fab Inv, Tax Inv, Item, DN, Location) now support multi-select
- ✅ Date filters (From/To) remain as text inputs with auto-formatting
- ✅ Stock Status filter uses radio buttons with custom filter logic
- ✅ Removed old filter implementation (~200 lines of code removed)
- ✅ Removed page-specific CSS that was causing first-option highlighting inconsistency
- ✅ All filters now work uniformly with multi-select support
- ✅ Version updated to GOMSv2.013

### Phase 4: Stitching Records Filter Migration (COMPLETED)
- ✅ Migrated Stitching Records page to FilterManager
- ✅ Converted from server-side filtering to client-side filtering for consistency
- ✅ All dropdown filters (PL#, Serial#, Fabric, Customer) now support multi-select
- ✅ Date filters (From/To) use custom filter functions for `created_at` field
- ✅ Delivery Status filter uses radio buttons with custom filter logic (checks `packing_list_number`)
- ✅ Preserved delivery status logic: delivered = has packing_list_number, undelivered = no packing_list_number
- ✅ Default filter remains "undelivered" (preserves original behavior)
- ✅ Removed old filter implementation (~150 lines of code removed)
- ✅ All filters now work uniformly with multi-select support
- ✅ Version updated to GOMSv2.014

### Phase 4: Group Bills Filter Migration (COMPLETED)
- ✅ Migrated Group Bills page to FilterManager
- ✅ Converted from server-side filtering to client-side filtering for consistency
- ✅ All dropdown filters (Customer, Group Number) now support multi-select
- ✅ Date filters (From/To) use custom filter functions that handle both Group Bills and Commission Sales data structures
- ✅ Group Number filter only applies to Group Bills view (returns true for Commission Sales items)
- ✅ Preserved toggle functionality: "Show Group Bills" / "Show Commission Sales" button still works correctly
- ✅ FilterManager updates data source when toggling views and re-applies filters
- ✅ Loads all data for both views upfront (client-side filtering)
- ✅ Removed old filter implementation (~100 lines of code removed)
- ✅ All filters now work uniformly with multi-select support
- ✅ Version updated to GOMSv2.015

### Phase 4: Dashboard Filter Migration (COMPLETED)
- ✅ Migrated Dashboard page to FilterManager
- ✅ Preserved server-side filtering (filters sent to API endpoints)
- ✅ All dropdown filters (Customer, Garment Type, Location) now support multi-select
- ✅ Date filters (From/To) integrated with FilterManager
- ✅ Preserved date range quick-select buttons (30D, 60D, 90D, YTD, LFY) - dashboard-specific feature
- ✅ Filter options loaded from API based on date range
- ✅ Fixed infinite loop issue by preventing filter updates during option loading
- ✅ Removed duplicate filter CSS (~130 lines) and JavaScript functions (~100 lines)
- ✅ All filters now work uniformly with multi-select support
- ✅ Version updated to GOMSv2.016

### Phase 3: Pagination Component (COMPLETED)
- ✅ Created `frontend/js/common/pagination.js` with `PaginationComponent` class
- ✅ Handles pagination HTML rendering, state management, and event handling
- ✅ Supports customizable container IDs, button IDs, and callback functions
- ✅ Includes page number calculation and display with ellipsis for large page counts
- ✅ Provides methods for updating data length, resetting to first page, and getting paginated data slices
- ✅ Version updated to GOMSv2.017

### Phase 3: Page Initializer Component (COMPLETED)
- ✅ Created `frontend/js/common/page-initializer.js` with `PageInitializer` class
- ✅ Handles common initialization patterns: theme loading, navigation rendering, auth checking
- ✅ Provides static methods for different initialization patterns (onLoad, onDOMReady, init)
- ✅ Configurable callbacks for auth success/failure
- ✅ Version updated to GOMSv2.017

### Phase 5: Pagination Refactoring (COMPLETED)
- ✅ Refactored all pages to use `PaginationComponent` and `PageInitializer`
  - Packing Lists: Migrated to `PaginationComponent` and `PageInitializer`
  - Stitching Records: Migrated to `PaginationComponent` and `PageInitializer`
  - Group Bills: Migrated to `PaginationComponent` and `PageInitializer`
  - Fabric Invoices: Migrated to `PageInitializer`, fixed pagination buttons (uses `TableManager` for pagination)
  - Dashboard: Migrated to `PageInitializer` (no pagination)
- ✅ Standardized pagination CSS in `frontend/css/common.css`
- ✅ Removed ~50-80 lines of duplicate pagination CSS from each page
- ✅ Removed ~80-100 lines of duplicate pagination code per page
- ✅ Removed ~50-80 lines of duplicate initialization code per page
- ✅ Fixed Fabric Invoices pagination buttons (Next/Previous) by adding `goToPreviousPage()` and `goToNextPage()` functions
- ✅ Updated `TableManager.updatePageNumbers()` to show ellipsis with first and last page numbers (matching `PaginationComponent` behavior)
- ✅ Consistent button styling across all pages (no borders, `gap: 10px`)
- ✅ All pages now show ellipsis correctly (e.g., `1...8,9,10,11,12...27`)
- ✅ Total: ~200-300 lines of duplicate code removed per page
- ✅ Version updated to GOMSv2.018

### Phase 5.5: Hierarchical Table Manager & Table Migrations (COMPLETED)
- ✅ Created `frontend/js/common/hierarchical-table-manager.js` – base component for flat and hierarchical tables (pagination, sorting, selection, optional customRender)
- ✅ **Fabric Invoices**: Migrated to `HierarchicalTableManager` (flat mode), `PaginationComponent`, and `TableSorter`; pagination and column sorting (including Location) working; version GOMSv2.020
- ✅ **Packing Lists**: Migrated to `HierarchicalTableManager` with `customRender`; 4 visual levels (parent PL → child line → secondary fabric → lining) preserved; pagination by packing list, sorting and filters wired; fixed `startIndex` when `skipPagination`; version GOMSv2.021
- ✅ **Group Bills**: Migrated to `HierarchicalTableManager` with `customRender`; Group Bills view (parent → Fabric/Stitching summary → detail rows) and Commission Sales view (flat) preserved; toggle, expand/collapse, sorting, filters, and selection unchanged; version GOMSv2.022

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

**Create `frontend/js/common/pagination.js`** - Reusable pagination component that handles:
- Rendering pagination HTML structure
- Managing pagination state (current page, items per page, data length)
- Updating pagination controls (buttons, page numbers, info text)
- Handling page navigation events
- Calculating paginated data slices
- ✅ **COMPLETED** - Created `PaginationComponent` class with full functionality

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

**Create `frontend/js/common/page-initializer.js`** - Handles common page initialization patterns:
- Theme loading (prevents flashing)
- Navigation bar rendering
- Authentication checking
- Coordinating data loading and filter setup
- ✅ **COMPLETED** - Created `PageInitializer` class with static methods for different initialization patterns

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
- **Type**: Client-side filtering (filters loaded data in memory) ✅ **MIGRATED**
- **Method**: FilterManager with enhanced dropdowns and multi-select
- **Filters**: 
  - Customer (multi-select dropdown) ✅
  - Fabric Invoice (multi-select dropdown) ✅
  - Tax Invoice (multi-select dropdown) ✅
  - Item Code (multi-select dropdown) ✅
  - Delivery Note (multi-select dropdown) ✅
  - Location (multi-select dropdown) ✅
  - Date From/To (text input with auto-format)
  - Stock Status (radio buttons: inStock/noStock with custom filter logic)
- **Implementation**: `FilterManager` class with `filterConfig` array
- **Special**: Auto-extracts options from loaded data, supports multi-select, consistent behavior with other pages

#### Stitching Records
- **Type**: Client-side filtering (filters loaded data in memory) ✅ **MIGRATED**
- **Method**: FilterManager with enhanced dropdowns and multi-select
- **Filters**: 
  - PL# (multi-select dropdown) ✅
  - Serial# (multi-select dropdown) ✅
  - Fabric (multi-select dropdown) ✅
  - Customer (multi-select dropdown) ✅
  - Date From/To (text input with custom filter for `created_at` field)
  - Delivery Status (radio buttons: all/delivered/undelivered with custom filter logic)
- **Implementation**: `FilterManager` class with `filterConfig` array
- **Special**: Auto-extracts options from loaded data, supports multi-select, delivery status checks `packing_list_number` field, default remains "undelivered"

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
- **Type**: Client-side filtering (filters loaded data in memory) ✅ **MIGRATED**
- **Method**: FilterManager with enhanced dropdowns and multi-select
- **Filters**: 
  - Customer (multi-select dropdown) ✅
  - Group Number (multi-select dropdown, only filters Group Bills view) ✅
  - Date From/To (text input with custom filter for both Group Bills and Commission Sales data structures) ✅
- **Implementation**: `FilterManager` class with `filterConfig` array
- **Special**: Auto-extracts options from loaded data, supports multi-select, handles both Group Bills and Commission Sales views, toggle button preserved and works with FilterManager

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

1. **Phase 1**: Create unified `FilterManager` with multi-select support ✅ **COMPLETED**
2. **Phase 2**: Convert all pages to use enhanced dropdowns with multi-select:
   - **Fabric Invoices**: ✅ **COMPLETED** - Migrated to FilterManager with multi-select, client-side filtering
   - **Packing Lists**: ✅ **COMPLETED** - Migrated to FilterManager with multi-select dropdowns
   - **Stitching Records**: ✅ **COMPLETED** - Migrated to FilterManager with multi-select dropdowns, delivery status logic preserved
   - **Group Bills**: ✅ **COMPLETED** - Migrated to FilterManager with multi-select dropdowns, toggle functionality preserved
   - **Dashboard**: ✅ **COMPLETED** - Migrated to FilterManager with multi-select dropdowns, server-side filtering preserved, date range buttons preserved
3. **Phase 3**: Standardize filter configurations:
   - All filters use the same UI pattern ✅ (All pages: Fabric Invoices, Packing Lists, Stitching Records, Group Bills, Dashboard)
   - All filters support multi-select ✅ (All pages)
   - All filters have search functionality ✅ (All pages)
   - Date filters remain as text inputs (with auto-format) ✅
   - Radio button filters remain as radio buttons ✅

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

### ✅ Phase 2: Extract JavaScript Utilities (COMPLETED)
- [x] Create `frontend/js/common/utils.js`
- [x] Move theme functions (Function #1: ✅ COMPLETED)
- [x] Move formatting functions (Function #2: ✅ COMPLETED)
- [x] Move API utilities (Function #3: ✅ COMPLETED)
- [x] Move auth utilities (Function #4: ✅ COMPLETED)
- [x] Move date utilities (Function #5: ✅ COMPLETED)
- [x] Move pagination utilities (Function #6: ✅ COMPLETED)
- [x] Update all HTML files to include `utils.js`
- [x] Remove duplicated functions from HTML files (Functions #1-6)
- [x] Test all pages for functionality (Functions #1-6)

### Phase 3: Create Components (COMPLETED)
- [x] Create `frontend/js/common/filter-manager.js` with multi-select
- [x] Test FilterManager on Packing Lists page (proof of concept)
- [x] Create `frontend/js/common/pagination.js`
- [x] Create `frontend/js/common/page-initializer.js`
- [x] Create `frontend/js/common/hierarchical-table-manager.js`

### Phase 4: Standardize Filters (COMPLETED)
- [x] FilterManager component created with multi-select support
- [x] Packing Lists page migrated to FilterManager (all filters are dropdowns except date)
- [x] Fabric Invoices page migrated to FilterManager (all dropdowns support multi-select, client-side filtering)
- [x] Stitching Records page migrated to FilterManager (all dropdowns support multi-select, delivery status logic preserved)
- [x] Group Bills page migrated to FilterManager (all dropdowns support multi-select, toggle functionality preserved)
- [x] Dashboard page migrated to FilterManager (all dropdowns support multi-select, server-side filtering preserved, date range buttons preserved)
- [x] Standardize filter configurations across all pages
- [x] Ensure all filters support multi-select
- [x] Test filter behavior on all pages

### Phase 5: Pagination Refactoring (COMPLETED)
- [x] Refactor Packing Lists to use PaginationComponent and PageInitializer
- [x] Refactor Stitching Records to use PaginationComponent and PageInitializer
- [x] Refactor Group Bills to use PaginationComponent and PageInitializer
- [x] Refactor Fabric Invoices to use PageInitializer
- [x] Refactor Dashboard to use PageInitializer
- [x] Standardize pagination CSS in common.css
- [x] Remove duplicate pagination CSS from all pages
- [x] Fix Fabric Invoices pagination buttons (Next/Previous)
- [x] Update TableManager to show ellipsis with first/last page
- [x] Test all pagination on all pages
- [x] Update version to GOMSv2.018
- [x] Commit changes

### Phase 6: Cleanup (PENDING)
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
- `js/common/utils.js`: ~339 lines (✅ Completed - All Functions #1-6 completed)
- `js/common/filter-manager.js`: ~720 lines (✅ Completed - with multi-select, tested on Packing Lists)
- `js/common/pagination.js`: ~269 lines (✅ Created)
- `js/common/hierarchical-table-manager.js`: ~664 lines (✅ Created – flat/hierarchical, customRender, pagination, sorting)
- `js/common/page-initializer.js`: ~91 lines (✅ Created)
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
