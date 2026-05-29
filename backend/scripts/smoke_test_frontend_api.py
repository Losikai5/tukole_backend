#!/usr/bin/env python3
import requests, uuid, time
BASE = 'http://127.0.0.1:8000/api/v2'

def r(method, path, token=None, json=None, params=None):
    url = f"{BASE}{path}"
    headers = {'Accept':'application/json'}
    if token: headers['Authorization'] = f"Bearer {token}"
    try:
        resp = requests.request(method, url, headers=headers, json=json, params=params, timeout=10)
        data = None
        ctype = resp.headers.get('content-type','')
        if 'application/json' in ctype:
            data = resp.json()
        else:
            data = resp.text
        return resp.status_code, data
    except Exception as e:
        return None, str(e)

results = []

print('Running smoke tests against', BASE)

# Public GETs
for path in ['/services/', '/providers/', '/reviews/']:
    status, data = r('GET', path)
    results.append((path, status, isinstance(data, (dict,list,str)) and (str(data)[:200]) or data))
    print(path, status)

# Register a test user
email = f"smoke+{uuid.uuid4().hex[:8]}@example.com"
password = 'TestPass123!'
signup = {
    'username':'smokeuser',
    'first_name':'Smoke',
    'last_name':'Test',
    'email': email,
    'password': password,
    'role': 'consumer'
}
status, data = r('POST','/auth/register', json=signup)
results.append(('/auth/register', status, str(data)[:1000]))
print('/auth/register', status)
if status and status >=400:
    print('  response:', data)
else:
    # Try to mark the user as verified directly in the database (dev-only)
    try:
        from app.core.config import settings
        from sqlalchemy import create_engine, text

        dburl = settings.DATABASE_URL
        sync_dburl = dburl.replace('+asyncpg', '')
        eng = create_engine(sync_dburl)
        with eng.connect() as conn:
            conn.execute(text("UPDATE users SET is_active = TRUE, is_verified = TRUE WHERE email = :email"), {'email': email})
            conn.commit()
        print('Marked user active in DB')
    except Exception as e:
        print('  DB auto-verify skipped:', e)

# Login
login = {'email': email, 'password': password}
status, data = r('POST','/auth/login', json=login)
results.append(('/auth/login', status, str(data)[:1000]))
print('/auth/login', status)
if status and status >=400:
    print('  response:', data)
access=None
refresh=None
if status==200 and isinstance(data, dict):
    access = data.get('access_token')
    refresh = data.get('refresh_token')

# Get me
status, data = r('GET','/auth/me', token=access)
results.append(('/auth/me', status, str(data)[:200]))
print('/auth/me', status)

# Try create provider (may require extra fields)
prov_payload = {'display_name':'Smoke Provider','bio':'test'}
status, data = r('POST','/providers/', token=access, json=prov_payload)
results.append(('/providers/ POST', status, str(data)[:200]))
print('/providers/ POST', status)

# Try create service (likely requires provider role, expect 403 or 201)
service_payload = {'title':'Smoke Service','description':'smoke service','price':10.0}
status, data = r('POST','/services/', token=access, json=service_payload)
results.append(('/services/ POST', status, str(data)[:200]))
print('/services/ POST', status)

# Refresh token
if refresh:
    status, data = r('POST','/auth/refresh-token', json=None, token=refresh)
    results.append(('/auth/refresh-token', status, str(data)[:200]))
    print('/auth/refresh-token', status)

# Report summary
print('\nSummary:')
for path,status,data in results:
    print(f"{path:25} -> {status}")

# Exit code semantics omitted; script just prints results
