import asyncio
import httpx
import asyncpg
import logging
from uuid import uuid4
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestApp")

API_BASE_URL = "http://localhost:8000/api/v2"
DB_URL = "postgresql://postgres:160061@localhost/tukole_db"

def generate_user(role="user"):
    return {
        "username": f"test_{role}_{uuid4().hex[:8]}",
        "first_name": "Test",
        "last_name": role.capitalize(),
        "email": f"test_{role}_{uuid4().hex[:8]}@example.com",
        "password": "Password123!",
        "role": role
    }

CUSTOMER = generate_user("user")
PROVIDER = generate_user("provider")
ADMIN = generate_user("admin")

async def activate_user_in_db(email: str, set_admin=False):
    logger.info(f"Directly activating user {email} via DB...")
    try:
        conn = await asyncpg.connect(DB_URL)
        if set_admin:
            await conn.execute("UPDATE users SET is_active = True, role = 'admin' WHERE email = $1", email)
        else:
            await conn.execute("UPDATE users SET is_active = True WHERE email = $1", email)
        await conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to activate user in DB: {e}")
        return False

async def run_tests():
    logger.info("Starting API tests with mock data for all 11 modules...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register and Activate users
        logger.info("Registering Customer, Provider, and Admin...")
        await client.post(f"{API_BASE_URL}/auth/register", json=CUSTOMER)
        await activate_user_in_db(CUSTOMER["email"])

        await client.post(f"{API_BASE_URL}/auth/register", json=PROVIDER)
        await activate_user_in_db(PROVIDER["email"])

        admin_payload = ADMIN.copy()
        admin_payload["role"] = "user"
        await client.post(f"{API_BASE_URL}/auth/register", json=admin_payload)
        await activate_user_in_db(ADMIN["email"], set_admin=True)

        # Login users
        res_cust_login = await client.post(f"{API_BASE_URL}/auth/login", json={"email": CUSTOMER["email"], "password": CUSTOMER["password"]})
        cust_headers = {"Authorization": f"Bearer {res_cust_login.json().get('access_token')}"}

        res_prov_login = await client.post(f"{API_BASE_URL}/auth/login", json={"email": PROVIDER["email"], "password": PROVIDER["password"]})
        prov_headers = {"Authorization": f"Bearer {res_prov_login.json().get('access_token')}"}

        res_admin_login = await client.post(f"{API_BASE_URL}/auth/login", json={"email": ADMIN["email"], "password": ADMIN["password"]})
        admin_headers = {"Authorization": f"Bearer {res_admin_login.json().get('access_token')}"}

        # TEST 7: Create Provider Profile
        logger.info("Test 7: Creating Provider Profile...")
        res_profile = await client.post(f"{API_BASE_URL}/providers/provider", json={"business_name": "Pro Plumbers", "bio": "Expert"}, headers=prov_headers)
        if res_profile.status_code not in [200, 201]:
            logger.error(f"Provider profile failed: {res_profile.text}")
            return

        # TEST 8: Create Service
        logger.info("Test 8: Creating Service...")
        res_service = await client.post(f"{API_BASE_URL}/services/", json={"name": f"Plumbing_{uuid4().hex[:6]}", "description": "Fix pipes", "price": 100.0}, headers=prov_headers)
        if res_service.status_code != 201:
            logger.error(f"Service creation failed: {res_service.text}")
            return
        service_id = res_service.json().get("uid")

        # TEST 9: Create Booking
        logger.info("Test 9: Creating Booking as Customer...")
        booking_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        res_booking = await client.post(f"{API_BASE_URL}/bookings/", json={"service_id": service_id, "booking_date": booking_date}, headers=cust_headers)
        if res_booking.status_code not in [200, 201]:
            logger.error(f"Booking creation failed: {res_booking.text}")
            return
        booking_id = res_booking.json().get("uid")

        # TEST 10: Create Payment
        logger.info("Test 10: Creating Payment...")
        res_payment = await client.post(f"{API_BASE_URL}/payments/", json={"booking_id": booking_id, "amount": 100.0}, headers=cust_headers)
        if res_payment.status_code in [200, 201]:
            logger.info("Payment created successfully.")
        else:
            logger.error(f"Failed to create payment: {res_payment.status_code} - {res_payment.text}")

        # TEST 11: Create Review
        logger.info("Test 11: Creating Review...")
        res_review = await client.post(f"{API_BASE_URL}/reviews/", json={"booking_id": booking_id, "rating": 5, "comment": "Great work"}, headers=cust_headers)
        if res_review.status_code in [200, 201]:
            logger.info("Review created.")
        else:
            logger.error(f"Failed to create review: {res_review.status_code} - {res_review.text}")

        # TEST 12: Create Dispute
        logger.info("Test 12: Creating Dispute...")
        res_dispute = await client.post(f"{API_BASE_URL}/disputes/", json={"booking_id": booking_id, "reason": "Service issue", "description": "Provider was late"}, headers=cust_headers)
        if res_dispute.status_code in [200, 201]:
            logger.info("Dispute created.")
        else:
            logger.error(f"Failed to create dispute: {res_dispute.status_code} - {res_dispute.text}")

        # TEST 13: Fetch Notifications
        logger.info("Test 13: Fetching Notifications...")
        res_notif = await client.get(f"{API_BASE_URL}/notifications/unread-count", headers=cust_headers)
        if res_notif.status_code == 200:
            logger.info(f"Unread Notifications: {res_notif.json()}")
        else:
            logger.error(f"Failed to fetch notifications: {res_notif.status_code} - {res_notif.text}")

        # TEST 14: Analytics Dashboard
        logger.info("Test 14: Admin Analytics Dashboard...")
        res_analytics = await client.get(f"{API_BASE_URL}/analytics/dashboard", headers=admin_headers)
        if res_analytics.status_code == 200:
            logger.info(f"Analytics Dashboard: {res_analytics.json()}")
        else:
            logger.error(f"Analytics Dashboard failed: {res_analytics.text}")

        # TEST 15: Admin Dashboard
        logger.info("Test 15: Admin Main Dashboard...")
        res_admin = await client.get(f"{API_BASE_URL}/admin/dashboard", headers=admin_headers)
        if res_admin.status_code == 200:
            logger.info(f"Admin Dashboard: {res_admin.json()}")
        else:
            logger.error(f"Admin Dashboard failed: {res_admin.text}")

        logger.info("All 15 module tests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
