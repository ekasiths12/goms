/**
 * Fabric Invoice Row Template - Custom template for fabric invoice table rows
 * Includes action buttons, status displays, and proper formatting
 */
class FabricInvoiceRowTemplate {
    constructor() {
        this.template = this.createTemplate.bind(this);
    }
    
    /**
     * Create row template for fabric invoice
     */
    createTemplate(item, index) {
        // Calculate values like the original code
        const yardsSent = item.yards_sent || item.quantity || 0;
        const yardsConsumed = item.yards_consumed || 0;
        const commissionYards = item.total_commission_yards || 0;
        const totalUsed = (yardsConsumed + commissionYards);
        const pending = yardsSent - totalUsed;
        const displayTotalUsed = item.total_used || totalUsed;
        
        // Create status display and action buttons
        const statusDisplay = this.createStatusDisplay(item);
        const actionButtons = this.createActionButtons(item, pending);
        const finalActionButtons = statusDisplay + actionButtons;
        
        return `
            <td class="checkbox-wrapper">
                <input type="checkbox" class="row-checkbox" data-id="${item.id}" onclick="toggleInvoiceSelection(event, ${item.id})">
            </td>
            <td data-field="date">${this.formatDate(item.invoice_date)}</td>
            <td data-field="short_name">${item.customer?.short_name || ''}</td>
            <td data-field="invoice_number">${item.invoice_number || ''}</td>
            <td data-field="tax_invoice_number">${item.tax_invoice_number || ''}</td>
            <td data-field="item_name">${item.item_name || ''}</td>
            <td data-field="color">${item.color || ''}</td>
            <td data-field="delivery_note">${item.delivery_note || ''}</td>
            <td data-field="yards_sent">${this.formatNumber(yardsSent)}</td>
            <td data-field="total_used">${this.formatNumber(displayTotalUsed)}</td>
            <td data-field="pending">${this.formatNumber(pending)}</td>
            <td data-field="unit_price">${this.formatNumber(item.unit_price || 0)}</td>
            <td data-field="total">${this.formatNumber(yardsSent * (item.unit_price || 0))}</td>
            <td data-field="delivered_location">${item.delivered_location || ''}</td>
            <td>${finalActionButtons}</td>
            <td style="display: none;">${item.id || ''}</td>
        `;
    }
    
    /**
     * Create status display for the row
     */
    createStatusDisplay(item) {
        const yardsConsumed = item.yards_consumed || 0;
        const commissionYards = item.total_commission_yards || 0;
        
        const statusParts = [];
        
        if (item.commission_sales_count > 0) {
            statusParts.push(`✓ Commission (${this.formatNumber(commissionYards)} yards)`);
        }
        
        if (yardsConsumed > 0) {
            statusParts.push(`✓ Stitched (${this.formatNumber(yardsConsumed)} yards)`);
        }
        
        if (statusParts.length > 0) {
            const formattedParts = statusParts.map(part => {
                if (part.includes('Commission')) {
                    return `<span style="color: #f57c00;">${part}</span>`;
                } else {
                    return `<span style="color: #2E7D32;">${part}</span>`;
                }
            });
            
            return `<div style="font-size: 10px; font-weight: bold; margin-bottom: 3px;">
                ${formattedParts.join(' | ')}
            </div>`;
        }
        
        return '';
    }
    
    /**
     * Create action buttons for the row
     */
    createActionButtons(item, pending) {
        const yardsSent = item.yards_sent || item.quantity || 0;
        const yardsConsumed = item.yards_consumed || 0;
        const commissionYards = item.total_commission_yards || 0;
        const totalUsed = (yardsConsumed + commissionYards);
        
        // Show action buttons if there are pending yards
        if (yardsSent > totalUsed) {
            const commissionButton = `
                <button onclick="openCommissionSaleDialog(${item.id}, ${pending}, '${item.item_name}', '${item.color || ''}')" 
                        class="btn btn-warning" style="padding: 4px 8px; font-size: 11px; margin-right: 5px;">
                    Commission
                </button>
            `;
            
            const stitchingButton = `
                <button onclick="createStitchingRecordFromTable(${item.id})" 
                        class="btn btn-success" style="padding: 4px 8px; font-size: 11px;">
                    Stitching
                </button>
            `;
            
            return commissionButton + stitchingButton;
        }
        
        return '';
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
     * Update row in UI when data changes
     */
    updateRowInUI(rowElement, updates) {
        // Update specific cells based on updates
        Object.keys(updates).forEach(key => {
            const cell = rowElement.querySelector(`[data-field="${key}"]`);
            if (cell) {
                let newValue = '';
                
                switch (key) {
                    case 'date':
                    case 'invoice_date':
                        newValue = this.formatDate(updates[key]);
                        break;
                    case 'unit_price':
                    case 'price':
                    case 'total':
                    case 'cost':
                    case 'yards_sent':
                    case 'yards_consumed':
                    case 'total_used':
                    case 'pending':
                    case 'quantity':
                        newValue = this.formatNumber(updates[key]);
                        break;
                    default:
                        newValue = String(updates[key] || '');
                }
                
                cell.innerHTML = newValue;
            }
        });
        
        // Update action buttons if needed
        if (updates.delivered_location !== undefined || updates.pending_yards !== undefined) {
            this.updateActionButtons(rowElement, updates);
        }
    }
    
    /**
     * Update action buttons when data changes
     */
    updateActionButtons(rowElement, updates) {
        const item = this.getRowData(rowElement);
        if (!item) return;
        
        // Recalculate pending yards
        const yardsSent = item.yards_sent || item.quantity || 0;
        const yardsConsumed = item.yards_consumed || 0;
        const commissionYards = item.total_commission_yards || 0;
        const totalUsed = (yardsConsumed + commissionYards);
        const pending = yardsSent - totalUsed;
        
        // Update the action buttons cell
        const actionCell = rowElement.querySelector('td:last-child');
        if (actionCell) {
            const statusDisplay = this.createStatusDisplay(item);
            const actionButtons = this.createActionButtons(item, pending);
            actionCell.innerHTML = statusDisplay + actionButtons;
        }
    }
    
    /**
     * Get row data from DOM element
     */
    getRowData(rowElement) {
        const rowId = rowElement.getAttribute('data-row-id');
        if (!rowId) return null;
        
        // Try to get data from global invoiceData array
        if (typeof invoiceData !== 'undefined' && Array.isArray(invoiceData)) {
            return invoiceData.find(item => item.id == rowId);
        }
        
        // Fallback: reconstruct from DOM cells
        const cells = rowElement.querySelectorAll('td[data-field]');
        const data = { id: rowId };
        
        cells.forEach(cell => {
            const field = cell.getAttribute('data-field');
            const value = cell.textContent.trim();
            
            switch (field) {
                case 'date':
                case 'invoice_date':
                    data.invoice_date = value;
                    break;
                case 'unit_price':
                case 'price':
                    data.unit_price = parseFloat(value.replace(/,/g, '')) || 0;
                    break;
                case 'yards_sent':
                    data.yards_sent = parseFloat(value.replace(/,/g, '')) || 0;
                    break;
                case 'total_used':
                    data.total_used = parseFloat(value.replace(/,/g, '')) || 0;
                    break;
                case 'pending':
                    data.pending_yards = parseFloat(value.replace(/,/g, '')) || 0;
                    break;
                default:
                    data[field] = value;
            }
        });
        
        return data;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FabricInvoiceRowTemplate;
}
