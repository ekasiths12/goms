from flask import Blueprint, jsonify, request
from extensions import db
from sqlalchemy import text, inspect
import json
from datetime import datetime

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')

@debug_bp.route('/health')
def health_check():
    """Basic health check for debug endpoints"""
    return jsonify({
        'status': 'healthy',
        'message': 'Debug endpoints are working',
        'timestamp': datetime.now().isoformat()
    })

@debug_bp.route('/tables')
def list_tables():
    """List all tables in the database"""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        table_info = []
        for table in tables:
            columns = inspector.get_columns(table)
            table_info.append({
                'table_name': table,
                'column_count': len(columns),
                'columns': [col['name'] for col in columns]
            })
        
        return jsonify({
            'status': 'success',
            'tables': table_info,
            'total_tables': len(tables)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/stitching-records')
def inspect_stitching_records():
    """Inspect stitching records and their line items"""
    try:
        # Get basic stitching records
        with db.engine.connect() as connection:
            # Get stitching records
            result = connection.execute(text("""
                SELECT 
                    id, serial_number, customer_name, invoice_date, 
                    created_at, updated_at,
                    fabric_name, fabric_unit_price, yard_consumed,
                    price, add_vat, delivered, delivery_date
                FROM stitching_invoices 
                ORDER BY created_at DESC 
                LIMIT 10
            """))
            stitching_records = [dict(row._mapping) for row in result]
            
            # Get line items for each record
            for record in stitching_records:
                # Get garment fabrics
                fabric_result = connection.execute(text("""
                    SELECT * FROM garment_fabrics 
                    WHERE stitching_invoice_id = :record_id
                """), {'record_id': record['id']})
                record['garment_fabrics'] = [dict(row._mapping) for row in fabric_result]
                
                # Get lining fabrics
                lining_result = connection.execute(text("""
                    SELECT * FROM lining_fabrics 
                    WHERE stitching_invoice_id = :record_id
                """), {'record_id': record['id']})
                record['lining_fabrics'] = [dict(row._mapping) for row in lining_result]
        
        return jsonify({
            'status': 'success',
            'stitching_records': stitching_records,
            'total_records': len(stitching_records)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/stitching-structure')
def inspect_stitching_structure():
    """Inspect the structure of stitching-related tables"""
    try:
        inspector = inspect(db.engine)
        
        tables = ['stitching_invoices', 'garment_fabrics', 'lining_fabrics']
        structure = {}
        
        for table in tables:
            if inspector.has_table(table):
                columns = inspector.get_columns(table)
                structure[table] = {
                    'columns': [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col.get('nullable', True),
                            'default': col.get('default', None)
                        }
                        for col in columns
                    ]
                }
            else:
                structure[table] = {'error': 'Table not found'}
        
        return jsonify({
            'status': 'success',
            'structure': structure
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/missing-data')
def find_missing_data():
    """Find records with missing line items or quantities"""
    try:
        with db.engine.connect() as connection:
            # Find stitching records without garment fabrics
            result1 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices si
                LEFT JOIN garment_fabrics gf ON si.id = gf.stitching_invoice_id
                WHERE gf.id IS NULL
            """))
            missing_garment_fabrics = result1.fetchone()[0]
            
            # Find stitching records without lining fabrics
            result2 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices si
                LEFT JOIN lining_fabrics lf ON si.id = lf.stitching_invoice_id
                WHERE lf.id IS NULL
            """))
            missing_lining_fabrics = result2.fetchone()[0]
            
            # Find records with missing size quantities
            result3 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices 
                WHERE size_qty IS NULL OR size_qty = '{}' OR size_qty = ''
            """))
            missing_size_qty = result3.fetchone()[0]
            
            # Find records with missing stitching quantities
            result4 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices 
                WHERE stitching_qty IS NULL OR stitching_qty = 0
            """))
            missing_stitching_qty = result4.fetchone()[0]
            
            # Get sample records with missing data
            result5 = connection.execute(text("""
                SELECT id, serial_number, customer_name, size_qty, stitching_qty
                FROM stitching_invoices 
                WHERE (size_qty IS NULL OR size_qty = '{}' OR size_qty = '')
                   OR (stitching_qty IS NULL OR stitching_qty = 0)
                LIMIT 5
            """))
            sample_missing = [dict(row._mapping) for row in result5]
        
        return jsonify({
            'status': 'success',
            'missing_data_summary': {
                'records_without_garment_fabrics': missing_garment_fabrics,
                'records_without_lining_fabrics': missing_lining_fabrics,
                'records_with_missing_size_qty': missing_size_qty,
                'records_with_missing_stitching_qty': missing_stitching_qty
            },
            'sample_missing_records': sample_missing
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/sample-data/<table_name>')
def get_sample_data(table_name):
    """Get sample data from any table"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        with db.engine.connect() as connection:
            result = connection.execute(text(f"""
                SELECT * FROM {table_name} 
                LIMIT :limit
            """), {'limit': limit})
            
            columns = result.keys()
            data = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Handle JSON fields
                    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                        try:
                            row_dict[col] = json.loads(value)
                        except:
                            row_dict[col] = value
                    else:
                        row_dict[col] = value
                data.append(row_dict)
        
        return jsonify({
            'status': 'success',
            'table': table_name,
            'data': data,
            'total_rows': len(data)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/data-comparison')
def compare_data_structures():
    """Compare expected vs actual data structures"""
    try:
        with db.engine.connect() as connection:
            # Check stitching_invoices table
            result = connection.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN size_qty IS NOT NULL AND size_qty != '{}' AND size_qty != '' THEN 1 END) as with_size_qty,
                    COUNT(CASE WHEN stitching_qty IS NOT NULL AND stitching_qty > 0 THEN 1 END) as with_stitching_qty,
                    COUNT(CASE WHEN fabric_name IS NOT NULL AND fabric_name != '' THEN 1 END) as with_fabric_name
                FROM stitching_invoices
            """))
            stitching_stats = dict(result.fetchone()._mapping)
            
            # Check garment_fabrics table
            result2 = connection.execute(text("""
                SELECT COUNT(*) as total_records FROM garment_fabrics
            """))
            garment_fabrics_count = result2.fetchone()[0]
            
            # Check lining_fabrics table
            result3 = connection.execute(text("""
                SELECT COUNT(*) as total_records FROM lining_fabrics
            """))
            lining_fabrics_count = result3.fetchone()[0]
        
        return jsonify({
            'status': 'success',
            'data_comparison': {
                'stitching_invoices': stitching_stats,
                'garment_fabrics': {'total_records': garment_fabrics_count},
                'lining_fabrics': {'total_records': lining_fabrics_count}
            },
            'analysis': {
                'size_qty_completion_rate': f"{(stitching_stats['with_size_qty'] / stitching_stats['total_records'] * 100):.1f}%" if stitching_stats['total_records'] > 0 else "0%",
                'stitching_qty_completion_rate': f"{(stitching_stats['with_stitching_qty'] / stitching_stats['total_records'] * 100):.1f}%" if stitching_stats['total_records'] > 0 else "0%",
                'fabric_name_completion_rate': f"{(stitching_stats['with_fabric_name'] / stitching_stats['total_records'] * 100):.1f}%" if stitching_stats['total_records'] > 0 else "0%"
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@debug_bp.route('/migration-check')
def check_migration_issues():
    """Check for common migration issues"""
    try:
        with db.engine.connect() as connection:
            issues = []
            
            # Check for empty size_qty fields
            result1 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices 
                WHERE size_qty IS NULL OR size_qty = '{}' OR size_qty = ''
            """))
            empty_size_qty = result1.fetchone()[0]
            if empty_size_qty > 0:
                issues.append(f"Found {empty_size_qty} records with empty size_qty")
            
            # Check for records without line items
            result2 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices si
                LEFT JOIN garment_fabrics gf ON si.id = gf.stitching_invoice_id
                LEFT JOIN lining_fabrics lf ON si.id = lf.stitching_invoice_id
                WHERE gf.id IS NULL AND lf.id IS NULL
            """))
            no_line_items = result2.fetchone()[0]
            if no_line_items > 0:
                issues.append(f"Found {no_line_items} records without any line items")
            
            # Check for malformed JSON in size_qty
            result3 = connection.execute(text("""
                SELECT id, serial_number, size_qty FROM stitching_invoices 
                WHERE size_qty IS NOT NULL AND size_qty != '{}' AND size_qty != ''
                LIMIT 5
            """))
            sample_size_qty = [dict(row._mapping) for row in result3]
            
            # Check for records with zero quantities
            result4 = connection.execute(text("""
                SELECT COUNT(*) as count FROM stitching_invoices 
                WHERE stitching_qty = 0 OR yard_consumed = 0
            """))
            zero_quantities = result4.fetchone()[0]
            if zero_quantities > 0:
                issues.append(f"Found {zero_quantities} records with zero quantities")
        
        return jsonify({
            'status': 'success',
            'migration_issues': issues,
            'sample_size_qty_data': sample_size_qty,
            'total_issues_found': len(issues)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
