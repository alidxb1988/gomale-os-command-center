#!/usr/bin/env python3
"""Request test USDT from Bybit TestNet faucet"""

import requests
import time
import hmac
import hashlib
import json

API_KEY = "FOGRlBM57gms6nxS1z"
API_SECRET = "Y3ERXjLTDGHH1EqZh81WHNEcKgnGc8xpbAsO"
BASE_URL = "https://api-testnet.bybit.com"

def generate_signature(params, secret):
    timestamp = str(int(time.time() * 1000))
    params_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sign_str = f"{timestamp}{API_KEY}{params_str}"
    signature = hmac.new(secret.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
    return signature, timestamp

print("🚀 Requesting TestNet USDT...")
print("=" * 50)

# Try faucet endpoint
timestamp = str(int(time.time() * 1000))

headers = {
    "X-BAPI-API-KEY": API_KEY,
    "X-BAPI-TIMESTAMP": timestamp,
    "X-BAPI-RECV-WINDOW": "5000",
    "Content-Type": "application/json"
}

# Check balance first
print("\n[1] Checking current balance...")
try:
    params = {"accountType": "UNIFIED"}
    param_str = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
    sign_str = f"{timestamp}{API_KEY}{param_str}"
    headers["X-BAPI-SIGN"] = hmac.new(API_SECRET.encode(), sign_str.encode(), hashlib.sha256).hexdigest()
    
    response = requests.get(f"{BASE_URL}/v5/account/wallet-balance", params=params, headers=headers, timeout=10)
    data = response.json()
    
    if data.get("retCode") == 0:
        accounts = data.get("result", {}).get("list", [])
        if accounts:
            for account in accounts:
                coins = account.get("coin", [])
                for coin in coins:
                    print(f"   {coin.get('coin')}: {coin.get('walletBalance', '0')}")
        else:
            print("   No coins found (account is new)")
    else:
        print(f"   Error: {data.get('retMsg')}")
except Exception as e:
    print(f"   Error: {e}")

# Try to get faucet URL from Bybit
print("\n[2] Checking available TestNet services...")
print("   Bybit TestNet faucet is available at:")
print("   👉 https://testnet.bybit.com/faucet")
print("\n   Or manually via web:")
print("   1. Login to https://testnet.bybit.com")
print("   2. Go to Assets → Faucet")
print("   3. Select USDT → Get Test Funds")

print("\n" + "=" * 50)
print("✅ Check complete!")
