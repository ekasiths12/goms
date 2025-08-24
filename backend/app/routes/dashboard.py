from flask import Blueprint, request, jsonify
from sqlalchemy import func, text
from datetime import datetime, timedelta
from extensions import db

def add_filter_condition(where_conditions, params, field_name, filter_value, param_prefix, operator="="):
    """Helper function to add filter conditions for single or multiple values"""
    if filter_value:
        if operator in [">=", "<=", ">", "<"]:
            # Handle date range operators
            where_conditions.append(f"{field_name} {operator} :{param_prefix}")
            params[param_prefix] = filter_value
        elif ',' in filter_value:
            # Handle multiple values
            value_list = [v.strip() for v in filter_value.split(',')]
            placeholders = ','.join([f':{param_prefix}_{i}' for i in range(len(value_list))])
            where_conditions.append(f"{field_name} IN ({placeholders})")
            for i, val in enumerate(value_list):
                params[f'{param_prefix}_{i}'] = val
        else:
            # Handle single value
            where_conditions.append(f"{field_name} = :{param_prefix}")
            params[param_prefix] = filter_value
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
        
        # Calculate direct commission sales (commission sales not from stitching)
        commission_conditions = ["il.is_commission_sale = TRUE"]
        commission_params = {}
        
        if date_from:
            commission_conditions.append("il.commission_date >= :date_from")
            commission_params['date_from'] = date_from
        if date_to:
            commission_conditions.append("il.commission_date <= :date_to")
            commission_params['date_to'] = date_to
        if customer:
            commission_conditions.append("c.short_name = :customer")
            commission_params['customer'] = customer
            
        commission_where = " AND ".join(commission_conditions)
        
        commission_sales_query = text(f"""
            SELECT 
                COALESCE(SUM(il.commission_yards * il.unit_price), 0) as direct_sales_total,
                COALESCE(SUM(il.commission_amount), 0) as direct_commission
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE {commission_where}
        """)
        commission_result = db.session.execute(commission_sales_query, commission_params).fetchone()
        direct_sales_total = float(commission_result.direct_sales_total or 0)
        direct_commission = float(commission_result.direct_commission or 0)
        
        # Calculate stitching revenue (based on packing list delivery dates)
        stitching_query = text(f"""
            SELECT COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM packing_lists pl
            JOIN packing_list_lines pll ON pl.id = pll.packing_list_id
            JOIN stitching_invoices si ON pll.stitching_invoice_id = si.id
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN customers c ON pl.customer_id = c.id
            WHERE {where_clause}
        """)
        
        stitching_result = db.session.execute(stitching_query, params).fetchone()
        stitching_revenue = float(stitching_result.stitching_revenue or 0)
        
        # Total revenue (including direct commission sales)
        total_revenue = fabric_commission + stitching_revenue + direct_commission
        
        # Active orders (count of all stitching records based on packing list delivery date)
        active_orders_conditions = ["1=1"]  # Always true, so we count all records
        active_orders_params = {}
        
        if date_from:
            active_orders_conditions.append("pl.delivery_date >= :date_from")
            active_orders_params['date_from'] = date_from
        if date_to:
            active_orders_conditions.append("pl.delivery_date <= :date_to")
            active_orders_params['date_to'] = date_to
        if customer:
            active_orders_conditions.append("c.short_name = :customer")
            active_orders_params['customer'] = customer
        if garment:
            active_orders_conditions.append("si.stitched_item = :garment")
            active_orders_params['garment'] = garment
        if location:
            active_orders_conditions.append("il.delivered_location = :location")
            active_orders_params['location'] = location
        
        active_orders_where = " AND ".join(active_orders_conditions)
        
        active_orders_query = text(f"""
            SELECT COUNT(*) as count
            FROM stitching_invoices si
            LEFT JOIN invoice_lines il ON si.invoice_line_id = il.id
            LEFT JOIN invoices i ON il.invoice_id = i.id
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE {active_orders_where}
        """)
        active_orders_result = db.session.execute(active_orders_query, active_orders_params).fetchone()
        active_orders = int(active_orders_result.count or 0)
        
        # Fabric stock (pending yards) - apply location filter if provided
        fabric_stock_conditions = ["(il.yards_sent - COALESCE(il.yards_consumed, 0)) > 0"]
        fabric_stock_params = {}
        
        if location:
            fabric_stock_conditions.append("il.delivered_location = :location")
            fabric_stock_params['location'] = location
        
        fabric_stock_where = " AND ".join(fabric_stock_conditions)
        
        fabric_stock_query = text(f"""
            SELECT COALESCE(SUM(il.yards_sent - COALESCE(il.yards_consumed, 0)), 0) as pending_yards
            FROM invoice_lines il
            WHERE {fabric_stock_where}
        """)
        fabric_stock_result = db.session.execute(fabric_stock_query, fabric_stock_params).fetchone()
        fabric_stock = float(fabric_stock_result.pending_yards or 0)
        
        # Production rate (average items per day based on filtered date range)
        production_conditions = []
        production_params = {}
        
        if date_from:
            production_conditions.append("pl.delivery_date >= :date_from")
            production_params['date_from'] = date_from
        if date_to:
            production_conditions.append("pl.delivery_date <= :date_to")
            production_params['date_to'] = date_to
        if customer:
            production_conditions.append("c.short_name = :customer")
            production_params['customer'] = customer
        if garment:
            production_conditions.append("si.stitched_item = :garment")
            production_params['garment'] = garment
        if location:
            production_conditions.append("il.delivered_location = :location")
            production_params['location'] = location
        
        production_where = " AND ".join(production_conditions) if production_conditions else "1=1"
        
        production_query = text(f"""
            SELECT COALESCE(SUM(
                CASE 
                    WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                    THEN (
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                        COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                    )
                    ELSE 0 
                END
            ), 0) as total_items
            FROM stitching_invoices si
            LEFT JOIN invoice_lines il ON si.invoice_line_id = il.id
            LEFT JOIN invoices i ON il.invoice_id = i.id
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            LEFT JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE {production_where}
        """)
        production_result = db.session.execute(production_query, production_params).fetchone()
        total_production_count = int(production_result.total_items or 0)
        
        # Calculate the number of days in the filtered date range
        if date_from and date_to:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            end_date = datetime.strptime(date_to, '%Y-%m-%d')
            days_in_range = (end_date - start_date).days + 1  # +1 to include both start and end dates
        else:
            # Default to 30 days if no date range is specified
            days_in_range = 30
        
        production_rate = total_production_count / days_in_range if days_in_range > 0 else 0
        
        # Calculate percentage changes (mock data for now)
        revenue_change = 12.5  # Mock positive growth
        fabric_change = 8.3    # Mock positive growth
        stitching_change = 15.7  # Mock positive growth
        
        return jsonify({
            'totalRevenue': float(total_revenue),
            'directCommission': float(direct_commission),  # Direct commission sales
            'fabricCommission': float(fabric_commission),  # Fabric commission from stitching
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
        
        # Query for revenue by packing list delivery date (stitching commission)
        stitching_query = text(f"""
            SELECT 
                DATE(pl.delivery_date) as date,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE pl.delivery_date BETWEEN :date_from AND :date_to
            AND {where_clause}
            GROUP BY DATE(pl.delivery_date)
            ORDER BY DATE(pl.delivery_date)
        """)
        
        stitching_results = db.session.execute(stitching_query, params).fetchall()
        
        # Query for direct commission sales
        commission_conditions = ["il.is_commission_sale = TRUE"]
        commission_params = {
            'date_from': date_from,
            'date_to': date_to
        }
        
        if customer:
            commission_conditions.append("c.short_name = :customer")
            commission_params['customer'] = customer
        if location:
            commission_conditions.append("il.delivered_location = :location")
            commission_params['location'] = location
            
        commission_where = " AND ".join(commission_conditions)
        
        commission_query = text(f"""
            SELECT 
                DATE(il.commission_date) as date,
                COALESCE(SUM(il.commission_amount), 0) as direct_commission
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE il.commission_date BETWEEN :date_from AND :date_to
            AND {commission_where}
            GROUP BY DATE(il.commission_date)
            ORDER BY DATE(il.commission_date)
        """)
        
        commission_results = db.session.execute(commission_query, commission_params).fetchall()
        
        # Combine both datasets
        revenue_data = {}
        
        # Add stitching revenue
        for row in stitching_results:
            date_str = row.date.strftime('%m/%d')
            if date_str not in revenue_data:
                revenue_data[date_str] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            revenue_data[date_str]['fabric_commission'] = float(row.fabric_commission or 0)
            revenue_data[date_str]['stitching_revenue'] = float(row.stitching_revenue or 0)
        
        # Add direct commission sales
        for row in commission_results:
            date_str = row.date.strftime('%m/%d')
            if date_str not in revenue_data:
                revenue_data[date_str] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            revenue_data[date_str]['direct_commission'] = float(row.direct_commission or 0)
        
        # Only include dates with actual data (non-zero values)
        dates = []
        fabric_commission = []
        stitching_revenue = []
        
        for date_str, data in sorted(revenue_data.items()):
            fabric_comm = data['fabric_commission']
            stitch_rev = data['stitching_revenue']
            direct_comm = data['direct_commission']
            total = fabric_comm + stitch_rev + direct_comm
            
            # Only include dates with actual revenue
            if total > 0:
                dates.append(date_str)
                fabric_commission.append(fabric_comm + direct_comm)  # Combine both commission types
                stitching_revenue.append(stitch_rev)
        
        return jsonify({
            'labels': dates,
            'directCommission': [data['direct_commission'] for date_str, data in sorted(revenue_data.items())],
            'fabricCommission': [data['fabric_commission'] for date_str, data in sorted(revenue_data.items())],
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
        add_filter_condition(where_conditions, params, "c.short_name", customer, "customer")
        add_filter_condition(where_conditions, params, "si.stitched_item", garment, "garment")
        add_filter_condition(where_conditions, params, "il.delivered_location", location, "location")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Query for stitching revenue and commission
        stitching_query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE {where_clause}
            GROUP BY c.id, c.short_name
        """)
        
        stitching_results = db.session.execute(stitching_query, params).fetchall()
        
        # Query for direct commission sales
        commission_conditions = ["il.is_commission_sale = TRUE"]
        commission_params = {}
        
        if date_from:
            commission_conditions.append("il.commission_date >= :date_from")
            commission_params['date_from'] = date_from
        if date_to:
            commission_conditions.append("il.commission_date <= :date_to")
            commission_params['date_to'] = date_to
        if customer:
            commission_conditions.append("c.short_name = :customer")
            commission_params['customer'] = customer
        if location:
            commission_conditions.append("il.delivered_location = :location")
            commission_params['location'] = location
            
        commission_where = " AND ".join(commission_conditions)
        
        commission_query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.commission_amount), 0) as direct_commission
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE {commission_where}
            GROUP BY c.id, c.short_name
        """)
        
        commission_results = db.session.execute(commission_query, commission_params).fetchall()
        
        # Combine both datasets
        customer_data = {}
        
        # Add stitching data
        for row in stitching_results:
            customer_name = row.short_name
            if customer_name not in customer_data:
                customer_data[customer_name] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            customer_data[customer_name]['fabric_commission'] = float(row.fabric_commission or 0)
            customer_data[customer_name]['stitching_revenue'] = float(row.stitching_revenue or 0)
        
        # Add direct commission data
        for row in commission_results:
            customer_name = row.short_name
            if customer_name not in customer_data:
                customer_data[customer_name] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            customer_data[customer_name]['direct_commission'] = float(row.direct_commission or 0)
        
        # Sort by total revenue and get top 10
        sorted_customers = sorted(
            customer_data.items(),
            key=lambda x: x[1]['fabric_commission'] + x[1]['stitching_revenue'] + x[1]['direct_commission'],
            reverse=True
        )[:10]
        
        labels = [customer[0] for customer in sorted_customers]
        direct_commission = [customer[1]['direct_commission'] for customer in sorted_customers]
        fabric_commission = [customer[1]['fabric_commission'] for customer in sorted_customers]
        stitching_revenue = [customer[1]['stitching_revenue'] for customer in sorted_customers]
        
        return jsonify({
            'labels': labels,
            'directCommission': direct_commission,
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
        
        add_filter_condition(where_conditions, params, "si.created_at", date_from, "date_from", ">=")
        add_filter_condition(where_conditions, params, "si.created_at", date_to, "date_to", "<=")
        add_filter_condition(where_conditions, params, "c.short_name", customer, "customer")
        add_filter_condition(where_conditions, params, "si.stitched_item", garment, "garment")
        add_filter_condition(where_conditions, params, "il.delivered_location", location, "location")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                si.stitched_item,
                SUM(COALESCE(si.yard_consumed, 0)) as total_yards,
                SUM(
                    CASE 
                        WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                        THEN (
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                        )
                        ELSE 0 
                    END
                ) as total_quantity,
                CASE 
                    WHEN SUM(
                        CASE 
                            WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                            THEN (
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                            )
                            ELSE 0 
                        END
                    ) > 0 
                    THEN SUM(COALESCE(si.yard_consumed, 0)) / SUM(
                        CASE 
                            WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                            THEN (
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                                COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                            )
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
                        THEN (
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                        )
                        ELSE 0 
                    END
                ) as total_quantity
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
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
        
        # Calculate percentages
        total = sum(values) if values else 0
        percentages = [round((value / total * 100), 1) if total > 0 else 0 for value in values]
        
        return jsonify({
            'labels': labels,
            'values': values,
            'percentages': percentages
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
        params = {}
        
        if date_from:
            where_conditions.append("pl.delivery_date >= :date_from")
            params['date_from'] = date_from
        if date_to:
            where_conditions.append("pl.delivery_date <= :date_to")
            params['date_to'] = date_to
        
        add_filter_condition(where_conditions, params, "c.short_name", customer, "customer")
        add_filter_condition(where_conditions, params, "si.stitched_item", garment, "garment")
        add_filter_condition(where_conditions, params, "il.delivered_location", location, "location")
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = text(f"""
            SELECT 
                DATE(pl.delivery_date) as date,
                SUM(
                    CASE 
                        WHEN si.size_qty_json IS NOT NULL AND si.size_qty_json != '' 
                        THEN (
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.S'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.M'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.L'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XXXL'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.XS'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."2XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."3XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."4XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."5XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."6XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."7XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."8XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."9XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$."10XL"'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.ONE_SIZE'), 0) + 
                            COALESCE(JSON_EXTRACT(si.size_qty_json, '$.UNISEX'), 0)
                        )
                        ELSE 0 
                    END
                ) as items_produced
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE pl.delivery_date BETWEEN :date_from AND :date_to
            AND {where_clause}
            GROUP BY DATE(pl.delivery_date)
            ORDER BY DATE(pl.delivery_date)
        """)
        
        results = db.session.execute(query, params).fetchall()
        
        # Only include dates with actual production data (non-zero values)
        dates = []
        values = []
        
        for row in results:
            items_produced = int(row.items_produced or 0)
            
            # Only include dates with actual production
            if items_produced > 0:
                dates.append(row.date.strftime('%m/%d'))
                values.append(items_produced)
        
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
        
        # Query for stitching revenue and commission
        stitching_query = text(f"""
            SELECT 
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE {where_clause}
        """)
        
        stitching_result = db.session.execute(stitching_query, params).fetchone()
        fabric_commission = float(stitching_result.fabric_commission or 0)
        stitching_revenue = float(stitching_result.stitching_revenue or 0)
        
        # Query for direct commission sales
        commission_conditions = ["il.is_commission_sale = TRUE"]
        commission_params = {}
        
        if date_from:
            commission_conditions.append("il.commission_date >= :date_from")
            commission_params['date_from'] = date_from
        if date_to:
            commission_conditions.append("il.commission_date <= :date_to")
            commission_params['date_to'] = date_to
        if customer:
            commission_conditions.append("c.short_name = :customer")
            commission_params['customer'] = customer
        if location:
            commission_conditions.append("il.delivered_location = :location")
            commission_params['location'] = location
            
        commission_where = " AND ".join(commission_conditions)
        
        commission_query = text(f"""
            SELECT COALESCE(SUM(il.commission_amount), 0) as direct_commission
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE {commission_where}
        """)
        
        commission_result = db.session.execute(commission_query, commission_params).fetchone()
        direct_commission = float(commission_result.direct_commission or 0)
        
        total = fabric_commission + stitching_revenue + direct_commission
        
        # Calculate percentages
        fabric_percentage = ((fabric_commission + direct_commission) / total * 100) if total > 0 else 0
        stitching_percentage = (stitching_revenue / total * 100) if total > 0 else 0
        
        return jsonify({
            'labels': ['Direct Commission', 'Fabric Commission', 'Stitching Revenue'],
            'values': [direct_commission, fabric_commission, stitching_revenue],
            'percentages': [
                round((direct_commission / total * 100) if total > 0 else 0, 1),
                round((fabric_commission / total * 100) if total > 0 else 0, 1),
                round(stitching_percentage, 1)
            ]
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
        
        # Query for stitching revenue and commission
        stitching_query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.yards_sent * il.unit_price * :commission_rate), 0) as fabric_commission,
                COALESCE(SUM(si.total_value), 0) as stitching_revenue
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            JOIN packing_list_lines pll ON si.id = pll.stitching_invoice_id
            JOIN packing_lists pl ON pll.packing_list_id = pl.id
            WHERE {where_clause}
            GROUP BY c.id, c.short_name
        """)
        
        stitching_results = db.session.execute(stitching_query, params).fetchall()
        
        # Query for direct commission sales
        commission_conditions = ["il.is_commission_sale = TRUE"]
        commission_params = {}
        
        if date_from:
            commission_conditions.append("il.commission_date >= :date_from")
            commission_params['date_from'] = date_from
        if date_to:
            commission_conditions.append("il.commission_date <= :date_to")
            commission_params['date_to'] = date_to
        if customer:
            commission_conditions.append("c.short_name = :customer")
            commission_params['customer'] = customer
        if location:
            commission_conditions.append("il.delivered_location = :location")
            commission_params['location'] = location
            
        commission_where = " AND ".join(commission_conditions)
        
        commission_query = text(f"""
            SELECT 
                c.short_name,
                COALESCE(SUM(il.commission_amount), 0) as direct_commission
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE {commission_where}
            GROUP BY c.id, c.short_name
        """)
        
        commission_results = db.session.execute(commission_query, commission_params).fetchall()
        
        # Combine both datasets
        customer_data = {}
        
        # Add stitching data
        for row in stitching_results:
            customer_name = row.short_name
            if customer_name not in customer_data:
                customer_data[customer_name] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            customer_data[customer_name]['fabric_commission'] = float(row.fabric_commission or 0)
            customer_data[customer_name]['stitching_revenue'] = float(row.stitching_revenue or 0)
        
        # Add direct commission data
        for row in commission_results:
            customer_name = row.short_name
            if customer_name not in customer_data:
                customer_data[customer_name] = {'fabric_commission': 0, 'stitching_revenue': 0, 'direct_commission': 0}
            customer_data[customer_name]['direct_commission'] = float(row.direct_commission or 0)
        
        # Sort by total revenue and get top 10
        sorted_customers = sorted(
            customer_data.items(),
            key=lambda x: x[1]['fabric_commission'] + x[1]['stitching_revenue'] + x[1]['direct_commission'],
            reverse=True
        )[:10]
        
        labels = [customer[0] for customer in sorted_customers]
        total_earnings = [customer[1]['fabric_commission'] + customer[1]['stitching_revenue'] + customer[1]['direct_commission'] for customer in sorted_customers]
        
        return jsonify({
            'labels': labels,
            'values': total_earnings
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/test', methods=['GET'])
def test_dashboard():
    """Test endpoint for dashboard"""
    return jsonify({'message': 'Dashboard API is working!'}), 200

@dashboard_bp.route('/filter-options', methods=['GET'])
def get_filter_options():
    """Get filter options that have data in the current date range"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        
        # Set default date range if not provided
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        
        # Get customers with data
        customers_query = text("""
            SELECT DISTINCT c.short_name
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE si.created_at BETWEEN :date_from AND :date_to
            ORDER BY c.short_name
        """)
        
        customers_result = db.session.execute(customers_query, params).fetchall()
        customers = [row.short_name for row in customers_result]
        
        # Get garment types with data
        garments_query = text("""
            SELECT DISTINCT si.stitched_item
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE si.created_at BETWEEN :date_from AND :date_to
            AND si.stitched_item IS NOT NULL
            AND si.stitched_item != ''
            ORDER BY si.stitched_item
        """)
        
        garments_result = db.session.execute(garments_query, params).fetchall()
        garments = [row.stitched_item for row in garments_result]
        
        # Get locations with data
        locations_query = text("""
            SELECT DISTINCT il.delivered_location
            FROM stitching_invoices si
            JOIN invoice_lines il ON si.invoice_line_id = il.id
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE si.created_at BETWEEN :date_from AND :date_to
            AND il.delivered_location IS NOT NULL
            AND il.delivered_location != ''
            ORDER BY il.delivered_location
        """)
        
        locations_result = db.session.execute(locations_query, params).fetchall()
        locations = [row.delivered_location for row in locations_result]
        
        return jsonify({
            'customers': customers,
            'garments': garments,
            'locations': locations
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/fabric-aging', methods=['GET'])
def get_fabric_aging():
    """Get fabric aging data by location and age buckets"""
    try:
        # Get filter parameters
        date_from = request.args.get('dateFrom')
        date_to = request.args.get('dateTo')
        customer = request.args.get('customer')
        garment = request.args.get('garment')
        location = request.args.get('location')
        
        # Build filter conditions for fabric invoices
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
        
        # Calculate current date for aging calculation
        current_date = datetime.now().date()
        
        # Get fabric aging data by location and age buckets
        fabric_aging_query = text(f"""
            SELECT 
                il.delivered_location,
                CASE 
                    WHEN DATEDIFF(:current_date, i.invoice_date) <= 30 THEN '0-30 days'
                    WHEN DATEDIFF(:current_date, i.invoice_date) <= 60 THEN '30-60 days'
                    WHEN DATEDIFF(:current_date, i.invoice_date) <= 180 THEN '60-180 days'
                    ELSE '180+ days'
                END as age_bucket,
                COALESCE(SUM(il.yards_sent - il.yards_consumed), 0) as pending_yards,
                COALESCE(SUM((il.yards_sent - il.yards_consumed) * il.unit_price), 0) as pending_value,
                COUNT(DISTINCT il.id) as fabric_count
            FROM invoice_lines il
            JOIN invoices i ON il.invoice_id = i.id
            JOIN customers c ON i.customer_id = c.id
            WHERE {where_clause} 
                AND il.yards_sent > il.yards_consumed
                AND il.yards_sent > 0
            GROUP BY il.delivered_location, age_bucket
            ORDER BY il.delivered_location, 
                CASE age_bucket
                    WHEN '0-30 days' THEN 1
                    WHEN '30-60 days' THEN 2
                    WHEN '60-180 days' THEN 3
                    WHEN '180+ days' THEN 4
                END
        """)
        
        # Add current date to params
        params['current_date'] = current_date
        
        fabric_aging_result = db.session.execute(fabric_aging_query, params).fetchall()
        
        # Process results into structured format
        aging_data = {}
        locations = set()
        age_buckets = ['0-30 days', '30-60 days', '60-180 days', '180+ days']
        
        for row in fabric_aging_result:
            loc = row.delivered_location or 'Unknown'
            locations.add(loc)
            
            if loc not in aging_data:
                aging_data[loc] = {
                    'location': loc,
                    'buckets': {bucket: {'yards': 0, 'value': 0, 'count': 0} for bucket in age_buckets},
                    'total_yards': 0,
                    'total_value': 0,
                    'total_count': 0
                }
            
            aging_data[loc]['buckets'][row.age_bucket] = {
                'yards': float(row.pending_yards),
                'value': float(row.pending_value),
                'count': int(row.fabric_count)
            }
            
            aging_data[loc]['total_yards'] += float(row.pending_yards)
            aging_data[loc]['total_value'] += float(row.pending_value)
            aging_data[loc]['total_count'] += int(row.fabric_count)
        
        # Convert to list format for frontend
        result_data = []
        for loc in sorted(locations):
            if loc in aging_data:
                result_data.append(aging_data[loc])
        
        # Also provide summary data
        summary_data = {
            'total_locations': len(locations),
            'total_yards': sum(data['total_yards'] for data in result_data),
            'total_value': sum(data['total_value'] for data in result_data),
            'total_fabrics': sum(data['total_count'] for data in result_data),
            'age_buckets': age_buckets
        }
        
        return jsonify({
            'aging_data': result_data,
            'summary': summary_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
