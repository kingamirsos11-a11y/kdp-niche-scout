#!/usr/bin/env python3
"""Cloudflare KV Storage Backend for Hermes
Offloads memory/session data from Railway volume to Cloudflare KV.
Usage: import cf_kv; cf_kv.put("key", "value"); val = cf_kv.get("key")
"""
import os, json, urllib.request, urllib.parse

CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_KV_NAMESPACE_ID = os.environ.get("CF_KV_NAMESPACE_ID", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")

# Fallback to local creds file if env vars not set
if not CF_ACCOUNT_ID:
    try:
        with open("/data/.hermes/cf_kv.json") as f:
            creds = json.load(f)
            CF_ACCOUNT_ID = creds["CF_ACCOUNT_ID"]
            CF_KV_NAMESPACE_ID = creds["CF_KV_NAMESPACE_ID"]
            CF_API_TOKEN = creds["CF_API_TOKEN"]
    except Exception:
        pass

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}"

def _request(method, path, data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    if data is not None:
        headers["Content-Type"] = "application/octet-stream"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req, timeout=15)
    return resp.read()

def put(key: str, value: str, ttl: int = None) -> bool:
    """Store a key-value pair. Returns True on success."""
    try:
        encoded_key = urllib.parse.quote(key, safe="")
        path = f"/values/{encoded_key}"
        if ttl:
            path += f"?expiration_ttl={ttl}"
        _request("PUT", path, data=value.encode("utf-8"))
        return True
    except Exception as e:
        print(f"[CF-KV] PUT error ({key}): {e}")
        return False

def get(key: str, default: str = None) -> str | None:
    """Retrieve a value by key. Returns default if not found."""
    try:
        encoded_key = urllib.parse.quote(key, safe="")
        raw = _request("GET", f"/values/{encoded_key}")
        return raw.decode("utf-8")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return default
        print(f"[CF-KV] GET error ({key}): {e}")
        return default
    except Exception as e:
        print(f"[CF-KV] GET error ({key}): {e}")
        return default

def delete(key: str) -> bool:
    """Delete a key. Returns True on success."""
    try:
        encoded_key = urllib.parse.quote(key, safe="")
        _request("DELETE", f"/values/{encoded_key}")
        return True
    except Exception as e:
        print(f"[CF-KV] DELETE error ({key}): {e}")
        return False

def list_keys(prefix: str = "", limit: int = 100) -> list[str]:
    """List keys with optional prefix filter."""
    try:
        params = urllib.parse.urlencode({"limit": limit, "prefix": prefix})
        raw = _request("GET", f"/keys?{params}")
        result = json.loads(raw)
        return [k["name"] for k in result.get("result", [])]
    except Exception as e:
        print(f"[CF-KV] LIST error: {e}")
        return []

def put_json(key: str, obj, ttl: int = None) -> bool:
    """Store a JSON-serializable object."""
    return put(key, json.dumps(obj), ttl=ttl)

def get_json(key: str, default=None):
    """Retrieve and parse a JSON object."""
    raw = get(key)
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default

if __name__ == "__main__":
    # Quick self-test
    print("Testing Cloudflare KV...")
    assert put("__test__", "hello world"), "PUT failed"
    assert get("__test__") == "hello world", "GET failed"
    assert delete("__test__"), "DELETE failed"
    assert get("__test__") is None, "Key should be deleted"
    print("✅ All tests passed!")

