# Frontend Code Refactoring - Common Components

## Executive Summary

This document addresses the massive code duplication in frontend HTML files. Analysis shows **~11,000+ lines of duplicated code** across themes, tables, sorting, filters, and common behaviors that should be extracted into reusable components.

**Status**: Phase 1 (CSS Extraction), Navigation Bar refactoring, JavaScript Utilities (Functions #1-6), Filter Manager component completed, all filter migrations completed, pagination refactoring completed (all pages use PaginationComponent and PageInitializer), and **table migrations completed**: Fabric Invoices, Packing Lists, Group Bills, and Stitching Records now use `HierarchicalTableManager` (with `PaginationComponent` and `TableSorter`). Phase 6 cleanup (duplicate CSS/comments removed). **Phase 7 plan** (Section 6.1): further CSS consolidation—analysis of fabric-invoices lines 13–664 vs other pages; plan to move .btn, .action-buttons, .table-container, .data-table, .checkbox-wrapper, .modal, .form-group, .loading-state/.error-state to common.css and in-page cleanups. Current version: GOMSv2.024.

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
- ✅ **Stitching Records**: Migrated to `HierarchicalTableManager` with `customRender`; 2-level treeview (parent row per record, child rows for garment_fabrics and lining_fabrics) and expand/collapse preserved; pagination by record count, sorting and filters wired; selection by actualIndex preserved; version GOMSv2.023

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
- **Implementation**: Uses `HierarchicalTableManager` (flat mode) from `hierarchical-table-manager.js`, with `PaginationComponent` and `TableSorter`
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
- **Implementation**: `HierarchicalTableManager` with `customRender`; existing treeview markup and expand/collapse preserved
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
- **Implementation**: `HierarchicalTableManager` with `customRender`; existing parent/child/secondary/lining markup and expand/collapse preserved
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
- **Implementation**: `HierarchicalTableManager` with `customRender`; existing parent/child/detail markup and expand/collapse preserved; Commission Sales view uses same manager with different data
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

#### Hierarchical Table Manager (COMPLETED)

**Created `frontend/js/common/hierarchical-table-manager.js`** – base component for flat and hierarchical tables (pagination, sorting, selection, optional `customRender`).

#### Page Table Configurations (all migrated)

- **Fabric Invoices**: `HierarchicalTableManager` (flat mode), `PaginationComponent`, `TableSorter`
- **Packing Lists**: `HierarchicalTableManager` with `customRender` (4 visual levels: parent PL → child line → secondary fabric → lining)
- **Group Bills**: `HierarchicalTableManager` with `customRender` (Group Bills hierarchy + Commission Sales flat view)
- **Stitching Records**: `HierarchicalTableManager` with `customRender` (2-level treeview: parent record → garment_fabrics/lining_fabrics child rows)

### 5.7 Refactoring Strategy for Filters

#### Unified Filter Manager with Standardized Behavior and Multi-Select

**IMPORTANT**: All filters will work the same way across all pages with:
- **Standardized UI**: Enhanced dropdowns with search (like Fabric Invoices)
- **Multi-select capability**: Users can select multiple values for each filter
- **Unified behavior**: Same interaction pattern on all pages
- **Client-side filtering**: All pages will filter loaded data in memory (for consistency)

**Create `frontend/js/common/filter-manager.js`** (see Section 11.7 in original document for full implementation with multi-select support).

### 5.8 Migration Plan for Tables

1. **Phase 1**: Create `HierarchicalTableManager` base class ✅ **COMPLETED**
2. **Phase 2**: Migrate pages using shared manager (flat mode or `customRender` for existing markup) ✅ **COMPLETED**:
   - **Fabric Invoices**: Flat mode, `PaginationComponent`, `TableSorter` (GOMSv2.020)
   - **Packing Lists**: `customRender`, 4 visual levels preserved (GOMSv2.021)
   - **Group Bills**: `customRender`, Group Bills + Commission Sales views preserved (GOMSv2.022)
   - **Stitching Records**: `customRender`, 2-level treeview preserved (GOMSv2.023)
3. No page-specific subclasses; all use `HierarchicalTableManager` with optional `customRender` for pages that keep their own row HTML.

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

### Phase 6: Cleanup (IN PROGRESS)
- [x] Remove duplicate CSS from pages (filter-controls, filter-row, filter-group, filter-input, filter-dropdown, etc. in common.css)
- [x] Remove duplicate `formatDateForAPI` from stitching-records (use `GOMS.date.formatForAPI` from utils.js)
- [x] Remove redundant "Pagination Styles - moved to common.css" and duplicate filter/action-buttons blocks from group-bills, packing-lists, stitching-records
- [x] Simplify comments in fabric-invoices (pagination wrappers, API/auth moved to utils)
- [ ] Final testing (see testing list below)

---

## 6.1 Phase 7: Further CSS Consolidation (PLAN – no coding yet)

This section documents the analysis of **fabric-invoices.html** inline styles (lines 13–664) and comparison with **packing-lists**, **group-bills**, **stitching-records**, and **dashboard** (first ~800 lines / `<style>` blocks) to identify what can be moved to `common.css` or otherwise refactored.

### 6.1.1 Inventory: fabric-invoices.html &lt;style&gt; (lines 13–664)

| Block | Description | Lines (approx) |
|-------|-------------|----------------|
| `.checkbox-label` | Checkbox + label flex | 13–23 |
| `.table-container` | Card, border, overflow (first block) | 25–33 |
| `.data-table` | Base table, th, td, tr:hover, tr.selected | 35–66 |
| `.table-container` (second block) | max-height 600px, overflow-y, scrollbar | 68–93 |
| `.checkbox-wrapper`, `.data-table td.checkbox-wrapper` | Checkbox cell alignment | 95–114 |
| `.data-table tr` cursor/hover | Non-clickable row, hover | 116–127 |
| `.action-buttons` | Flex, gap, margin-bottom | 129–135 |
| Bulk item list | `.bulk-item-list`, `.bulk-item-row`, `.item-info`, `.control-group`, `.yards-input`, etc. | 138–220 |
| **`.btn`** (base + variants) | .btn, .btn-primary … .btn-info | 222–286 |
| Import progress | `.import-progress`, `.progress-bar`, `.progress-fill`, `.progress-text` | 288–316 |
| **Modal** | `.modal`, `#costDialog/#priceDialog` z-index, `.modal-content`, `.modal-header`, `.modal-title`, `.close`, `.form-group`, `.modal-footer` | 319–414 |
| **Custom dialog** | `.custom-dialog`, `.custom-dialog-content`, `.custom-dialog-header`, `.custom-dialog-btn-*` (primary, secondary, success, warning, danger, info) | 416–559 |
| Fabric selection dialog hover | `.fabric-selection-dialog table tbody tr:hover` | 543–550 |
| Content section | `.content-section`, `.section-header` | 561–576 |
| Cost/Price list tables | `#costListTable`, `#priceListTable` | 578–604 |
| **`.action-buttons`** (duplicate) | display flex, gap 5px | 606–609 |
| `.btn-edit`, `.btn-delete` | Small action buttons | 611–636 |
| Dialog-specific | `.modal-content[style*="width: 90%"]`, `#selectedLinesInfo` | 638–663 |

### 6.1.2 Duplication Across Pages

| Style / pattern | Fabric | Packing | Group | Stitching | Dashboard | In common.css? |
|-----------------|--------|---------|-------|-----------|-----------|----------------|
| **.btn** (base + .btn-primary … .btn-info) | ✓ ~65 lines | ✓ ~70 lines | ✓ ~65 lines | ✓ ~65 lines | ✓ ~65 lines | **No** → move |
| **.action-buttons** (base: flex, gap, margin) | ✓ (2x – duplicate) | ✓ | ✓ (card wrapper variant) | ✓ | (uses filter row) | **No** → move base |
| **.table-container** (card, max-height, overflow-y) | ✓ (2 blocks) | ✓ | ✓ | ✓ | — | **No** → move |
| **.table-container** scrollbar (webkit) | ✓ | ✓ (+ data-table-container) | ✓ | ✓ (+ treeview-container) | — | **No** → move |
| **.data-table** (base, th, td, tr:hover, tr.selected) | ✓ | ✓ (sticky th, min-width) | ✓ (sticky th) | ✓ (treeview separate) | — | **No** → move base |
| **.checkbox-wrapper** | ✓ | ✓ (2x – duplicate) | ✓ (2x – duplicate) | ✓ | — | **No** → move |
| **.data-table tr** cursor/hover | ✓ | ✓ | ✓ | ✓ (#424242 hardcoded) | — | **No** → move; fix stitching var |
| **.modal** (base, content, header, title, close, footer, body) | ✓ | — | ✓ | ✓ (z-index 10000) | — | **No** → move |
| **.form-group** (label, input, select, textarea, focus) | ✓ | — | ✓ | — | — | **No** → move |
| **.loading-state**, **.error-state** | — | ✓ | ✓ | — | — | **No** → move |
| Filter/nav/pagination | — | — | — | — | — | **Yes** (already) |

### 6.1.3 Page-Only Styles (keep in page or optional common extras)

- **Fabric-invoices only:** `.checkbox-label`, bulk item list (`.bulk-item-list`, `.bulk-item-row`, `.item-*`, `.control-group`, `.yards-input`), `.import-progress` / `.progress-bar` / `.progress-fill` / `.progress-text`, `#costDialog` / `#priceDialog` z-index, `.custom-dialog*` (if only fabric uses full set, consider moving base to common for future reuse), `.fabric-selection-dialog`, `.content-section`, `#costListTable` / `#priceListTable`, `.btn-edit` / `.btn-delete`, `.modal-content[style*="width: 90%"]`, `#selectedLinesInfo`.
- **Packing-lists only:** `.data-table-container`, `.parent-row`, `.child-row`, `.secondary-fabric-row`, `.lining-fabric-row`, `.expand-indicator`, column `nth-child` widths.
- **Group-bills only:** `.action-buttons` card wrapper (background, padding, border), `.commission-sales-table`, `.checkbox-group`, hierarchy (`.parent-row`, `.child-row`, `.sub-child-row`, `.detail-row`, `.expand-indicator`, indentation), column widths.
- **Stitching-records only:** `.treeview-container`, `.treeview-table`, `.treeview-parent`, `.treeview-child`, `.expand-indicator`, `.status-badge`, `.image-preview`, `.detail-section` / `.detail-grid` / `.detail-item`, `.size-quantities`, treeview column widths.
- **Dashboard only:** `.date-range-buttons`, `.date-btn`, `.kpi-grid` / `.kpi-card` / `.kpi-*`, `.charts-grid` / `.chart-card` / `.chart-container`, `.loading`.

### 6.1.4 Refactor Plan (to implement in Phase 7)

1. **Move to `common.css`** (then remove from each page):
   - **Button set:** `.btn` (base) + `.btn-primary`, `.btn-secondary`, `.btn-success`, `.btn-warning`, `.btn-danger`, `.btn-info` and `:hover`. Use one canonical set (e.g. fabric-invoices) and drop from packing, group, stitching, dashboard.
   - **Action bar base:** `.action-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }`. Group-bills keeps its override (card wrapper) in page.
   - **Table container:** `.table-container` base (card, border, max-height 600px or 500px – pick one or use a variable), plus `.table-container::-webkit-scrollbar` (track, thumb, thumb:hover). Optionally `.data-table-container` if shared (packing, group).
   - **Data table base:** `.data-table` (width, border-collapse, font-size), `.data-table th` (background, color, padding, border-bottom, font-weight), `.data-table td` (padding, border-bottom), `.data-table tr:hover`, `.data-table tr.selected`. Pages that need `text-align: left`, `sticky` th, or `min-width` add overrides in page.
   - **Checkbox:** `.checkbox-wrapper` (flex, center), `.checkbox-wrapper input[type="checkbox"]`, `.data-table td.checkbox-wrapper` if shared. Optionally `.checkbox-label` if used on more than one page.
   - **Row behavior:** `.data-table tr { cursor: default; }`, `.data-table tr:hover`, `.data-table tr:hover td` using `var(--bg-tertiary)` (not hardcoded).
   - **Modal:** `.modal` (fixed overlay), `.modal-content`, `.modal-header`, `.modal-title`, `.close`, `.modal-body`, `.modal-footer`. Stitching’s higher z-index can stay as page override or be a modifier in common.
   - **Form in modals:** `.form-group`, `.form-group label`, `.form-group input/select/textarea`, `:focus` (shared by fabric, group).
   - **Loading/error:** `.loading-state`, `.error-state` (packing, group).

2. **In-page cleanups (no new common CSS):**
   - **Fabric-invoices:** Merge the two `.table-container` blocks into one; remove the second `.action-buttons` definition (line 606–609).
   - **Packing-lists:** Remove duplicate `.checkbox-wrapper` block (lines 294–308 duplicate 265–279).
   - **Group-bills:** Remove duplicate `.checkbox-wrapper` block (second block ~316–325).
   - **Stitching-records:** Replace `.data-table tr:hover` / `tr:hover td` hardcoded `#424242` with `var(--bg-tertiary)` for theme consistency.

3. **Optional (later):**
   - **Custom dialog:** If only fabric-invoices uses `.custom-dialog*`, either move a minimal base to common for future reuse or leave in fabric. Align `.custom-dialog-btn-*` with `.btn-*` where possible (e.g. use `.btn` inside dialogs) to reduce duplication.
   - **Column widths:** Keep all `nth-child` column widths page-specific (table structure differs per page).

### 6.1.5 Phase 7 Checklist (when implementing)

- [ ] Add to `common.css`: .btn set, .action-buttons base, .table-container + scrollbar, .data-table base, .checkbox-wrapper, .data-table tr cursor/hover, .modal set, .form-group set, .loading-state/.error-state.
- [ ] Remove from fabric-invoices: duplicated blocks above; merge .table-container; remove duplicate .action-buttons.
- [ ] Remove from packing-lists, group-bills, stitching-records, dashboard: same duplicated blocks; remove duplicate .checkbox-wrapper on packing and group.
- [ ] Stitching-records: replace #424242 with var(--bg-tertiary) for .data-table tr:hover.
- [ ] Test all pages: buttons, action bars, tables, modals, forms, loading/error states, theme toggle.
- [ ] Update version and FRONTEND_REFACTORING.md when Phase 7 is done.

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

## Testing After Phase 6 Cleanup

After the cleanup (removal of duplicate CSS, `formatDateForAPI`, and redundant comments), verify the following:

1. **Login** (`login.html`): Theme toggle, login flow, redirect after auth.
2. **Dashboard** (`dashboard.html`): Nav, theme, filter controls (Customer, Garment Type, Location, Date From/To), date range buttons (30D, 60D, 90D, YTD, LFY), KPI cards, charts load.
3. **Fabric Invoices** (`fabric-invoices.html`): Nav, theme, FilterManager (Customer, Fab Inv, Tax Inv, Item, DN, Location, dates, Stock Status), table sort, pagination (Next/Previous, page numbers), row selection, bulk actions, inline edit, modals.
4. **Packing Lists** (`packing-lists.html`): Nav, theme, FilterManager (PL#, Serial#, Fabric, Customer, etc.), hierarchical table (expand/collapse parent/child/secondary/lining), pagination, selection, PDF, assign tax invoice.
5. **Group Bills** (`group-bills.html`): Nav, theme, FilterManager (Customer, Group Number, dates), toggle "Show Group Bills" / "Show Commission Sales", expand/collapse groups and fabric/stitching details, pagination, selection, PDF actions.
6. **Stitching Records** (`stitching-records.html`): Nav, theme, FilterManager (PL#, Serial#, Fabric, Customer, dates, Delivery Status), treeview expand/collapse, pagination, selection, Refresh/Export/Generate Packing List/Delete Selected; date filters use `isDateInRange`/`formatForAPI` from utils.
7. **Common**: All pages use `common.css` (no missing filter/button/table styles), nav from `nav-bar.js`, theme from `utils.js`, no console errors.

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
