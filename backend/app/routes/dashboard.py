from flask import Blueprint, request, jsonify
from sqlalchemy import func, text
from datetime import datetime, timedelta
from extensions import db
from app.models.invoice import Invoice, InvoiceLine
from app.models.stitching import StitchingInvoice
from app.models.customer import Customer
from app.models.packing_list import PackingList, PackingListLine
from app.models.group_bill import StitchingInvoiceGroup

dashboard_bp = Blueprint('dashboard', __name__)

# Commission rate for fabric sales (5.1%)
FABRIC_COMMISSION_RATE = 0.051

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary data including KPIs"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Calculate fabric commission (based on packing list delivery dates)
        fabric_query = text(f"""
            SELECT 
                COALESCE(SUM(il.yards_sent * il.unit_price), 0) as fabric_sales_total,
                COALESCE(SUM(il.yards_sent * il.unit_price * {FABRIC_COMMISSION_RATE}), 0) as fabric_commission
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
        """)
        
        fabric_result = db.session.execute(fabric_query, params).fetchone()
        fabric_sales_total = float(fabric_result.fabric_sales_total or 0)
        fabric_commission = float(fabric_result.fabric_commission or 0)
        
        # Calculate stitching revenue (based on packing list delivery dates)
        stitching_query = text(f"""
            SELECT COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
        """)
        
        stitching_result = db.session.execute(stitching_query, params).fetchone()
        stitching_revenue = float(stitching_result.stitching_revenue or 0)
        
        # Total revenue
        total_revenue = fabric_commission + stitching_revenue
        
        # Active orders (count of unbilled stitching records)
        active_orders_query = text("""
            SELECT COUNT(*) as count
            FROM stitching_invoices si
            WHERE si.billing_group_id IS NULL
        """)
        active_orders_result = db.session.execute(active_orders_query).fetchone()
        active_orders = int(active_orders_result.count or 0)
        
        # Fabric stock (pending yards)
        fabric_stock_query = text("""
            SELECT COALESCE(SUM(il.yards_sent - COALESCE(il.yards_consumed, 0)), 0) as pending_yards
            FROM invoice_lines il
            WHERE (il.yards_sent - COALESCE(il.yards_consumed, 0)) > 0
        """)
        fabric_stock_result = db.session.execute(fabric_stock_query).fetchone()
        fabric_stock = float(fabric_stock_result.pending_yards or 0)
        
        # Production rate (total items per day - last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        production_query = text("""
            SELECT COALESCE(SUM(pl.total_items), 0) as total_items
            FROM packing_lists pl
            WHERE pl.delivery_date >= :thirty_days_ago
        """)
        production_result = db.session.execute(production_query, {
            'thirty_days_ago': thirty_days_ago
        }).fetchone()
        recent_production_count = int(production_result.total_items or 0)
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
    """Get revenue trends over time based on packing list delivery dates"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        # Build filter conditions
        where_conditions = []
        params = {
            'date_from': date_from,
            'date_to': date_to,
            'commission_rate': FABRIC_COMMISSION_RATE
        }
        
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Query for revenue by packing list delivery date
        query = text(f"""
            SELECT 
                DATE(pl.delivery_date) as date,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE pl.delivery_date BETWEEN :date_from AND :date_to
            AND {where_clause}
            GROUP BY DATE(pl.delivery_date)
            ORDER BY DATE(pl.delivery_date)
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        # Create date range
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        current_date = start_date
        
        dates = []
        fabric_commission = []
        stitching_revenue = []
        
        # Create dictionary for quick lookup
        data_dict = {}
        for row in results:
            date_str = str(row.date)
            fabric_comm = float(row.fabric_commission or 0)
            stitch_rev = float(row.stitching_revenue or 0)
            total = fabric_comm + stitch_rev
            
            data_dict[date_str] = {
                'fabric_commission': fabric_comm,
                'stitching_revenue': stitch_rev,
                'total': total
            }
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(current_date.strftime('%m/%d'))
            
            if date_str in data_dict:
                fabric_commission.append(data_dict[date_str]['fabric_commission'])
                stitching_revenue.append(data_dict[date_str]['stitching_revenue'])
            else:
                fabric_commission.append(0)
                stitching_revenue.append(0)
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'labels': dates,
            'fabricSales': fabric_commission,
            'stitchingRevenue': stitching_revenue
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/top-customers', methods=['GET'])
def get_top_customers():
    """Get top customers by revenue with split commission/stitching based on delivery dates"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {'commission_rate': FABRIC_COMMISSION_RATE}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
            GROUP BY c.id, c.short_name
            HAVING (fabric_commission + stitching_revenue) > 0
            ORDER BY (fabric_commission + stitching_revenue) DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, params).fetchall()
        
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
    """Get fabric consumption by garment type (total yards / total quantity)"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                si.stitched_item,
                SUM(COALESCE(si.yard_consumed, 0)) as total_yards,
                SUM(
                    CASE 
                        WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                        THEN JSON_LENGTH(si.size_qty_json)
                        ELSE 0 
                    END
                ) as total_quantity,
                CASE 
                    WHEN SUM(
                        CASE 
                            WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                            THEN JSON_LENGTH(si.size_qty_json)
                            ELSE 0 
                        END
                    ) > 0 
                    THEN SUM(COALESCE(si.yard_consumed, 0)) / SUM(
                        CASE 
                            WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                            THEN JSON_LENGTH(si.size_qty_json)
                            ELSE 0 
                        END
                    )
                    ELSE 0 
                END as yards_per_item
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE COALESCE(si.yard_consumed, 0) > 0
            AND {where_clause}
            GROUP BY si.stitched_item
            HAVING total_quantity > 0
            ORDER BY yards_per_item DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        labels = [row.stitched_item for row in results]
        values = [float(row.yards_per_item) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/production-overview', methods=['GET'])
def get_production_overview():
    """Get most stitched items by total quantity based on delivery dates"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                si.stitched_item,
                SUM(
                    CASE 
                        WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                        THEN JSON_LENGTH(si.size_qty_json)
                        ELSE 0 
                    END
                ) as total_quantity
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
            GROUP BY si.stitched_item
            HAVING total_quantity > 0
            ORDER BY total_quantity DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        labels = [row.stitched_item for row in results]
        values = [int(row.total_quantity) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/stock-status', methods=['GET'])
def get_stock_status():
    """Get fabric stock overview by location"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {}
        
        if date_from:
            where_conditions.append("i.invoice_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("i.invoice_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                COALESCE(il.delivered_location, 'Unknown') as location,
                SUM(il.yards_sent - COALESCE(il.yards_consumed, 0)) as pending_yards
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE (il.yards_sent - COALESCE(il.yards_consumed, 0)) > 0
            AND {where_clause}
            GROUP BY il.delivered_location
            ORDER BY pending_yards DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        labels = [row.location for row in results]
        values = [float(row.pending_yards) for row in results]
        
        return jsonify({
            'labels': labels,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/production-rate', methods=['GET'])
def get_production_rate():
    """Get production rate over time based on delivery dates (total quantity per day)"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        # Build filter conditions
        where_conditions = []
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                DATE(pl.delivery_date) as date,
                SUM(
                    CASE 
                        WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                        THEN JSON_LENGTH(si.size_qty_json)
                        ELSE 0 
                    END
                ) as items_produced
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE pl.delivery_date BETWEEN :date_from AND :date_to
            AND {where_clause}
            GROUP BY DATE(pl.delivery_date)
            ORDER BY DATE(pl.delivery_date)
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        # Create date range
        start_date = datetime.strptime(date_from, '%Y-%m-%d')
        end_date = datetime.strptime(date_to, '%Y-%m-%d')
        current_date = start_date
        
        dates = []
        values = []
        
        # Create dictionary for quick lookup
        data_dict = {str(row.date): int(row.items_produced) for row in results}
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            dates.append(current_date.strftime('%m/%d'))
            values.append(data_dict.get(date_str, 0))
            current_date += timedelta(days=1)
        
        return jsonify({
            'labels': dates,
            'values': values
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/earnings-breakdown', methods=['GET'])
def get_earnings_breakdown():
    """Get earnings breakdown pie chart (fabric commission vs stitching revenue)"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {'commission_rate': FABRIC_COMMISSION_RATE}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
        """)
        
        result = db.session.execute(query, params).fetchone()
        fabric_commission = float(result.fabric_commission or 0)
        stitching_revenue = float(result.stitching_revenue or 0)
        total = fabric_commission + stitching_revenue
        
        # Calculate percentages
        fabric_percentage = (fabric_commission / total * 100) if total > 0 else 0
        stitching_percentage = (stitching_revenue / total * 100) if total > 0 else 0
        
        return jsonify({
            'labels': ['Fabric Commission', 'Stitching Revenue'],
            'values': [fabric_commission, stitching_revenue],
            'percentages': [round(fabric_percentage, 1), round(stitching_percentage, 1)]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/earnings-by-customer', methods=['GET'])
def get_earnings_by_customer():
    """Get earnings breakdown by customer pie chart"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions
        where_conditions = []
        params = {'commission_rate': FABRIC_COMMISSION_RATE}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        if customer:
            where_conditions.append("c.short_name = :customer")
            params['customer'] = customer
        if garment:
            where_conditions.append("si.stitched_item = :garment")
            params['garment'] = garment
        if location:
            where_conditions.append("il.delivered_location = :location")
            params['location'] = location
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
            GROUP BY c.id, c.short_name
            HAVING (COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) + COALESCE(SUM(si.total_value), 0)) > 0
            ORDER BY (COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) + COALESCE(SUM(si.total_value), 0)) DESC
            LIMIT 10
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        labels = [row.short_name for row in results]
        values = []
        for row in results:
            fabric_comm = float(row.fabric_commission or 0)
            stitch_rev = float(row.stitching_revenue or 0)
            values.append(fabric_comm + stitch_rev)
        
        # Calculate percentages
        total = sum(values)
        percentages = [(value / total * 100) if total > 0 else 0 for value in values]
        
        return jsonify({
            'labels': labels,
            'values': values,
            'percentages': [round(p, 1) for p in percentages]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/test', methods=['GET'])
def test_dashboard():
    """Test endpoint for dashboard"""
    return jsonify({'message': 'Dashboard API is working!'}), 200
