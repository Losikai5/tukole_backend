import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import asyncpg
import httpx

API_BASE_URL = "http://127.0.0.1:8000/api/v2"
DB_URL = "postgresql://postgres:160061@localhost/tukole_db"
PASSWORD = "Password123!"


def make_user(role: str):
    suffix = uuid4().hex[:8]
    return {
        "username": f"smoke_{role}_{suffix}",
        "first_name": "Smoke",
        "last_name": role.capitalize(),
        "email": f"smoke_{role}_{suffix}@example.com",
        "password": PASSWORD,
        "role": role,
    }


CUSTOMER = make_user("user")
PROVIDER = make_user("provider")
ADMIN = make_user("user")


async def activate_user(email: str, make_admin: bool = False):
    conn = await asyncpg.connect(DB_URL)
    try:
        if make_admin:
            await conn.execute("UPDATE users SET is_active = True, role = 'admin' WHERE email = $1", email)
        else:
            await conn.execute("UPDATE users SET is_active = True WHERE email = $1", email)
    finally:
        await conn.close()


async def login(client: httpx.AsyncClient, user: dict):
    response = await client.post(f"{API_BASE_URL}/auth/login", json={"email": user["email"], "password": user["password"]})
    response.raise_for_status()
    return response.json()


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        for user, is_admin in [(CUSTOMER, False), (PROVIDER, False), (ADMIN, True)]:
            register_response = await client.post(f"{API_BASE_URL}/auth/register", json=user)
            print("register", user["email"], register_response.status_code)
            await activate_user(user["email"], make_admin=is_admin)

        customer_login = await login(client, CUSTOMER)
        provider_login = await login(client, PROVIDER)
        admin_login = await login(client, ADMIN)

        print("customer_login_ok", customer_login["access_token"][:24])
        print("provider_login_ok", provider_login["access_token"][:24])
        print("admin_login_ok", admin_login["access_token"][:24])

        customer_headers = {"Authorization": f"Bearer {customer_login['access_token']}"}
        provider_headers = {"Authorization": f"Bearer {provider_login['access_token']}"}
        admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

        provider_profile = await client.post(
            f"{API_BASE_URL}/providers/",
            json={"business_name": "Smoke Provider", "bio": "Smoke test provider"},
            headers=provider_headers,
        )
        print("provider_profile", provider_profile.status_code)
        provider_profile.raise_for_status()
        provider_profile_uid = provider_profile.json()["uid"]

        unique_service_name = f"Smoke Service {uuid4().hex[:8]}"

        service_response = await client.post(
            f"{API_BASE_URL}/services/",
            json={"name": unique_service_name, "description": "Smoke test service", "price": 1000},
            headers=provider_headers,
        )
        print("service_create", service_response.status_code)
        service_response.raise_for_status()
        service_id = service_response.json()["uid"]

        booking_date = (datetime.now() + timedelta(days=2)).isoformat(timespec="seconds")
        booking_response = await client.post(
            f"{API_BASE_URL}/bookings/",
            json={"service_id": service_id, "booking_date": booking_date},
            headers=customer_headers,
        )
        print("booking_create", booking_response.status_code)
        booking_response.raise_for_status()
        booking_id = booking_response.json()["uid"]

        checks = [
            ("get_me", f"{API_BASE_URL}/auth/me", customer_headers),
            ("my_bookings", f"{API_BASE_URL}/bookings/my-bookings", customer_headers),
            ("provider_bookings", f"{API_BASE_URL}/bookings/provider-bookings", provider_headers),
            ("notifications", f"{API_BASE_URL}/notifications/", customer_headers),
            ("unread_notifications", f"{API_BASE_URL}/notifications/unread", customer_headers),
            ("admin_dashboard", f"{API_BASE_URL}/admin/dashboard", admin_headers),
            ("analytics_dashboard", f"{API_BASE_URL}/admin/dashboard", admin_headers),
            ("admin_users", f"{API_BASE_URL}/admin/users", admin_headers),
        ]

        for label, url, headers in checks:
            response = await client.get(url, headers=headers)
            print(label, response.status_code)
            if response.status_code >= 400:
                print(response.text)
                response.raise_for_status()

        print("customer_email", CUSTOMER["email"])
        print("customer_password", CUSTOMER["password"])
        print("customer_access_token", customer_login["access_token"])
        print("customer_refresh_token", customer_login["refresh_token"])
        print("customer_user_json", customer_login["user"])
        print("booking_id", booking_id)
        print("service_id", service_id)
        print("provider_profile_uid", provider_profile_uid)


if __name__ == "__main__":
    asyncio.run(main())
