# Tukole Frontend

A React + Vite frontend for the `tukole_backend` FastAPI application.

## Quick start

1. Install dependencies:

   ```bash
   npm install
   ```

2. Create an environment file:

   ```bash
   copy .env.example .env
   ```

3. Start the development server:

   ```bash
   npm run dev
   ```

The app expects the backend API at `http://127.0.0.1:8000/api/v2` by default.

## Included product surfaces

- Public landing page with live services and provider previews
- Login and registration flow
- Authenticated workspace for:
  - booking services
  - paying for bookings
  - leaving reviews
  - raising disputes
  - reading notifications
- Provider studio for provider profiles and service publishing
- Admin operations dashboard for users, disputes, audits, analytics, and notification delivery metrics
