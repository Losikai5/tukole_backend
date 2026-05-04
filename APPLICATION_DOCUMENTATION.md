# Tukole Application Documentation

## 1. Overview

Tukole is a mobile-first service marketplace platform with:

- A FastAPI backend (Python, SQLModel, PostgreSQL)
- A React + Vite frontend
- Redis-backed token revocation and cooldown control
- Optional Celery background worker for email delivery

The platform supports:

- User authentication and email verification
- Provider onboarding and service publishing
- Booking and status workflows
- Payment escrow/release/refund transitions
- Reviews and disputes
- In-app notifications
- Admin dashboards and audits
- Analytics summaries

---

## 2. Repository Structure

### Backend

- app/main.py: FastAPI app entrypoint and router registration
- app/core/config.py: Environment-based settings
- app/core/database.py: Async SQLAlchemy/SQLModel engine and session factory
- app/core/models.py: Domain models and relationships
- app/core/dependencies.py: Access token auth, refresh token auth, role checks
- app/core/redis.py: Redis blocklist and resend-verification cooldown helper
- app/middleware.py: Logging, CORS, and trusted host middleware
- app/email.py: HTML email template rendering and FastAPI-Mail sending
- app/celery_task.py: Celery tasks for async email sending
- app/modules/*: Feature modules (routes, schemes, services)
- migrations/: Alembic migration environment and versions
- tests/: Focused tests for access rules, payment transitions, auth verification token flow

### Frontend

- Tukole_frontend/src/App.jsx: Main route map
- Tukole_frontend/src/api/client.js: API abstraction and request utility
- Tukole_frontend/src/pages/: Product surfaces (home/auth/verify/dashboard)
- Tukole_frontend/src/context/: Auth/session context
- Tukole_frontend/package.json: Frontend scripts and dependencies

---

## 3. Runtime Architecture

### Request flow

1. Client calls API under /api/v2/*.
2. Middleware logs request method/path/status/time.
3. Route-level dependencies validate JWT and role access where required.
4. Service layer enforces ownership, business rules, and state transitions.
5. Data is persisted via async SQLModel session.
6. Notifications are written using an isolated notification transaction.

### Auth and authorization model

- Access token required for protected routes.
- Refresh token is used only by auth refresh endpoint.
- Revoked token JTIs are stored in Redis blocklist.
- Verified-account enforcement happens in get_current_user (is_active must be true).
- Role-based access enforced with RoleChecker.

### Notification reliability pattern

Notification writes are intentionally isolated from business transactions:

- NotificationService opens its own DB session (local_session)
- Retries notification writes with exponential backoff
- Tracks delivery metrics in memory
- Avoids breaking successful business operations when notification persistence fails

---

## 4. Technology Stack

### Backend

- FastAPI
- SQLModel + SQLAlchemy async engine
- PostgreSQL (via asyncpg)
- Redis
- JWT auth (PyJWT)
- FastAPI-Mail + Jinja2 templates
- Celery for background jobs
- Alembic for DB migrations
- Pytest + pytest-asyncio for tests

### Frontend

- React 18
- React Router DOM
- Vite

---

## 5. Environment Configuration

Create a .env file in the project root (backend root) with at least the following values:

- DATABASE_URL
- JWT_SECRET_KEY
- JWT_ALGORITHM
- REDIS_URL (optional, defaults available)
- REDIS_HOST (optional default localhost)
- REDIS_PORT (optional default 6379)
- MAIL_USERNAME
- MAIL_PASSWORD
- MAIL_FROM
- MAIL_PORT
- MAIL_SERVER
- MAIL_FROM_NAME
- MAIL_STARTTLS
- MAIL_SSL_TLS
- USE_CREDENTIALS
- VALIDATE_CERTS
- DOMAIN

Notes:

- DOMAIN is used to compose the email verification link.
- Default verification link path is /api/v2/auth/verify/{token}.

---

## 6. Local Development Setup

### Backend setup

1. Create and activate virtual environment.
2. Install dependencies from requirements.txt.
3. Ensure PostgreSQL and Redis are running.
4. Run migrations with Alembic.
5. Start API server with Uvicorn.

Example commands (PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

API base URL (local):

- http://127.0.0.1:8000/api/v2

### Frontend setup

1. Change into Tukole_frontend.
2. Install dependencies.
3. Configure VITE_API_BASE_URL if needed (default is backend local URL).
4. Start Vite dev server.

```powershell
cd Tukole_frontend
npm install
npm run dev
```

---

## 7. Database Domain Model Summary

### Core entities

- User: account identity, role, active status
- Provider: provider profile linked one-to-one with user
- Service: provider-owned service listing
- Booking: customer-service engagement with lifecycle status
- Payment: one-per-booking financial record with guarded status transitions
- Review: customer feedback for bookings (supports soft delete + audit fields)
- Dispute: issue case tied to booking with resolution state
- Notification: user-targeted event messages with metadata payload support

### Important data constraints and behavior

- Payment is unique per booking.
- Service names are unique.
- Bookings and reviews support soft-delete audit metadata.
- Notification payload supports JSON metadata (event_type/entity_type/entity_id/payload).

---

## 8. API Versioning and Base Routes

All backend routers are mounted under:

- /api/v2

Root health/demo endpoint:

- GET /

Router groups:

- /users
- /auth
- /services
- /reviews
- /bookings
- /payments
- /providers
- /disputes
- /notifications
- /analytics
- /admin

---

## 9. Endpoint Reference

### 9.1 Auth

Base: /api/v2/auth

- POST /login: Login with email/password (verified users only)
- POST /register: Register user and send verification email
- GET /verify/{token}: Activate account with signed token
- POST /resend-verification: Resend verification email with Redis cooldown protection
- POST /refresh-token: Exchange refresh token for new access token
- POST /logout: Revoke access token JTI in Redis
- GET /me: Return current authenticated user

### 9.2 Users

Base: /api/v2/users

- GET /{user_id}: Get one user (auth required)
- PUT /{user_id}: Update user (owner or admin; role/is_active are admin-only)
- DELETE /{user_id}: Delete user (admin only)
- GET /: List users (admin only)

### 9.3 Providers

Base: /api/v2/providers

- POST /provider: Create provider profile (auth required)
- GET /me: Get my provider profile
- PUT /provider/{provider_id}: Update provider profile (owner provider or admin)
- DELETE /provider/{provider_id}: Delete provider profile (owner provider or admin)
- GET /providers: List providers (public)

### 9.4 Services

Base: /api/v2/services

- POST /: Create service (provider/admin)
- GET /: List all services (public)
- GET /{service_id}: Get service by id (public)
- PUT /{service_id}: Update service (owner provider/admin)
- DELETE /{service_id}: Delete service (owner provider/admin)

### 9.5 Bookings

Base: /api/v2/bookings

- POST /: Create booking (authenticated customer)
- GET /me: List current user bookings
- GET /provider/me: List bookings for current provider
- PUT /{booking_id}/status?status_value=: Update booking status (provider/admin, with provider restrictions)
- DELETE /{booking_id}?reason=: Soft-delete booking (owner customer or admin)
- POST /expire-pending?timeout_minutes=: Cancel stale pending bookings (admin)

### 9.6 Payments

Base: /api/v2/payments

- POST /: Create payment for booking (owner customer/admin)
- PATCH /{payment_id}/escrow: Move pending -> escrow (admin)
- PATCH /{payment_id}/release: Move escrow -> released (admin; only completed bookings and no open disputes)
- PATCH /{payment_id}/refund: Move pending/escrow -> refunded (admin)
- GET /{payment_id}: Get payment (customer/provider/admin with access checks)

### 9.7 Reviews

Base: /api/v2/reviews

- POST /: Create review (authenticated)
- GET /: List reviews (public)
- GET /{review_id}: Get review (public)
- PATCH /{review_id}: Update review (owner/admin rules in service layer)
- DELETE /{review_id}?reason=: Soft-delete review (owner/admin rules in service layer)

### 9.8 Disputes

Base: /api/v2/disputes

- POST /: Create dispute (authenticated)
- GET /: List all disputes (admin)
- GET /{dispute_id}: Get dispute (participant/admin access checks)
- PATCH /{dispute_id}: Update/respond to dispute (admin)

### 9.9 Notifications

Base: /api/v2/notifications

- GET /?limit=&offset=&unread_only=: Paginated user notifications
- PATCH /{notification_id}/read: Mark one notification as read
- PATCH /read-all: Mark all current user notifications as read
- GET /unread-count: Get unread count
- GET /delivery-metrics: Notification write metrics (admin)

### 9.10 Analytics

Base: /api/v2/analytics

- GET /dashboard: Total users, bookings, and revenue (admin)

### 9.11 Admin

Base: /api/v2/admin

- GET /dashboard: Summary admin metrics
- GET /users: List users
- DELETE /users/{user_id}: Delete user
- PATCH /users/{user_id}/status: Toggle active status
- PATCH /users/{user_id}/role: Change role
- GET /disputes: List disputes
- GET /audits/deleted-bookings: List soft-deleted bookings
- GET /audits/deleted-reviews: List soft-deleted reviews
- GET /providers: List providers
- GET /providers/{provider_id}/services: List services for provider
- DELETE /providers/{provider_id}: Delete provider
- PATCH /disputes/{dispute_id}/resolve: Resolve dispute

---

## 10. Core Business Rules

### Authentication and account activation

- New users register with is_active=false.
- Login is blocked until email verification succeeds.
- Verification resend has cooldown to limit abuse.

### Ownership and role protections

- Provider mutations enforce ownership in service layer.
- Dispute reads enforce participant/admin access.
- Admin role has elevated controls across dashboards, audits, and moderation actions.

### Booking lifecycle

- Default status starts at pending.
- Provider can only update to completed or cancelled.
- Soft-delete sets status cancelled and records deleted_at/deleted_by/delete_reason.

### Payment lifecycle

Allowed transitions:

- pending -> escrow
- pending -> refunded
- escrow -> released
- escrow -> refunded

Blocked transitions raise conflict errors.
Release additionally requires:

- booking.status == completed
- no open/under_review disputes

### Notifications

Domain events can create typed notifications, including:

- auth.*
- booking.*
- payment.*
- review.*
- dispute.*

---

## 11. Frontend Application Flows

### Route map

- /: Public landing page
- /auth: Login/register page
- /verify/:token: Account verification page
- /workspace: Authenticated application workspace

### Client API defaults

- API URL defaults to http://127.0.0.1:8000/api/v2
- Can be overridden via VITE_API_BASE_URL

### Frontend capabilities currently integrated

- Authentication and session bootstrap
- Service browsing
- Provider profile creation/edit
- Booking creation and status updates
- Payments and payment state reads
- Reviews and disputes
- Notification feed and unread counters
- Admin metrics and moderation endpoints

---

## 12. Testing Strategy and Existing Coverage

### Existing tests

- tests/test_access_rules.py
  - Service ownership checks
  - Provider ownership checks
  - Dispute access controls

- tests/test_payment_transitions.py
  - Invalid payment transition rejection
  - Allowed transition acceptance
  - Release precondition enforcement

- tests/test_auth_verification_tokens.py
  - URL-safe token encode/decode behavior
  - Expiry and invalid token handling
  - Register/verify/resend flow behavior via endpoint-level tests

### End-to-end-style mock runner

- run_tests_with_mock_data.py orchestrates cross-module API flow with seeded mock users and role scenarios.

---

## 13. Operations Notes

### Middleware

- Custom request log line includes client, method, path, status, and latency.
- CORS configured for localhost ports 3000, 5173, 4173.
- Trusted hosts restricted to localhost and 127.0.0.1.

### Redis responsibilities

- Access-token revocation (logout flow)
- Email verification resend cooldown keying

### Email delivery

- HTML template: app/templates/email_verification.html
- Immediate async fallback exists if Celery task dispatch fails

### Celery

- Broker/backend defaults to REDIS_URL
- Tasks include generic send_email_task and send_verification_email_task

---

## 14. Migrations and Data Evolution

Schema changes are tracked in migrations/versions.
Run migrations on deploy with:

```powershell
alembic upgrade head
```

Rollback workflow should be defined per release policy before production use.

---

## 15. Troubleshooting Guide

### 401 Invalid or expired token

- Ensure Authorization header is Bearer access token.
- Ensure token is not revoked in Redis.

### 403 Account not verified

- Verify email first or resend verification if cooldown window allows.

### 409 payment release errors

- Check booking status is completed.
- Check no open or under_review dispute exists for booking.

### Notification delivery metrics show failures

- Check DB availability and model constraints.
- Review app logs for retry exhaustion errors.

### Frontend cannot call backend

- Verify VITE_API_BASE_URL and backend URL.
- Verify backend CORS includes your frontend origin.

---

## 16. Suggested Next Documentation Enhancements

- Add OpenAPI schema snapshots to docs per release.
- Add sequence diagrams for booking-payment-dispute flows.
- Add deployment runbooks (Docker/systemd/Nginx) with environment templates.
- Add role-based permission matrix table by endpoint.
- Add architecture decision records (ADRs) for notification isolation and payment transition rules.
