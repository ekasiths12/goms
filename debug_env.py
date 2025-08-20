#!/usr/bin/env python3
"""
Debug script to check environment variables
"""

import os

def main():
    print("🔍 Environment Variables Debug")
    print("=" * 50)
    
    # Check all environment variables
    env_vars = [
        'DATABASE_URL',
        'MYSQL_URL',
        'SECRET_KEY',
        'FLASK_DEBUG',
        'PORT',
        'RAILWAY_ENVIRONMENT'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        if var in ['DATABASE_URL', 'MYSQL_URL'] and value != 'NOT_SET':
            # Mask sensitive parts of database URLs
            if 'mysql://' in value:
                parts = value.split('@')
                if len(parts) > 1:
                    masked_value = f"mysql://***:***@{parts[1]}"
                else:
                    masked_value = value[:20] + "..." if len(value) > 20 else value
            else:
                masked_value = value[:20] + "..." if len(value) > 20 else value
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")
    
    print("\n🔍 All Environment Variables:")
    print("-" * 30)
    for key, value in os.environ.items():
        if 'DATABASE' in key.upper() or 'MYSQL' in key.upper():
            if 'mysql://' in value:
                parts = value.split('@')
                if len(parts) > 1:
                    masked_value = f"mysql://***:***@{parts[1]}"
                else:
                    masked_value = value[:20] + "..." if len(value) > 20 else value
                print(f"{key}: {masked_value}")
            else:
                print(f"{key}: {value[:20]}..." if len(value) > 20 else f"{key}: {value}")
        else:
            print(f"{key}: {value}")

if __name__ == '__main__':
    main()
