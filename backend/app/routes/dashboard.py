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
        
        # Calculate stitching revenue (full amount - you keep 100% of stitching)
        stitching_revenue = db.session.query(
            func.sum(StitchingInvoice.total_value).label('total')
        ).scalar() or 0
        
        # Total revenue (only stitching revenue - no fabric commission)
        total_revenue = float(stitching_revenue)
        
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
            'stitchingRevenue': float(stitching_revenue),
            'activeOrders': active_orders,
            'fabricStock': float(fabric_stock),
            'productionRate': round(production_rate, 1),
            'revenueChange': revenue_change,
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
        
        # Query for stitching revenue by group bill date
        stitching_query = text("""
            SELECT 
                DATE(si.created_at) as date,
                SUM(si.total_value) as stitching_revenue
            FROM stitching_invoices si
            WHERE si.created_at BETWEEN :date_from AND :date_to
            GROUP BY DATE(si.created_at)
            ORDER BY DATE(si.created_at)
        """)
        
        stitching_results = db.session.execute(stitching_query, {
            'date_from': date_from,
            'date_to': date_to
        }).fetchall()
        

        
        # Combine results
        dates = []
        stitching_revenue = []
        
        # Create date range
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        current_date = start_date
        
        stitching_dict = {str(row.date): float(row.stitching_revenue or 0) for row in stitching_results}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(current_date.strftime('%m/%d'))
            stitching_revenue.append(stitching_dict.get(date_str, 0))
            current_date += timedelta(days=1)
        
        return jsonify({
            'labels': dates,
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
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(
                    (SELECT SUM(si.total_value) 
                     FROM stitching_invoices si 
                     JOIN invoice_lines il2 ON si.invoice_line_id = il2.id
                     JOIN invoices i2 ON il2.invoice_id = i2.id
                     WHERE i2.customer_id = c.id
                     """ + (f"AND si.created_at >= '{date_from}'" if date_from else "") + """
                     """ + (f"AND si.created_at <= '{date_to}'" if date_to else "") + """
                    ), 0
                ) as stitching_revenue
            FROM customers c
            LEFT JOIN invoices i ON c.id = i.customer_id
            LEFT JOIN invoice_lines il ON i.id = il.invoice_id
            """ + (f"WHERE i.invoice_date >= '{date_from}'" if date_from else "") + """
            """ + (f"{'AND' if date_from else 'WHERE'} i.invoice_date <= '{date_to}'" if date_to else "") + """
            GROUP BY c.id, c.short_name
            HAVING (fabric_commission + stitching_revenue) > 0
            ORDER BY (fabric_commission + stitching_revenue) DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, {
            'commission_rate': FABRIC_COMMISSION_RATE
        }).fetchall()
        
        labels = [row.short_name for row in results]
        fabric_commission = [float(row.fabric_commission) for row in results]
        stitching_revenue = [float(row.stitching_revenue) for row in results]
        
        return jsonify({
            'labels': labels,
            'fabricCommission': fabric_commission,
            'stitchingRevenue': stitching_revenue
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/fabric-consumption', methods=['GET'])
def get_fabric_consumption():
    """Get fabric consumption by yards per garment per location"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        location = request.args.get('location')
        
        # Build location filter
        location_filter = ""
        if location:
            location_filter = f"AND si.delivery_location = '{location}'"
        
        query = text("""
            SELECT 
                il.item_name,
                SUM(COALESCE(il.yards_consumed, 0)) as total_yards,
                COUNT(DISTINCT si.id) as garment_count,
                CASE 
                    WHEN COUNT(DISTINCT si.id) > 0 
                    THEN SUM(COALESCE(il.yards_consumed, 0)) / COUNT(DISTINCT si.id)
                    ELSE 0 
                END as yards_per_garment
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            LEFT JOIN stitching_invoices si ON il.id = si.invoice_line_id
            WHERE COALESCE(il.yards_consumed, 0) > 0
            """ + (f"AND si.created_at >= '{date_from}'" if date_from else "") + """
            """ + (f"{'AND' if date_from else 'AND'} si.created_at <= '{date_to}'" if date_to else "") + """
            GROUP BY il.item_name
            HAVING garment_count > 0
            ORDER BY yards_per_garment DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query).fetchall()
        
        labels = [row.item_name for row in results]
        values = [float(row.yards_per_garment) for row in results]
        
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
            HAVING total_items > 0
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
    """Get fabric stock overview"""
    try:
        # Query for fabric stock by type
        query = text("""
            SELECT 
                il.item_name,
                SUM(yards_sent - COALESCE(yards_consumed, 0)) as pending_yards
            FROM invoice_lines il
            WHERE (yards_sent - COALESCE(yards_consumed, 0)) > 0
            GROUP BY il.item_name
            ORDER BY pending_yards DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query).fetchall()
        
        labels = [row.item_name for row in results]
        values = [float(row.pending_yards) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/production-rate', methods=['GET'])
def get_production_rate():
    """Get production rate over time"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        query = text("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as items_produced
            FROM stitching_invoices
            WHERE created_at BETWEEN :date_from AND :date_to
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)
        
        results = db.session.execute(query, {
            'date_from': date_from or (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'date_to': date_to or datetime.now().strftime('%Y-%m-%d')
        }).fetchall()
        
        dates = [row.date.strftime('%m/%d') for row in results]
        values = [int(row.items_produced) for row in results]
        
        return jsonify({
            'labels': dates,
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
