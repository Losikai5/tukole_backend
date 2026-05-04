# celery_task.py
import os
from celery import Celery
from app.core.config import settings
from app.email import create_message
from asgiref.sync import async_to_sync

app = Celery("app")

app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)

if os.name == "nt":
    app.conf.worker_pool = "solo"

app.autodiscover_tasks(["app"])


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

@app.task(name="app.celery_task.send_verification_email")
def send_verification_email(recipient: str, verification_link: str):
    subject = "Verify your Email"
    body = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{verification_link}">link</a> to verify your account.</p>
    """
    async_to_sync(create_message)(subject=subject, recipients=[recipient], body=body)


# ─────────────────────────────────────────────
# BOOKING
# ─────────────────────────────────────────────

@app.task(bind=True, name="app.celery_task.send_booking_created_email", max_retries=3, default_retry_delay=60)
def send_booking_created_email(self, provider_email: str, service_name: str, booking_date: str):
    try:
        subject = "New Booking Request"
        body = f"""
        <h1>You have a new booking request!</h1>
        <p>A customer has requested your service.</p>
        <ul>
            <li><strong>Service:</strong> {service_name}</li>
            <li><strong>Date:</strong> {booking_date}</li>
        </ul>
        <p>Please log in to accept or decline the booking.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[provider_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_booking_accepted_email", max_retries=3, default_retry_delay=60)
def send_booking_accepted_email(self, customer_email: str, service_name: str, booking_date: str):
    try:
        subject = "Booking Accepted"
        body = f"""
        <h1>Your booking has been accepted!</h1>
        <ul>
            <li><strong>Service:</strong> {service_name}</li>
            <li><strong>Date:</strong> {booking_date}</li>
        </ul>
        <p>The provider is ready for you. Please ensure payment is made.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[customer_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_booking_completed_email", max_retries=3, default_retry_delay=60)
def send_booking_completed_email(self, recipient_email: str, service_name: str, is_provider: bool):
    try:
        subject = "Booking Completed"
        if is_provider:
            body = f"""
            <h1>Booking Completed!</h1>
            <p>You have successfully completed the service: <strong>{service_name}</strong>.</p>
            <p>Funds will be released from escrow shortly.</p>
            """
        else:
            body = f"""
            <h1>Service Completed!</h1>
            <p>Your booking for <strong>{service_name}</strong> has been completed.</p>
            <p>Please leave a review for the provider.</p>
            """
        async_to_sync(create_message)(subject=subject, recipients=[recipient_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_booking_cancelled_email", max_retries=3, default_retry_delay=60)
def send_booking_cancelled_email(self, recipient_email: str, service_name: str):
    try:
        subject = "Booking Cancelled"
        body = f"""
        <h1>Booking Cancelled</h1>
        <p>The booking for <strong>{service_name}</strong> has been cancelled.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[recipient_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────
# DISPUTE
# ─────────────────────────────────────────────

@app.task(bind=True, name="app.celery_task.send_dispute_raised_email", max_retries=3, default_retry_delay=60)
def send_dispute_raised_email(self, recipient_email: str, booking_uid: str, is_admin: bool):
    try:
        subject = "Dispute Raised"
        if is_admin:
            body = f"""
            <h1>A dispute requires your attention</h1>
            <p>A dispute has been raised on booking <strong>{booking_uid}</strong>.</p>
            <p>Please log in to review the case.</p>
            """
        else:
            body = f"""
            <h1>A dispute has been filed</h1>
            <p>A dispute has been filed against your booking <strong>{booking_uid}</strong>.</p>
            <p>Please log in to provide your evidence.</p>
            """
        async_to_sync(create_message)(subject=subject, recipients=[recipient_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_dispute_under_review_email", max_retries=3, default_retry_delay=60)
def send_dispute_under_review_email(self, recipient_email: str, booking_uid: str):
    try:
        subject = "Dispute Under Review"
        body = f"""
        <h1>Your dispute is under review</h1>
        <p>The admin is reviewing the dispute on booking <strong>{booking_uid}</strong>.</p>
        <p>You will be notified once a decision has been made.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[recipient_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_dispute_resolved_email", max_retries=3, default_retry_delay=60)
def send_dispute_resolved_email(self, recipient_email: str, admin_response: str, won: bool):
    try:
        subject = "Dispute Resolved"
        if won:
            body = f"""
            <h1>Dispute Resolved in Your Favour</h1>
            <p>{admin_response}</p>
            <p>The funds have been processed accordingly.</p>
            """
        else:
            body = f"""
            <h1>Dispute Resolved</h1>
            <p>{admin_response}</p>
            <p>Unfortunately the dispute was not resolved in your favour.</p>
            """
        async_to_sync(create_message)(subject=subject, recipients=[recipient_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────
# REVIEW
# ─────────────────────────────────────────────

@app.task(bind=True, name="app.celery_task.send_review_made_email", max_retries=3, default_retry_delay=60)
def send_review_made_email(self, provider_email: str, rating: int, comment: str):
    try:
        subject = "You received a new review"
        body = f"""
        <h1>New Review!</h1>
        <p>A customer has left you a review.</p>
        <ul>
            <li><strong>Rating:</strong> {rating}/5</li>
            <li><strong>Comment:</strong> {comment or "No comment left"}</li>
        </ul>
        """
        async_to_sync(create_message)(subject=subject, recipients=[provider_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

@app.task(bind=True, name="app.celery_task.send_payment_in_escrow_email", max_retries=3, default_retry_delay=60)
def send_payment_in_escrow_email(self, customer_email: str, amount: float, service_name: str):
    try:
        subject = "Payment Held in Escrow"
        body = f"""
        <h1>Your Payment is Secure</h1>
        <p>Your payment of <strong>${amount:.2f}</strong> for <strong>{service_name}</strong>
        is safely held in escrow.</p>
        <p>It will be released to the provider once the service is completed.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[customer_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_payment_released_email", max_retries=3, default_retry_delay=60)
def send_payment_released_email(self, provider_email: str, amount: float):
    try:
        subject = "Payment Released"
        body = f"""
        <h1>Your Payment has been Released!</h1>
        <p>The amount of <strong>${amount:.2f}</strong> has been released from escrow to your account.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[provider_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)


@app.task(bind=True, name="app.celery_task.send_payment_refunded_email", max_retries=3, default_retry_delay=60)
def send_payment_refunded_email(self, customer_email: str, amount: float):
    try:
        subject = "Payment Refunded"
        body = f"""
        <h1>Your Payment has been Refunded!</h1>
        <p>The amount of <strong>${amount:.2f}</strong> has been refunded to your account.</p>
        """
        async_to_sync(create_message)(subject=subject, recipients=[customer_email], body=body)
    except Exception as exc:
        raise self.retry(exc=exc)
