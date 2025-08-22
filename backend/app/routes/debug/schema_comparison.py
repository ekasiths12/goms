from flask import Blueprint, jsonify
from extensions import db
from sqlalchemy import text, inspect
import json

schema_bp = Blueprint('schema', __name__, url_prefix='/api/debug/schema')

@schema_bp.route('/compare')
def compare_schemas():
    """Compare actual database schema with expected schema"""
    try:
        inspector = inspect(db.engine)
        
        # Expected schema from the new app models (matching your actual database)
        expected_schema = {
            'stitching_invoices': {
                'id': 'INTEGER PRIMARY KEY',
                'stitching_invoice_number': 'VARCHAR(32)',
                'item_name': 'VARCHAR(100)',
                'yard_consumed': 'DECIMAL(10,2)',
                'stitched_item': 'VARCHAR(100)',
                'size_qty_json': 'TEXT',
                'price': 'DECIMAL(10,2)',
                'total_value': 'DECIMAL(12,2)',
                'add_vat': 'BOOLEAN DEFAULT FALSE',
                'image_id': 'INTEGER',
                'created_at': 'DATETIME',
                'billing_group_id': 'INTEGER',
                'invoice_line_id': 'INTEGER',
                'total_fabric_cost': 'DECIMAL(12,2)',
                'total_lining_cost': 'DECIMAL(12,2)'
            },
            'garment_fabrics': {
                'id': 'INTEGER PRIMARY KEY',
                'stitching_invoice_id': 'INTEGER',
                'fabric_invoice_line_id': 'INTEGER',
                'consumption_yards': 'DECIMAL(10,2)',
                'unit_price': 'DECIMAL(10,2)',
                'total_fabric_cost': 'DECIMAL(12,2)',
                'created_at': 'DATETIME'
            },
            'lining_fabrics': {
                'id': 'INTEGER PRIMARY KEY',
                'stitching_invoice_id': 'INTEGER',
                'lining_name': 'VARCHAR(100)',
                'consumption_yards': 'DECIMAL(10,2)',
                'unit_price': 'DECIMAL(10,2)',
                'total_cost': 'DECIMAL(12,2)',
                'created_at': 'DATETIME'
            }
        }
        
        # Get actual schema from database
        actual_schema = {}
        comparison = {}
        
        for table_name in expected_schema.keys():
            if inspector.has_table(table_name):
                columns = inspector.get_columns(table_name)
                actual_schema[table_name] = {
                    col['name']: str(col['type']) for col in columns
                }
                
                # Compare expected vs actual
                expected_cols = set(expected_schema[table_name].keys())
                actual_cols = set(actual_schema[table_name].keys())
                
                comparison[table_name] = {
                    'exists': True,
                    'missing_columns': list(expected_cols - actual_cols),
                    'extra_columns': list(actual_cols - expected_cols),
                    'common_columns': list(expected_cols & actual_cols),
                    'column_details': {
                        'expected': expected_schema[table_name],
                        'actual': actual_schema[table_name]
                    }
                }
            else:
                comparison[table_name] = {
                    'exists': False,
                    'missing_columns': list(expected_schema[table_name].keys()),
                    'extra_columns': [],
                    'common_columns': [],
                    'column_details': {
                        'expected': expected_schema[table_name],
                        'actual': {}
                    }
                }
        
        return jsonify({
            'status': 'success',
            'comparison': comparison,
            'summary': {
                'tables_missing': [name for name, comp in comparison.items() if not comp['exists']],
                'tables_with_missing_columns': [name for name, comp in comparison.items() if comp['exists'] and comp['missing_columns']],
                'tables_with_extra_columns': [name for name, comp in comparison.items() if comp['exists'] and comp['extra_columns']]
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@schema_bp.route('/actual')
def get_actual_schema():
    """Get the actual database schema"""
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        schema = {}
        for table in tables:
            columns = inspector.get_columns(table)
            schema[table] = {
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col.get('nullable', True),
                        'default': col.get('default', None),
                        'primary_key': col.get('primary_key', False)
                    }
                    for col in columns
                ]
            }
        
        return jsonify({
            'status': 'success',
            'schema': schema,
            'total_tables': len(tables)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@schema_bp.route('/expected')
def get_expected_schema():
    """Get the expected schema from the new app models"""
    expected_schema = {
        'stitching_invoices': {
            'id': 'INTEGER PRIMARY KEY',
            'stitching_invoice_number': 'VARCHAR(32)',
            'item_name': 'VARCHAR(100)',
            'yard_consumed': 'DECIMAL(10,2)',
            'stitched_item': 'VARCHAR(100)',
            'size_qty_json': 'TEXT',
            'price': 'DECIMAL(10,2)',
            'total_value': 'DECIMAL(12,2)',
            'add_vat': 'BOOLEAN DEFAULT FALSE',
            'image_id': 'INTEGER',
            'created_at': 'DATETIME',
            'billing_group_id': 'INTEGER',
            'invoice_line_id': 'INTEGER',
            'total_fabric_cost': 'DECIMAL(12,2)',
            'total_lining_cost': 'DECIMAL(12,2)'
        },
        'garment_fabrics': {
            'id': 'INTEGER PRIMARY KEY',
            'stitching_invoice_id': 'INTEGER',
            'fabric_invoice_line_id': 'INTEGER',
            'consumption_yards': 'DECIMAL(10,2)',
            'unit_price': 'DECIMAL(10,2)',
            'total_fabric_cost': 'DECIMAL(12,2)',
            'created_at': 'DATETIME'
        },
        'lining_fabrics': {
            'id': 'INTEGER PRIMARY KEY',
            'stitching_invoice_id': 'INTEGER',
            'lining_name': 'VARCHAR(100)',
            'consumption_yards': 'DECIMAL(10,2)',
            'unit_price': 'DECIMAL(10,2)',
            'total_cost': 'DECIMAL(12,2)',
            'created_at': 'DATETIME'
        }
    }
    
    return jsonify({
        'status': 'success',
        'expected_schema': expected_schema
    })

@schema_bp.route('/migration-plan')
def generate_migration_plan():
    """Generate a migration plan to fix schema differences"""
    try:
        inspector = inspect(db.engine)
        
        # Get actual schema
        actual_schema = {}
        for table_name in ['stitching_invoices', 'garment_fabrics', 'lining_fabrics']:
            if inspector.has_table(table_name):
                columns = inspector.get_columns(table_name)
                actual_schema[table_name] = [col['name'] for col in columns]
            else:
                actual_schema[table_name] = []
        
        # Expected columns
        expected_columns = {
            'stitching_invoices': [
                'id', 'stitching_invoice_number', 'item_name', 'yard_consumed', 
                'stitched_item', 'size_qty_json', 'price', 'total_value', 
                'add_vat', 'created_at', 'invoice_line_id', 'image_id', 
                'billing_group_id', 'total_lining_cost', 'total_fabric_cost'
            ],
            'garment_fabrics': [
                'id', 'stitching_invoice_id', 'fabric_invoice_line_id', 
                'consumption_yards', 'unit_price', 'total_fabric_cost', 'created_at'
            ],
            'lining_fabrics': [
                'id', 'stitching_invoice_id', 'lining_name', 'consumption_yards', 
                'unit_price', 'total_cost', 'created_at'
            ]
        }
        
        migration_plan = {}
        
        for table_name, expected_cols in expected_columns.items():
            actual_cols = actual_schema.get(table_name, [])
            missing_cols = [col for col in expected_cols if col not in actual_cols]
            
            if not actual_cols:
                # Table doesn't exist
                migration_plan[table_name] = {
                    'action': 'CREATE_TABLE',
                    'missing_columns': expected_cols,
                    'sql': f"CREATE TABLE {table_name} (...)"  # Simplified
                }
            elif missing_cols:
                # Table exists but missing columns
                migration_plan[table_name] = {
                    'action': 'ADD_COLUMNS',
                    'missing_columns': missing_cols,
                    'sql_statements': [
                        f"ALTER TABLE {table_name} ADD COLUMN {col} ..." 
                        for col in missing_cols
                    ]
                }
            else:
                migration_plan[table_name] = {
                    'action': 'NO_CHANGES_NEEDED',
                    'missing_columns': []
                }
        
        return jsonify({
            'status': 'success',
            'migration_plan': migration_plan,
            'summary': {
                'tables_to_create': [name for name, plan in migration_plan.items() if plan['action'] == 'CREATE_TABLE'],
                'tables_to_modify': [name for name, plan in migration_plan.items() if plan['action'] == 'ADD_COLUMNS'],
                'tables_ok': [name for name, plan in migration_plan.items() if plan['action'] == 'NO_CHANGES_NEEDED']
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
