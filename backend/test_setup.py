#!/usr/bin/env python3
"""
Test script to verify backend setup
"""

import requests
import json

def test_api_endpoints():
    """Test basic API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API endpoints...")
    
    # Test health check
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print("❌ Health check endpoint failed")
    except Exception as e:
        print(f"❌ Health check endpoint error: {e}")
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print("❌ Root endpoint failed")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test customers endpoint
    try:
        response = requests.get(f"{base_url}/api/customers")
        if response.status_code == 200:
            print("✅ Customers endpoint working")
        else:
            print("❌ Customers endpoint failed")
    except Exception as e:
        print(f"❌ Customers endpoint error: {e}")
    
    # Test placeholder endpoints
    endpoints = [
        "/api/invoices",
        "/api/stitching", 
        "/api/packing-lists",
        "/api/group-bills"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint} endpoint working")
            else:
                print(f"❌ {endpoint} endpoint failed")
        except Exception as e:
            print(f"❌ {endpoint} endpoint error: {e}")

def test_customer_creation():
    """Test customer creation"""
    base_url = "http://localhost:8000"
    
    print("\n🧪 Testing customer creation...")
    
    test_customer = {
        "customer_id": "TEST001",
        "short_name": "Test Customer",
        "full_name": "Test Customer Full Name",
        "is_active": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/customers",
            json=test_customer,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 201:
            print("✅ Customer creation working")
            data = response.json()
            print(f"   Created customer: {data['data']['short_name']}")
        else:
            print(f"❌ Customer creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Customer creation error: {e}")

if __name__ == '__main__':
    print("🚀 Testing Garment Management System Backend Setup")
    print("=" * 50)
    
    test_api_endpoints()
    test_customer_creation()
    
    print("\n" + "=" * 50)
    print("🏁 Testing completed!")
