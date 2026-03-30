#!/usr/bin/env python3
"""
Bybit TestNet Connection Test - Debug Version
"""

import requests
import time
import hmac
import hashlib

API_KEY = "FOGRlBM57gms6nxS1z"
API_SECRET = "Y3ERXjLTDGHH1EqZh81WHNEcKgnGc8xpbAsO"
BASE_URL = "https://api-testnet.bybit.com"

def get_signature(params, secret):
    """Bybit V5 API signature generation"""
    timestamp = str(int(time.time() * 1000))
    params_to_sign = dict(params)
    params_to_sign['timestamp'] = timestamp
    
    # Create param string sorted by key
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params_to_sign.items())])
    
    # Generate signature
    signature = hmac.new(
        secret.encode('utf-8'),
        param_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature, timestamp

print("=" * 60)
print("Bybit Connection Test - Debug")
print("=" * 60)
print(f"\nAPI Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"Secret: {API_SECRET[:5]}...{API_SECRET[-5:]}")
print(f"Endpoint: {BASE_URL}")

# Test with recv_window
timestamp = str(int(time.time() * 1000))
params = {
    "api_key": API_KEY,
    "timestamp": timestamp,
    "recv_window": "5000"
}

# Generate signature properly for V5 API
param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
signature = hmac.new(
    API_SECRET.encode('utf-8'),
    param_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

params["sign"] = signature

print(f"\nRequest params: {params}")
print(f"Param string: {param_str}")
print(f"Signature: {signature[:20]}...")

print("\n--- Testing /v5/user/query-api ---")
try:
    response = requests.get(f"{BASE_URL}/v5/user/query-api", params=params, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing with V5 auth headers instead ---")
import uuid

timestamp = str(int(time.time() * 1000))
recv_window = "5000"

# For V5 API, use headers-based auth
params_clean = {"api_key": API_KEY, "timestamp": timestamp, "recv_window": recv_window}
param_str = "&".join([f"{k}={v}" for k, v in sorted(params_clean.items())])
signature = hmac.new(API_SECRET.encode('utf-8'), param_str.encode('utf-8'), hashlib.sha256).hexdigest()

headers = {
    "X-BAPI-API-KEY": API_KEY,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-SIGN": signature,
    "X-BAPI-RECV-WINDOW": recv_window,
    "Content-Type": "application/json"
}

try:
    response = requests.get(f"{BASE_URL}/v5/user/query-api", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
