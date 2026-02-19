#!/usr/bin/env python3
"""Quick test script for the EC2 Provisioner API"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing GET /health...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_instances():
    """Test list instances endpoint"""
    print("\nTesting GET /instances...")
    try:
        response = requests.get(f"{BASE_URL}/instances")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_instance_invalid():
    """Test create instance with invalid data (should fail free tier check)"""
    print("\nTesting POST /instances with invalid instance type...")
    try:
        payload = {
            "name": "test-instance",
            "ami": "ami-0c02fb55956c7d316",
            "instance_type": "t2.large",  # Not free tier
            "storage_gb": 8
        }
        response = requests.post(f"{BASE_URL}/instances", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_instance_invalid_ami():
    """Test create instance with invalid AMI (should fail free tier check)"""
    print("\nTesting POST /instances with invalid AMI...")
    try:
        payload = {
            "name": "test-instance",
            "ami": "ami-invalid12345",  # Not free tier
            "instance_type": "t2.micro",
            "storage_gb": 8
        }
        response = requests.post(f"{BASE_URL}/instances", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_swagger_docs():
    """Test Swagger/OpenAPI docs"""
    print("\nTesting GET /docs (Swagger UI)...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Swagger UI available at http://localhost:8000/docs")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("EC2 Provisioner API — Local Testing")
    print("=" * 60)

    results = []
    results.append(("Health Check", test_health()))
    results.append(("List Instances", test_list_instances()))
    results.append(("Invalid Instance Type", test_create_instance_invalid()))
    results.append(("Invalid AMI", test_create_instance_invalid_ami()))
    results.append(("Swagger Docs", test_swagger_docs()))

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 60)
    total_passed = sum(1 for _, p in results if p)
    print(f"Total: {total_passed}/{len(results)} tests passed")

    sys.exit(0 if all(p for _, p in results) else 1)
