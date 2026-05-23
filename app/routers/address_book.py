from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.database import User
from app.models.schemas import (
    AddressDefaultsOut,
    ApiResponse,
    RecipientProfileCreate,
    RecipientProfileOut,
    RecipientProfileUpdate,
    SenderProfileCreate,
    SenderProfileOut,
    SenderProfileUpdate,
)
from app.services import address_book_service
from app.utils.helpers import ok
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/address-book", tags=["address-book"])


@router.get("/senders", response_model=ApiResponse)
def list_senders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profiles = address_book_service.list_sender_profiles(db, current_user)
    return ok(data=[SenderProfileOut.model_validate(profile) for profile in profiles])


@router.post("/senders", response_model=ApiResponse)
def create_sender(
    payload: SenderProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.create_sender_profile(db, current_user, payload)
    return ok(data=SenderProfileOut.model_validate(profile), message="Sender profile created")


@router.put("/senders/{profile_id}", response_model=ApiResponse)
def update_sender(
    profile_id: int,
    payload: SenderProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.update_sender_profile(db, current_user, profile_id, payload)
    return ok(data=SenderProfileOut.model_validate(profile), message="Sender profile updated")


@router.put("/senders/{profile_id}/default", response_model=ApiResponse)
def set_default_sender(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.set_default_sender_profile(db, current_user, profile_id)
    return ok(data=SenderProfileOut.model_validate(profile), message="Sender default updated")


@router.delete("/senders/{profile_id}", response_model=ApiResponse)
def delete_sender(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    address_book_service.delete_sender_profile(db, current_user, profile_id)
    return ok(message="Sender profile deleted")


@router.get("/recipients", response_model=ApiResponse)
def list_recipients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profiles = address_book_service.list_recipient_profiles(db, current_user)
    return ok(data=[RecipientProfileOut.model_validate(profile) for profile in profiles])


@router.post("/recipients", response_model=ApiResponse)
def create_recipient(
    payload: RecipientProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.create_recipient_profile(db, current_user, payload)
    return ok(data=RecipientProfileOut.model_validate(profile), message="Recipient profile created")


@router.put("/recipients/{profile_id}", response_model=ApiResponse)
def update_recipient(
    profile_id: int,
    payload: RecipientProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.update_recipient_profile(db, current_user, profile_id, payload)
    return ok(data=RecipientProfileOut.model_validate(profile), message="Recipient profile updated")


@router.put("/recipients/{profile_id}/default", response_model=ApiResponse)
def set_default_recipient(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    profile = address_book_service.set_default_recipient_profile(db, current_user, profile_id)
    return ok(data=RecipientProfileOut.model_validate(profile), message="Recipient default updated")


@router.delete("/recipients/{profile_id}", response_model=ApiResponse)
def delete_recipient(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    address_book_service.delete_recipient_profile(db, current_user, profile_id)
    return ok(message="Recipient profile deleted")


@router.get("/defaults", response_model=ApiResponse)
def get_defaults(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    sender = address_book_service.get_default_sender_profile(db, current_user)
    recipient = address_book_service.get_default_recipient_profile(db, current_user)
    return ok(
        data=AddressDefaultsOut(
            sender=SenderProfileOut.model_validate(sender) if sender else None,
            recipient=RecipientProfileOut.model_validate(recipient) if recipient else None,
        )
    )
