# Testing Plan: Server-Side Loading

Use this checklist after the server-side loading refactor to confirm nothing is broken. **Do not commit** until you have run through the tests that apply to your usage.

---

## Prerequisites

- Backend running (e.g. Flask on port 8000).
- Frontend served (e.g. HTTP server on port 3000).
- Logged in with a user that can access all list pages.

---

## 1. Fabric Invoices

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 1.1 | First load | Open Fabric Invoices page. | Table loads with first page (up to 50 rows). Pagination shows "Showing 1 to X of Y records" with correct total. No console errors. |
| 1.2 | Filter dropdowns | Open Customer, Fab Inv, Tax Inv, Item, DN, Location dropdowns. | Options are populated (from filter-options API). Multi-select works; selected values show as tags. |
| 1.3 | Apply filters | Select one or more values in Customer (or other dropdown), set date From/To, change Stock Status. | Table refetches and shows filtered results. Total updates. Pagination resets to page 1. |
| 1.4 | Clear filters | Click "Clear Filter". | Filters reset; table refetches with no filters; full first page and total shown. |
| 1.5 | Pagination | Click Next/Previous or a page number. | Table shows the requested page; "Showing X to Y of Z" updates correctly. |
| 1.6 | Sort | Click a sortable column header. | Client-side sort applies to current page (if table sorter is still wired). No crash. |
| 1.7 | Refresh after action | Create/edit/delete an invoice line or perform an action that calls `loadInvoiceData(1, ...)`. | Table refreshes with current filters and page 1. |
| 1.8 | Parallel load | On first load, check Network tab. | Requests to `/api/invoices`, `/api/invoices/filter-options`, cost, price, customers can run in parallel where implemented. |

---

## 2. Stitching Records

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 2.1 | First load | Open Stitching Records page. | Table loads first page. Pagination shows correct total. Default filter "Undelivered Only" is applied (server sends `undelivered_only=true`). |
| 2.2 | Filter dropdowns | Open PL#, Serial#, Fabric, Customer dropdowns. | Options populated from filter-options API. Fabric Inv. may be empty (not in backend filter-options). |
| 2.3 | Apply filters | Set PL#, Serial#, Fabric, Customer, dates, Delivery Status. | Table refetches; results match filters; total updates. |
| 2.4 | Clear filters | Click Clear; ensure default "Undelivered Only" is restored if applicable. | Table refetches; default delivery status applied. |
| 2.5 | Pagination | Change page. | Correct page of results; pagination info correct. |
| 2.6 | Expand/collapse | Expand a parent row. | Child rows (garment/lining fabrics) render. No crash. |
| 2.7 | Refresh after action | Amend, delete, or create packing list; code calls `loadStitchingData(1, ...)`. | Table refreshes with current filters. |
| 2.8 | Selection | Select rows; use bulk action (e.g. Create Packing List). | Selection and actions work; after action, table refreshes. |

---

## 3. Packing Lists

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 3.1 | First load | Open Packing Lists page. | Table loads first page. Pagination and total correct. |
| 3.2 | Filter dropdowns | Open PL#, Cust. (and others if options exist). | PL# and Customer options from filter-options; others may be empty. |
| 3.3 | Apply filters | Set PL#, Serial#, Fabric, Customer, dates, Billing Status. | Table refetches; filtered results and total. |
| 3.4 | Clear filters | Click Clear Filter. | Filters reset; table refetches. |
| 3.5 | Pagination | Change page. | Correct page; "Showing X to Y of Z" correct. |
| 3.6 | Expand/collapse | Expand a packing list row. | Child rows (lines, secondary/lining) render. No crash. |
| 3.7 | Refresh | Click Refresh or trigger refresh after an action. | Table refetches with current filters (`refreshPackingListTable(1, ...)`). |
| 3.8 | Create group bill | Select packing lists; create group bill. | Flow completes; table can refresh. |

---

## 4. Group Bills

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 4.1 | First load | Open Group Bills page. | Group Bills view loads first page. Pagination and total correct. |
| 4.2 | Toggle view | Click "Show Commission Sales". | Commission Sales data loads (first page). Headers and table content match view. |
| 4.3 | Toggle back | Click "Show Group Bills". | Group Bills data loads again (first page). |
| 4.4 | Filter dropdowns | Open Customer (and Group Number, Fabric Inv., Fabric if present). | Customer options from filter-options. |
| 4.5 | Apply filters | Set Customer, dates. | Table refetches for current view (Group Bills or Commission Sales); total updates. |
| 4.6 | Pagination | Change page in Group Bills view; then switch to Commission Sales and change page. | Each view paginates independently; correct page and total for current view. |
| 4.7 | Expand group bill | Expand a group bill row. | Fabric/stitching summary and detail rows render. No crash. |
| 4.8 | Refresh after action | Delete group bill, delete commission sale, or download PDF; code calls `loadGroupBillsData(1, ...)`. | Table refreshes for current view with current filters. |
| 4.9 | Selection | Select group bills; download stitching/fabric PDF or delete. | Actions work; table refreshes after. |

---

## 5. Dashboard

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 5.1 | Unchanged | Open Dashboard; change date/customer/garment/location filters. | Dashboard still uses server-side filtering (unchanged). Charts and KPIs update. No regression. |

---

## 6. Cross-Cutting

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 6.1 | AbortController | On Fabric Invoices (or any list), change filters quickly several times. | Only the latest request is used; no stale data overwriting newer results. (Optional: check Network tab for cancelled requests.) |
| 6.2 | Empty state | Apply filters that match zero records. | Table shows "No data found" (or page-specific message); total 0; pagination disabled or shows 0 pages. |
| 6.3 | API contract | For any list page, in Network tab inspect response of list API (e.g. `/api/invoices?limit=50&offset=0`). | Response is `{ "items": [ ... ], "total": N }`. |
| 6.4 | Filter-options | Call e.g. `GET /api/invoices/filter-options` (with or without date params). | Returns JSON with keys such as `customers`, `invoice_numbers`, etc., and arrays of distinct values. |
| 6.5 | Multi-value | Send e.g. `customer=A,B` in list API. | Only rows matching customer A or B (or both) are returned (backend uses IN). |
| 6.6 | Navigation | Move between Fabric Invoices, Stitching, Packing Lists, Group Bills, Dashboard. | No console errors; each page loads its first page and filter options correctly. |

---

## 7. Regression (existing behaviour)

| # | Test | Steps | Expected |
|---|------|--------|----------|
| 7.1 | Login/theme/nav | Log in; toggle theme; use nav bar. | Login, theme, and navigation unchanged. |
| 7.2 | Create/Edit flows | On Fabric Invoices: add/edit invoice line. On Stitching: create record. On Packing Lists: create packing list. | Forms and submit work; table refreshes after save. |
| 7.3 | Bulk actions | Fabric Invoices: bulk assign location, tax invoice, delete. Stitching: bulk delete. Packing Lists: assign tax invoice. Group Bills: create from packing lists. | Bulk actions run and table refreshes. |
| 7.4 | PDF/export | Group Bills: download stitching/fabric PDF. Packing Lists: PDF if available. | PDFs download without error. |

---

## 8. Sign-off

- [ ] Fabric Invoices: all applicable tests above passed.
- [ ] Stitching Records: all applicable tests above passed.
- [ ] Packing Lists: all applicable tests above passed.
- [ ] Group Bills: all applicable tests above passed.
- [ ] Dashboard: no regression.
- [ ] Cross-cutting and regression checks passed.

**Date tested:** _______________  
**Tested by:** _______________  
**Notes:** _______________
