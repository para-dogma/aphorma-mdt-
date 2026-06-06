import requests
BASE_URL = "http://localhost:8000"

def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    print("OK: health")

def test_policies():
    r = requests.get(f"{BASE_URL}/policies")
    assert r.status_code == 200
    print("OK: policies")

if __name__ == "__main__":
    test_health()
    test_policies()
    print("ALL TESTS PASSED")
