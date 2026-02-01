# Server-Side Loading Refactoring Plan

**Status:** Implementation completed (no commit made).  
**Goal:** Migrate list pages from client-side to server-side loading and apply recommendations so every table loads fast.

**Testing plan:** See [TESTING_PLAN_SERVER_SIDE.md](TESTING_PLAN_SERVER_SIDE.md).

---

## 1. Current State Summary

| Page | Data Load | API(s) | Filter Params Today | Notes |
|------|-----------|--------|---------------------|--------|
| **Fabric Invoices** | One full fetch + 3 sequential (cost, price, customers) | `/api/invoices`, `/api/cost-price/*`, `/api/customers` | None (client-side) | Backend already supports `customer`, `invoice_number`, `tax_invoice`, `item_code`, `dn`, `location`, `date_from`, `date_to`, `stock_status` |
| **Stitching Records** | One full fetch | `/api/stitching` | None (client-side) | Backend supports `pl_number`, `serial_number`, `fabric_name`, `customer`, `date_from`, `date_to`, `delivered_only`, `undelivered_only` |
| **Packing Lists** | One full fetch | `/api/packing-lists` | None (client-side) | Backend supports `pl_serial`, `stitch_serial`, `fabric_name`, `customer`, `tax_invoice`, `fabric_invoice`, `fabric_dn`, `date_from`, `date_to`, `billing_status` |
| **Group Bills** | Two full fetches (sequential) | `/api/group-bills`, `/api/group-bills/commission-sales` | None (client-side) | Backend supports `customer`, `status`, `date_from`, `date_to` for both |
| **Dashboard** | Server-side (unchanged) | `/api/dashboard/*` with query params | Yes | Reference implementation |

**Backend:** All list endpoints already accept filter query parameters. None currently support `limit`/`offset` or multi-value filters (e.g. multiple customers).

---

## 2. Refactoring Plan: Server-Side Loading

### Phase 0: Prerequisites and Decisions

- [ ] **Freeze scope:** Confirm which pages migrate (recommended: Fabric Invoices, Stitching, Packing Lists, Group Bills).
- [ ] **Multi-select semantics:** Decide how multi-select filters map to API (e.g. `customer=A&customer=B` vs `customer=A,B`). Recommend comma-separated for simplicity; backend already uses `ilike` so a single “A,B” could be split and OR’d or handled via IN.
- [ ] **Filter options source:** Choose one:
  - **Option A:** Dedicated filter-options endpoints per resource (e.g. `/api/invoices/filter-options?date_from=...`) returning distinct values for dropdowns. Best for large datasets.
  - **Option B:** One lightweight “options-only” fetch on load (e.g. minimal fields or a dedicated “distinct” endpoint). Avoids loading full list for options.
  - **Option C:** First page only: request with default filters and use that response to populate options (simpler but options depend on first page).
- [ ] **Pagination:** Decide server-side pagination vs “server filter + client paginate current result set.” Full server-side pagination (limit/offset) is recommended for very large tables.

---

### Phase 1: Backend API Enhancements

**1.1 Pagination (limit / offset)**

- [ ] Add optional query params to list endpoints:
  - `limit` (default e.g. 50 or 100; max cap e.g. 500)
  - `offset` (default 0)
- [ ] Endpoints: `GET /api/invoices`, `GET /api/stitching`, `GET /api/packing-lists`, `GET /api/group-bills`, `GET /api/group-bills/commission-sales`.
- [ ] Response shape: either **paginated** (e.g. `{ "items": [...], "total": N }`) or **list + total** (e.g. `X-Total-Count` header + body array). Document chosen contract for frontend.

**1.2 Multi-value filter support**

- [ ] For dropdown filters that are multi-select (customer, invoice number, etc.), accept multiple values:
  - Either: repeated params `customer=A&customer=B`
  - Or: single param with comma-separated values `customer=A,B` (backend splits and applies IN or OR).
- [ ] Apply consistently across: invoices, stitching, packing_lists, group_bills, commission-sales.
- [ ] Document param names and formats in README or OpenAPI.

**1.3 Filter-options endpoints (if Option A chosen)**

- [ ] Add e.g.:
  - `GET /api/invoices/filter-options?date_from=...&date_to=...` → `{ "customers": [...], "invoice_numbers": [...], ... }`
  - `GET /api/stitching/filter-options?date_from=...&date_to=...`
  - `GET /api/packing-lists/filter-options?...`
  - `GET /api/group-bills/filter-options?...` (and optionally commission-sales)
- [ ] Each returns only distinct values needed for dropdowns (and optionally counts), scoped by other filters to avoid leaking data.

**1.4 Response size and performance**

