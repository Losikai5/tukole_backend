from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.Payments.service import PaymentService


class ExecResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class FakeSession:
    def __init__(self):
        self.provider = None

    async def exec(self, statement):
        return ExecResult(None)

    async def commit(self):
        return None

    async def refresh(self, obj):
        return None

    async def get(self, model, key):
        return self.provider


@pytest.mark.asyncio
async def test_transition_blocks_release_from_pending():
    service = PaymentService()
    payment = SimpleNamespace(uid=uuid4(), status="pending")

    with pytest.raises(HTTPException) as exc:
        service._ensure_status_transition(payment, "released")

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_transition_allows_refund_from_escrow():
    service = PaymentService()
    payment = SimpleNamespace(uid=uuid4(), status="escrow")

    service._ensure_status_transition(payment, "refunded")


@pytest.mark.asyncio
async def test_release_payment_requires_completed_booking():
    service = PaymentService()
    session = FakeSession()

    payment_id = uuid4()
    payment = SimpleNamespace(uid=payment_id, booking_id=uuid4(), status="escrow")
    booking = SimpleNamespace(uid=payment.booking_id, status="pending")
    service_obj = SimpleNamespace(provider_id=uuid4())

    async def fake_get_payment(_payment_id, _session):
        return payment

    async def fake_get_booking_with_service(_booking_id, _session):
        return booking, service_obj

    service._get_payment_or_404 = fake_get_payment
    service._get_booking_with_service = fake_get_booking_with_service

    with pytest.raises(HTTPException) as exc:
        await service.release_payment(payment_id, session)

    assert exc.value.status_code == 409
    assert "completed bookings" in exc.value.detail


@pytest.mark.asyncio
async def test_refund_blocks_from_released():
    service = PaymentService()
    session = FakeSession()

    payment_id = uuid4()
    payment = SimpleNamespace(uid=payment_id, booking_id=uuid4(), status="released")

    async def fake_get_payment(_payment_id, _session):
        return payment

    service._get_payment_or_404 = fake_get_payment

    with pytest.raises(HTTPException) as exc:
        await service.refund_payment(payment_id, session)

    assert exc.value.status_code == 409
