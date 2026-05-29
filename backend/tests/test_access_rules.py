from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.models import Booking, Dispute, Provider, Service
from app.modules.Disputes.service import DisputeService
from app.modules.Providers.service import ProviderService
from app.modules.Services.service import ServiceService


class ExecResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class FakeSession:
    def __init__(self, objects=None):
        self.objects = objects or {}

    async def get(self, model, key):
        return self.objects.get((model, key))

    async def exec(self, statement):
        # Statement handling isn't needed for these focused access tests.
        return ExecResult(None)


@pytest.mark.asyncio
async def test_service_ownership_blocks_other_provider_update():
    service_service = ServiceService()

    service_id = uuid4()
    owner_user_id = uuid4()
    other_user_id = uuid4()
    provider_id = uuid4()

    service = Service(uid=service_id, provider_id=provider_id, name="Cleaning", price=10)
    provider = Provider(uid=provider_id, user_id=owner_user_id)
    session = FakeSession({(Provider, provider_id): provider})

    current_user = SimpleNamespace(uid=other_user_id, role="provider")

    with pytest.raises(HTTPException) as exc:
        await service_service._ensure_service_access(service, current_user, session)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_service_ownership_allows_owner():
    service_service = ServiceService()

    service_id = uuid4()
    owner_user_id = uuid4()
    provider_id = uuid4()

    service = Service(uid=service_id, provider_id=provider_id, name="Cleaning", price=10)
    provider = Provider(uid=provider_id, user_id=owner_user_id)
    session = FakeSession({(Provider, provider_id): provider})

    current_user = SimpleNamespace(uid=owner_user_id, role="provider")

    await service_service._ensure_service_access(service, current_user, session)


@pytest.mark.asyncio
async def test_provider_ownership_blocks_other_provider_profile_update():
    provider_service = ProviderService()

    owner_user_id = uuid4()
    other_user_id = uuid4()
    provider = Provider(uid=uuid4(), user_id=owner_user_id)

    current_user = SimpleNamespace(uid=other_user_id, role="provider")

    with pytest.raises(HTTPException) as exc:
        provider_service._ensure_provider_access(provider, current_user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_dispute_access_blocks_unrelated_user():
    dispute_service = DisputeService()

    dispute_id = uuid4()
    booking_id = uuid4()
    owner_user_id = uuid4()
    provider_user_id = uuid4()
    outsider_user_id = uuid4()

    dispute = Dispute(
        uid=dispute_id,
        booking_id=booking_id,
        raised_by=owner_user_id,
        reason="late",
        status="open",
    )
    booking = Booking(
        uid=booking_id,
        service_id=uuid4(),
        customer_id=owner_user_id,
        booking_date="2026-01-01T10:00:00",
    )
    session = FakeSession({
        (Dispute, dispute_id): dispute,
        (Booking, booking_id): booking,
    })

    async def fake_provider_user_id(_booking, _session):
        return provider_user_id

    dispute_service._get_booking_provider_user_id = fake_provider_user_id

    current_user = SimpleNamespace(uid=outsider_user_id, role="user")

    with pytest.raises(HTTPException) as exc:
        await dispute_service.get_dispute_by_id(dispute_id, current_user, session)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_dispute_access_allows_booking_provider():
    dispute_service = DisputeService()

    dispute_id = uuid4()
    booking_id = uuid4()
    owner_user_id = uuid4()
    provider_user_id = uuid4()

    dispute = Dispute(
        uid=dispute_id,
        booking_id=booking_id,
        raised_by=owner_user_id,
        reason="late",
        status="open",
    )
    booking = Booking(
        uid=booking_id,
        service_id=uuid4(),
        customer_id=owner_user_id,
        booking_date="2026-01-01T10:00:00",
    )
    session = FakeSession({
        (Dispute, dispute_id): dispute,
        (Booking, booking_id): booking,
    })

    async def fake_provider_user_id(_booking, _session):
        return provider_user_id

    dispute_service._get_booking_provider_user_id = fake_provider_user_id

    current_user = SimpleNamespace(uid=provider_user_id, role="provider")

    result = await dispute_service.get_dispute_by_id(dispute_id, current_user, session)
    assert result.uid == dispute_id
