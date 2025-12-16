import requests

def check_api():
    try:
        headers = {"Authorization": "Bearer super_admin_user"}
        r = requests.get("http://localhost:8000/analytics/locations", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
        
        r2 = requests.get("http://localhost:8000/reports/daily", headers=headers)
        print(f"Recent Txs: {len(r2.json().get('recent_transactions', []))}")

    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_api()
