from flask import Blueprint, request, jsonify
from sqlalchemy import func, text
from datetime import datetime, timedelta
from extensions import db
from app.models.invoice import Invoice, InvoiceLine
from app.models.stitching import StitchingInvoice
from app.models.customer import Customer
from app.models.packing_list import PackingList

dashboard_bp = Blueprint('dashboard', __name__)

# Commission rate for fabric sales (5.1%)
FABRIC_COMMISSION_RATE = 0.051

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary data including KPIs"""
    try:
        # Simple queries to start with
        
        # Calculate fabric sales (total invoice value)
        fabric_sales_total = db.session.query(
            func.sum(InvoiceLine.yards_sent * InvoiceLine.unit_price).label('total')
        ).scalar() or 0
        
        # Calculate fabric commission (5.1% of fabric sales)
        fabric_commission = float(fabric_sales_total) * FABRIC_COMMISSION_RATE
        
        # Calculate stitching revenue (full amount - you keep 100% of stitching)
        stitching_revenue = db.session.query(
            func.sum(StitchingInvoice.total_value).label('total')
        ).scalar() or 0
        
        # Total revenue (commission + full stitching revenue)
        total_revenue = fabric_commission + float(stitching_revenue)
        
        # Active orders (count of stitching records)
        active_orders = db.session.query(StitchingInvoice).count()
        
        # Fabric stock (pending yards)
        fabric_stock = db.session.query(
            func.sum(InvoiceLine.yards_sent - func.coalesce(InvoiceLine.yards_consumed, 0)).label('pending')
        ).filter(InvoiceLine.yards_sent > func.coalesce(InvoiceLine.yards_consumed, 0)).scalar() or 0
        
        # Production rate (records per day - last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_production_count = db.session.query(StitchingInvoice).filter(
            StitchingInvoice.created_at >= thirty_days_ago
        ).count()
        
        production_rate = recent_production_count / 30 if recent_production_count > 0 else 0
        
        # Calculate percentage changes (mock data for now)
        revenue_change = 12.5  # Mock positive growth
        fabric_change = 8.3    # Mock positive growth
        stitching_change = 15.7  # Mock positive growth
        
        return jsonify({
            'totalRevenue': float(total_revenue),
            'fabricSales': float(fabric_commission),  # Show commission amount
            'fabricSalesTotal': float(fabric_sales_total),  # Show total fabric sales for reference
            'stitchingRevenue': float(stitching_revenue),
            'activeOrders': active_orders,
            'fabricStock': float(fabric_stock),
            'productionRate': round(production_rate, 1),
            'revenueChange': revenue_change,
            'fabricChange': fabric_change,
            'stitchingChange': stitching_change
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/revenue-trends', methods=['GET'])
def get_revenue_trends():
    """Get revenue trends over time"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        # Query for fabric sales by date (with commission calculation)
        fabric_query = text("""
            SELECT 
                DATE(i.invoice_date) as date,
                SUM(il.yards_sent * il.unit_price) as fabric_sales_total,
                SUM(il.yards_sent * il.unit_price * :commission_rate) as fabric_commission
            FROM invoices i
            JOIN invoice_lines il ON i.id = il.invoice_id
            WHERE i.invoice_date BETWEEN :date_from AND :date_to
            GROUP BY DATE(i.invoice_date)
            ORDER BY DATE(i.invoice_date)
        """)
        
        fabric_results = db.session.execute(fabric_query, {
            'date_from': date_from, 
            'date_to': date_to,
            'commission_rate': FABRIC_COMMISSION_RATE
        }).fetchall()
        
        # Query for stitching revenue by date
        stitching_query = text("""
            SELECT 
                DATE(created_at) as date,
                SUM(total_value) as stitching_revenue
            FROM stitching_invoices
            WHERE created_at BETWEEN :date_from AND :date_to
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)
        
        stitching_results = db.session.execute(stitching_query, {
            'date_from': date_from,
            'date_to': date_to
        }).fetchall()
        
        # Combine results
        dates = []
        fabric_commission = []
        stitching_revenue = []
        
        # Create date range
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        current_date = start_date
        
        fabric_dict = {str(row.date): float(row.fabric_commission or 0) for row in fabric_results}
        stitching_dict = {str(row.date): float(row.stitching_revenue or 0) for row in stitching_results}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(current_date.strftime('%m/%d'))
            fabric_commission.append(fabric_dict.get(date_str, 0))
            stitching_revenue.append(stitching_dict.get(date_str, 0))
            current_date += timedelta(days=1)
        
        return jsonify({
            'labels': dates,
            'fabricSales': fabric_commission,  # Now shows commission amount
            'stitchingRevenue': stitching_revenue
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-customers', methods=['GET'])
def get_top_customers():
    """Get top customers by revenue"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        query = text("""
            SELECT 
                c.short_name,
                (
                    COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) + 
                    COALESCE(
                        (SELECT SUM(si.total_value) 
                         FROM stitching_invoices si 
                         JOIN invoice_lines il2 ON si.invoice_line_id = il2.id
                         JOIN invoices i2 ON il2.invoice_id = i2.id
                         WHERE i2.customer_id = c.id
                         """ + (f"AND si.created_at >= '{date_from}'" if date_from else "") + """
                         """ + (f"AND si.created_at <= '{date_to}'" if date_to else "") + """
                        ), 0
                    )
                ) as total_revenue
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            LEFT JOIN invoice_lines il ON i.id = il.invoice_id
            """ + (f"WHERE i.invoice_date >= '{date_from}'" if date_from else "") + """
            """ + (f"{'AND' if date_from else 'WHERE'} i.invoice_date <= '{date_to}'" if date_to else "") + """
            GROUP BY c.id, c.short_name
            HAVING total_revenue > 0
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, {
            'commission_rate': FABRIC_COMMISSION_RATE
        }).fetchall()
        
        labels = [row.short_name for row in results]
        values = [float(row.total_revenue) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/fabric-consumption', methods=['GET'])
def get_fabric_consumption():
    """Get fabric consumption by type"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        query = text("""
            SELECT 
                il.item_name,
                SUM(COALESCE(il.yards_consumed, 0)) as consumed
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            WHERE COALESCE(il.yards_consumed, 0) > 0
            """ + (f"AND i.invoice_date >= '{date_from}'" if date_from else "") + """
            """ + (f"AND i.invoice_date <= '{date_to}'" if date_to else "") + """
            GROUP BY il.item_name
            ORDER BY consumed DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query).fetchall()
        
        labels = [row.item_name for row in results]
        values = [float(row.consumed) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/production-overview', methods=['GET'])
def get_production_overview():
    """Get production overview by stitched items"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        garment = request.args.get('garment')
        
        query_conditions = []
        if date_from:
            query_conditions.append(f"created_at >= '{date_from}'")
        if date_to:
            query_conditions.append(f"created_at <= '{date_to}'")
        if garment:
            query_conditions.append(f"stitched_item LIKE '%{garment}%'")
        
        where_clause = "WHERE " + " AND ".join(query_conditions) if query_conditions else ""
        
        query = text(f"""
            SELECT 
                stitched_item,
                COUNT(*) as total_items
            FROM stitching_invoices
            {where_clause}
            GROUP BY stitched_item
            ORDER BY total_items DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query).fetchall()
        
        labels = [row.stitched_item for row in results]
        values = [int(row.total_items) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/stock-status', methods=['GET'])
def get_stock_status():
    """Get stock status overview"""
    try:
        # Query for stock status
        query = text("""
            SELECT 
                CASE 
                    WHEN (yards_sent - COALESCE(yards_consumed, 0)) > 100 THEN 'High Stock'
                    WHEN (yards_sent - COALESCE(yards_consumed, 0)) BETWEEN 20 AND 100 THEN 'Medium Stock'
                    WHEN (yards_sent - COALESCE(yards_consumed, 0)) BETWEEN 1 AND 19 THEN 'Low Stock'
                    ELSE 'Out of Stock'
                END as stock_level,
                COUNT(*) as count
            FROM invoice_lines
            WHERE yards_sent > 0
            GROUP BY stock_level
        """)
        
        results = db.session.execute(query).fetchall()
        
        labels = [row.stock_level for row in results]
        values = [int(row.count) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/test', methods=['GET'])
def test_dashboard():
    """Test endpoint for dashboard API"""
    return jsonify({
        'message': 'Dashboard API is working',
        'status': 'ok'
    }), 200

@dashboard_bp.route('/simple-test', methods=['GET'])
def simple_test():
    """Simple test to check basic queries"""
    try:
        # Test basic counts
        invoice_count = db.session.query(InvoiceLine).count()
        stitching_count = db.session.query(StitchingInvoice).count()
        
        return jsonify({
            'invoiceLines': invoice_count,
            'stitchingRecords': stitching_count,
            'message': 'Simple queries working'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
