/**
 * Action Manager - Handles optimistic updates for fabric invoice operations
 * Provides immediate UI feedback while performing server operations in background
 */
class ActionManager {
    constructor(tableManager, options = {}) {
        this.tableManager = tableManager;
        this.apiBaseUrl = options.apiBaseUrl || this.getApiBaseUrl();
        this.showNotifications = options.showNotifications !== false;
        this.optimisticUpdates = options.optimisticUpdates !== false;
        
        // Track pending operations
        this.pendingOperations = new Map();
        this.operationCounter = 0;
        
        console.log('✅ ActionManager initialized');
    }
    
    /**
     * Assign delivery location to selected rows
     */
    async assignDeliveryLocation(selectedRowIds, location) {
        if (!selectedRowIds || selectedRowIds.length === 0) {
            this.showNotification('Please select one or more invoice lines.', 'warning');
            return false;
        }
        
        if (!location) {
            this.showNotification('Please select a location.', 'warning');
            return false;
        }
        
        const operationId = this.generateOperationId();
        
        // Optimistic update
        if (this.optimisticUpdates) {
            this.tableManager.updateRows(selectedRowIds, { delivered_location: location });
            this.showNotification(`Assigning location "${location}" to ${selectedRowIds.length} line(s)...`, 'info');
        }
        
        try {
            // Get the selected lines data
            const selectedLines = selectedRowIds.map(rowId => {
                const row = this.tableManager.getRowById(rowId);
                return {
                    invoice_number: row.invoice_number,
                    item_name: row.item_name,
                    color: row.color
                };
            });
            
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/assign-location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    lines: selectedLines,
                    location: location
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message || `Location assigned successfully to ${selectedRowIds.length} line(s)`, 'success');
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to assign location', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error assigning location:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error assigning location: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Remove delivery location from selected rows
     */
    async removeDeliveryLocation(selectedRowIds) {
        if (!selectedRowIds || selectedRowIds.length === 0) {
            this.showNotification('Please select one or more invoice lines.', 'warning');
            return false;
        }
        
        const operationId = this.generateOperationId();
        
        // Optimistic update
        if (this.optimisticUpdates) {
            this.tableManager.updateRows(selectedRowIds, { delivered_location: '' });
            this.showNotification(`Removing location from ${selectedRowIds.length} line(s)...`, 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/remove-location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    line_ids: selectedRowIds
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message || `Location removed from ${selectedRowIds.length} line(s)`, 'success');
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to remove location', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error removing location:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error removing location: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Assign tax invoice number
     */
    async assignTaxInvoiceNumber(selectedRowIds, taxInvoiceNumber) {
        if (!selectedRowIds || selectedRowIds.length === 0) {
            this.showNotification('Please select one or more invoice lines.', 'warning');
            return false;
        }
        
        if (!taxInvoiceNumber) {
            this.showNotification('Please enter a tax invoice number.', 'warning');
            return false;
        }
        
        // Get unique base invoice numbers from selected rows
        const baseInvoiceNumbers = new Set();
        selectedRowIds.forEach(rowId => {
            const row = this.tableManager.getRowById(rowId);
            const invoiceNumber = row.invoice_number;
            let baseInvoiceNumber = invoiceNumber;
            if (invoiceNumber.includes('-')) {
                baseInvoiceNumber = invoiceNumber.split('-')[0];
            }
            baseInvoiceNumbers.add(baseInvoiceNumber);
        });
        
        // For now, use the first base invoice number
        const baseInvoiceNumber = Array.from(baseInvoiceNumbers)[0];
        
        // Optimistic update
        if (this.optimisticUpdates) {
            this.tableManager.updateRows(selectedRowIds, { tax_invoice_number: taxInvoiceNumber });
            this.showNotification(`Assigning tax invoice number "${taxInvoiceNumber}"...`, 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/assign-tax-invoice`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    base_invoice_number: baseInvoiceNumber,
                    tax_invoice_number: taxInvoiceNumber.trim()
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message || 'Tax invoice number assigned successfully', 'success');
                
                // Refresh table data to show all affected lines with the new tax invoice number
                console.log('🔄 Tax invoice assigned successfully, refreshing table data');
                await this.refreshTableData();
                
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to assign tax invoice number', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error assigning tax invoice number:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error assigning tax invoice number: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Create commission sale
     */
    async createCommissionSale(lineId, yardsSold, saleDate) {
        const row = this.tableManager.getRowById(lineId);
        if (!row) {
            this.showNotification('Invoice line not found', 'error');
            return false;
        }
        
        const availableYards = row.pending_yards || 0;
        if (yardsSold > availableYards) {
            this.showNotification(`Cannot sell ${yardsSold} yards, only ${availableYards} yards available`, 'error');
            return false;
        }
        
        // Optimistic update - update pending yards
        if (this.optimisticUpdates) {
            const newPending = availableYards - yardsSold;
            this.tableManager.updateRow(lineId, { pending_yards: newPending });
            this.showNotification(`Creating commission sale for ${yardsSold} yards...`, 'info');
            
            // If pending yards becomes 0, the line should move to "no stock" filter
            // We need to refresh the table data to update the stock status
            if (newPending === 0) {
                console.log('🔄 Pending yards is 0, refreshing table data to update stock status');
                // Small delay to ensure the optimistic update is applied first
                setTimeout(() => {
                    this.refreshTableData();
                }, 100);
            }
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/mark-commission-sale`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    line_id: lineId,
                    yards_sold: yardsSold,
                    sale_date: saleDate
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(`Successfully marked ${yardsSold} yards as commission sale. Commission: ฿${this.formatNumber(result.commission_amount)}`, 'success');
                
                // If pending yards is 0, refresh table data to update stock status
                if (availableYards - yardsSold === 0) {
                    console.log('🔄 Commission sale completed with 0 pending yards, refreshing table data');
                    await this.refreshTableData();
                }
                
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to create commission sale', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error creating commission sale:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error creating commission sale: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Create bulk commission sales
     */
    async createBulkCommissionSale(lines, saleDate) {
        if (!lines || lines.length === 0) {
            this.showNotification('No lines provided for bulk commission sale', 'warning');
            return false;
        }
        
        // Validate all lines first
        const validatedLines = [];
        for (const line of lines) {
            const row = this.tableManager.getRowById(line.line_id);
            if (!row) {
                this.showNotification(`Invoice line ${line.line_id} not found`, 'error');
                return false;
            }
            
            const availableYards = row.pending_yards || 0;
            if (line.yards_sold > availableYards) {
                this.showNotification(`Line ${line.line_id}: Cannot sell ${line.yards_sold} yards, only ${availableYards} yards available`, 'error');
                return false;
            }
            
            validatedLines.push({ ...line, availableYards });
        }
        
        // Optimistic updates for all lines
        if (this.optimisticUpdates) {
            for (const line of validatedLines) {
                const newPending = line.availableYards - line.yards_sold;
                this.tableManager.updateRow(line.line_id, { pending_yards: newPending });
            }
            this.showNotification(`Creating ${validatedLines.length} commission sales...`, 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/mark-commission-sale-bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sale_date: saleDate,
                    lines: lines
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(
                    `Successfully created ${result.commission_sales.length} commission sales. Total commission: ฿${this.formatNumber(result.total_commission)}`, 
                    'success'
                );
                
                // Refresh table data to ensure all updates are reflected
                await this.refreshTableData();
                
                return true;
            } else {
                // Revert optimistic updates on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to create bulk commission sales', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error creating bulk commission sales:', error);
            
            // Revert optimistic updates on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error creating bulk commission sales: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Delete selected invoice lines
     */
    async deleteInvoiceLines(selectedRowIds) {
        if (!selectedRowIds || selectedRowIds.length === 0) {
            this.showNotification('Please select at least one invoice to delete.', 'warning');
            return false;
        }
        
        // Optimistic update
        if (this.optimisticUpdates) {
            this.tableManager.removeRows(selectedRowIds);
            this.showNotification(`Deleting ${selectedRowIds.length} invoice line(s)...`, 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/delete-multiple`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    line_ids: selectedRowIds
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification(result.message || `Successfully deleted ${selectedRowIds.length} invoice line(s)`, 'success');
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to delete invoice lines', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error deleting invoice lines:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error deleting invoice lines: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Update invoice line
     */
    async updateInvoiceLine(lineId, updates) {
        const row = this.tableManager.getRowById(lineId);
        if (!row) {
            this.showNotification('Invoice line not found', 'error');
            return false;
        }
        
        // Optimistic update
        if (this.optimisticUpdates) {
            this.tableManager.updateRow(lineId, updates);
            this.showNotification('Updating invoice line...', 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices/${lineId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Invoice line updated successfully', 'success');
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification(result.error || 'Failed to update invoice line', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error updating invoice line:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error updating invoice line: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Add new invoice line
     */
    async addInvoiceLine(invoiceData) {
        // Optimistic update - add to top of table
        if (this.optimisticUpdates) {
            const newRow = {
                id: 'temp_' + Date.now(), // Temporary ID
                ...invoiceData,
                invoice_date: new Date().toISOString().split('T')[0]
            };
            this.tableManager.addRow(newRow);
            this.showNotification('Adding new invoice line...', 'info');
        }
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(invoiceData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showNotification('Invoice line added successfully!', 'success');
                
                // Refresh to get the real ID from server
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                
                return true;
            } else {
                // Revert optimistic update on error
                if (this.optimisticUpdates) {
                    await this.refreshTableData();
                }
                this.showNotification('Failed to add invoice line. Please check the data and try again.', 'error');
                return false;
            }
        } catch (error) {
            console.error('Error adding invoice line:', error);
            
            // Revert optimistic update on error
            if (this.optimisticUpdates) {
                await this.refreshTableData();
            }
            
            this.showNotification('Error adding invoice line: ' + error.message, 'error');
            return false;
        }
    }
    
    /**
     * Refresh table data from server
     */
    async refreshTableData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/invoices`);
            if (response.ok) {
                const data = await response.json();
                this.tableManager.setData(data);
                return true;
            } else {
                console.error('Failed to refresh table data');
                return false;
            }
        } catch (error) {
            console.error('Error refreshing table data:', error);
            return false;
        }
    }
    
    /**
     * Generate unique operation ID
     */
    generateOperationId() {
        return `op_${Date.now()}_${++this.operationCounter}`;
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        if (!this.showNotifications) return;
        
        // Use existing showNotification function if available
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            // Fallback notification
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
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
     * Get API base URL
     */
    getApiBaseUrl() {
        const hostname = window.location.hostname;
        const port = window.location.port;
        const protocol = window.location.protocol;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000';
        }
        
        if (hostname.includes('railway.app') || hostname.includes('up.railway.app')) {
            return `https://${hostname}`;
        }
        
        const origin = window.location.origin;
        if (protocol === 'https:') {
            return origin;
        } else {
            return origin.replace('http://', 'https://');
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActionManager;
}