- [ ] Ensure list queries use appropriate indexes (e.g. date, customer_id, status).
- [ ] Avoid N+1: use `joinedload`/`selectinload` where already in use; verify no extra queries per row.
- [ ] Remove or gate verbose debug logging in production (e.g. `print` in invoices route).

---

### Phase 2: FilterManager Server-Side Mode

**2.1 Config and behavior**

- [ ] Add optional config: `serverSide: true`.
- [ ] When `serverSide` is true:
  - Do **not** store full dataset in `this.data` (or keep it empty).
  - Do **not** run `applyFilters()` over in-memory data.
  - On filter change (and optionally on init): call a callback with current filter values only, e.g. `onServerFilterRequest(filterValues)` or reuse `onFilterChange(filteredData, filterValues)` with `filteredData` null or omitted to indicate “server-side, please refetch.”
- [ ] Document: when `serverSide` is true, the page is responsible for calling the API with `filterValues` and setting the table data (and optionally updating FilterManager with new data for dropdown options if not using filter-options API).

**2.2 Dropdown options in server-side mode**

- [ ] If using filter-options API: add optional `optionsUrl` or `optionsFetcher` per filter so FilterManager (or the page) can fetch options when dropdown opens.
- [ ] If options come from the page (e.g. from first response or a separate fetch): page passes `filter.options` or updates options after load; FilterManager stays agnostic.
- [ ] Ensure multi-select dropdowns still work when options are loaded asynchronously.

**2.3 Backward compatibility**

- [ ] When `serverSide` is false or unspecified, behavior remains as today (client-side filter over `this.data`).
- [ ] Dashboard and any page not migrated keep using current behavior.

---

### Phase 3: Page-by-Page Migration

**3.1 Fabric Invoices**

- [ ] Build API URL helper: from `filterManager.getFilterValues()` build query string (customer, invoice_number, tax_invoice, item_code, dn, location, date_from, date_to, stock_status; multi-value for dropdowns per backend contract).
- [ ] Add pagination params: `limit`, `offset` from current page and page size.
- [ ] Replace `loadInvoiceData()` “fetch all” with “fetch with params.” On load and on every filter (and page) change, call this function.
- [ ] Initialize FilterManager with `serverSide: true` and `onFilterChange` (or `onServerFilterRequest`) that triggers the same fetch-and-set-table flow.
- [ ] Filter options: either call `/api/invoices/filter-options` when initializing filters / when dropdown opens, or keep one lightweight “options” load; then pass options into FilterManager or set in filter config.
- [ ] Keep `loadCostList()`, `loadPriceList()`, `loadCustomers()` for their existing use (e.g. create/edit forms). Optionally run in parallel with first table fetch to speed up initial load (see Section 3).

**3.2 Stitching Records**

- [ ] Map filter values to API: `pl_number`, `serial_number`, `fabric_name`, `customer`, `date_from`, `date_to`, delivery status → `delivered_only` / `undelivered_only`.
- [ ] Add limit/offset to `/api/stitching` and use response total for pagination.
- [ ] Replace single “fetch all” with fetch-with-params; call on load and on filter/page change.
- [ ] FilterManager `serverSide: true`; options from filter-options endpoint or from first/lightweight response.

**3.3 Packing Lists**

- [ ] Map filter values to existing packing-lists API params; add limit/offset.
- [ ] Same pattern: fetch with params on load and on filter/page change; FilterManager server-side mode; options as chosen in Phase 0.

**3.4 Group Bills**

- [ ] Two APIs: group-bills and commission-sales. Both must receive the same filter params (and limit/offset if applicable).
- [ ] On “Group Bills” view: fetch `/api/group-bills` with params; on “Commission Sales” view: fetch `/api/group-bills/commission-sales` with params. On filter change, refetch current view.
- [ ] FilterManager server-side; options for Customer (and any other dropdowns) from filter-options or first response.
- [ ] Toggle between views continues to switch data source and refetch with current filters.

---

### Phase 4: Server-Side Pagination (Frontend)

- [ ] **PaginationComponent / HierarchicalTableManager:** When data is server-paginated, “total” comes from API (e.g. `total` in JSON or `X-Total-Count`). “Go to page N” means requesting with `offset = (N-1) * limit` (or `page` if backend uses page).
- [ ] Table manager receives one page of data; no client-side slice. Pagination controls show total pages from `total` and page size.
- [ ] Preserve sort: if backend supports `sort`/`order_by` params, pass current sort column and direction on every request so pagination and sort stay in sync.

---

### Phase 5: Testing and Rollback

- [ ] Test each page: filters, multi-select, date range, pagination, sort (if server-side sort added).
- [ ] Test with large datasets (e.g. 10k+ rows) to confirm only one page is returned and UI stays responsive.
- [ ] Rollback strategy: feature flag or config (e.g. `USE_SERVER_SIDE_LOADING`) so each page can switch back to client-side load without code revert; or keep old `load*Data()` path behind flag until migration is validated.

---

## 3. Other Recommendations for Fast Table Loading

These can be done alongside or after the server-side migration.

### 3.1 Parallelize initial requests (Fabric Invoices)

- **Current:** `loadInvoiceData()` → `loadCostList()` → `loadPriceList()` → `loadCustomers()` (sequential).
- **Recommendation:** Run independent requests in parallel: e.g. `Promise.all([loadInvoiceData(), loadCostList(), loadPriceList(), loadCustomers()])` so table and dropdown/options data load together. Ensure FilterManager and table init do not depend on cost/price/customers for first paint; show table as soon as invoice data arrives.

### 3.2 Group Bills: parallelize the two list fetches

- **Current:** `groupBillsResponse` then `commissionSalesResponse` (sequential).
- **Recommendation:** Use `Promise.all([fetch(group-bills), fetch(commission-sales)])` when both datasets are needed up front. If only one view is shown at a time, consider loading the other view lazily when user switches (reduces initial load).

### 3.3 Lazy / deferred loading of non-critical data

- **Filter dropdown options:** Load options when the user opens a dropdown (or after first paint) instead of blocking initial table render. Requires filter-options API or one lightweight options request.
- **Heavy modals/dialogs:** Load their data (e.g. delivery locations, stitched items) when the modal is first opened, not on page load.

### 3.4 Loading and perceived performance

- **Skeleton or placeholder rows:** Show a few placeholder rows or a spinner as soon as the request starts so the table “frame” appears immediately.
- **Progressive render (optional):** If backend sent a stream, render rows as they arrive; otherwise avoid—simpler to render one page at a time.

### 3.5 Caching and request deduplication

- **Filter-options:** Cache options in memory (or short-lived sessionStorage) per filter key so reopening the same dropdown doesn’t refetch.
- **Deduplication:** If the user changes filters rapidly, cancel previous fetch or ignore stale responses (e.g. AbortController + new request per latest filter state).

### 3.6 Backend

- **Indexes:** Ensure indexes on columns used in filters and sort (e.g. `invoice_date`, `created_at`, `customer_id`, `short_name`).
- **Query review:** Use query logging in dev to confirm no N+1 and that filters use indexes.
- **Compression:** Enable gzip (or similar) for JSON responses in production (often default in Flask/Railway).

### 3.7 Frontend assets

- **Cache static assets:** Ensure HTML/JS/CSS are cached with sensible cache-control (or versioned URLs). Reduces repeat load time when navigating between pages.

### 3.8 Optional: virtual scrolling

- **When:** Only if a single page of rows is still large (e.g. 500+ rows) and DOM is slow.
- **How:** Render only visible rows (e.g. 50) and recycle DOM nodes as the user scrolls. Requires integration with HierarchicalTableManager or a dedicated virtual-list component. Lower priority than server-side pagination.

---

## 4. Implementation Order (Suggested)

1. **Phase 0** – Decide multi-value format, filter-options strategy, and pagination contract.
2. **Phase 1** – Backend: add limit/offset and multi-value filters; add filter-options endpoints if used.
3. **Phase 2** – FilterManager server-side mode and docs.
4. **Phase 3** – Migrate one page first (e.g. Stitching Records—single API, fewer filters) as pilot; then Fabric Invoices, Packing Lists, Group Bills.
5. **Phase 4** – Wire server-side pagination in PaginationComponent and table managers.
6. **Phase 5** – Test and optional feature flag.
7. **Recommendations** – Parallelize Fabric Invoices and Group Bills requests; lazy options; loading states; backend indexes and compression.

---

## 5. Implementation Summary (Completed)

- **Backend:** All list endpoints return `{ "items": [...], "total": N }`; support `limit` (default 50, max 500), `offset`, and comma-separated multi-value filters. Filter-options endpoints added: `/api/invoices/filter-options`, `/api/stitching/filter-options`, `/api/packing-lists/filter-options`, `/api/group-bills/filter-options`.
- **FilterManager:** `serverSide: true` mode; `onFilterChange(null, filterValues)` triggers page refetch.
- **HierarchicalTableManager:** `serverSidePagination: true`, `onPageChange(page)`, `setServerSideTotal(total)`.
- **Pages:** Fabric Invoices, Stitching Records, Packing Lists, Group Bills now fetch with filter params and pagination; filter options loaded from API; AbortController used for in-flight request cancellation; Fabric Invoices init runs filter-options + cost/price/customers in parallel.

---

## 6. Document History

| Date | Change |
|------|--------|
| 2025-01-28 | Initial plan created (no code changes). |
| 2025-01-28 | Implementation completed; testing plan added. |
