from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.database import User, UserRecipientProfile, UserSenderProfile
from app.models.schemas import (
    RecipientProfileCreate,
    RecipientProfileUpdate,
    SenderProfileCreate,
    SenderProfileUpdate,
)


def _clear_default_sender(db: Session, user_id: int) -> None:
    db.query(UserSenderProfile).filter(
        UserSenderProfile.user_id == user_id, UserSenderProfile.is_default.is_(True)
    ).update({UserSenderProfile.is_default: False}, synchronize_session=False)


def _clear_default_recipient(db: Session, user_id: int) -> None:
    db.query(UserRecipientProfile).filter(
        UserRecipientProfile.user_id == user_id, UserRecipientProfile.is_default.is_(True)
    ).update({UserRecipientProfile.is_default: False}, synchronize_session=False)


def list_sender_profiles(db: Session, user: User) -> list[UserSenderProfile]:
    return (
        db.query(UserSenderProfile)
        .filter(UserSenderProfile.user_id == user.id)
        .order_by(UserSenderProfile.is_default.desc(), UserSenderProfile.updated_at.desc())
        .all()
    )


def list_recipient_profiles(db: Session, user: User) -> list[UserRecipientProfile]:
    return (
        db.query(UserRecipientProfile)
        .filter(UserRecipientProfile.user_id == user.id)
        .order_by(UserRecipientProfile.is_default.desc(), UserRecipientProfile.updated_at.desc())
        .all()
    )


def create_sender_profile(db: Session, user: User, payload: SenderProfileCreate) -> UserSenderProfile:
    if payload.is_default:
        _clear_default_sender(db, user.id)

    profile = UserSenderProfile(
        user_id=user.id,
        profile_name=payload.profile_name,
        sender_name=payload.sender_name,
        sender_phone_code=payload.sender_phone_code,
        sender_phone=payload.sender_phone,
        pickup_point_id=payload.pickup_point_id,
        pickup_point_name=payload.pickup_point_name,
        domestic_tracking_no=payload.domestic_tracking_no,
        is_default=payload.is_default,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_recipient_profile(db: Session, user: User, payload: RecipientProfileCreate) -> UserRecipientProfile:
    if payload.is_default:
        _clear_default_recipient(db, user.id)

    profile = UserRecipientProfile(
        user_id=user.id,
        profile_name=payload.profile_name,
        recipient_name=payload.recipient_name,
        phone_code=payload.phone_code,
        phone=payload.phone,
        country_code=payload.country_code,
        country_name=payload.country_name,
        province=payload.province,
        city=payload.city,
        district=payload.district,
        street1=payload.street1,
        street2=payload.street2,
        postcode=payload.postcode,
        email=payload.email,
        id_type=payload.id_type,
        id_number=payload.id_number,
        is_default=payload.is_default,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def _get_sender_profile_for_user(db: Session, user: User, profile_id: int) -> UserSenderProfile:
    profile = (
        db.query(UserSenderProfile)
        .filter(UserSenderProfile.id == profile_id, UserSenderProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Sender profile not found")
    return profile


def _get_recipient_profile_for_user(db: Session, user: User, profile_id: int) -> UserRecipientProfile:
    profile = (
        db.query(UserRecipientProfile)
        .filter(UserRecipientProfile.id == profile_id, UserRecipientProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Recipient profile not found")
    return profile


def update_sender_profile(
    db: Session, user: User, profile_id: int, payload: SenderProfileUpdate
) -> UserSenderProfile:
    profile = _get_sender_profile_for_user(db, user, profile_id)

    if payload.is_default:
        _clear_default_sender(db, user.id)

    profile.profile_name = payload.profile_name
    profile.sender_name = payload.sender_name
    profile.sender_phone_code = payload.sender_phone_code
    profile.sender_phone = payload.sender_phone
    profile.pickup_point_id = payload.pickup_point_id
    profile.pickup_point_name = payload.pickup_point_name
    profile.domestic_tracking_no = payload.domestic_tracking_no
    profile.is_default = payload.is_default

    db.commit()
    db.refresh(profile)
    return profile


def update_recipient_profile(
    db: Session, user: User, profile_id: int, payload: RecipientProfileUpdate
) -> UserRecipientProfile:
    profile = _get_recipient_profile_for_user(db, user, profile_id)

    if payload.is_default:
        _clear_default_recipient(db, user.id)

    profile.profile_name = payload.profile_name
    profile.recipient_name = payload.recipient_name
    profile.phone_code = payload.phone_code
    profile.phone = payload.phone
    profile.country_code = payload.country_code
    profile.country_name = payload.country_name
    profile.province = payload.province
    profile.city = payload.city
    profile.district = payload.district
    profile.street1 = payload.street1
    profile.street2 = payload.street2
    profile.postcode = payload.postcode
    profile.email = payload.email
    profile.id_type = payload.id_type
    profile.id_number = payload.id_number
    profile.is_default = payload.is_default

    db.commit()
    db.refresh(profile)
    return profile


def set_default_sender_profile(db: Session, user: User, profile_id: int) -> UserSenderProfile:
    profile = _get_sender_profile_for_user(db, user, profile_id)
    _clear_default_sender(db, user.id)
    profile.is_default = True
    db.commit()
    db.refresh(profile)
    return profile


def set_default_recipient_profile(db: Session, user: User, profile_id: int) -> UserRecipientProfile:
    profile = _get_recipient_profile_for_user(db, user, profile_id)
    _clear_default_recipient(db, user.id)
    profile.is_default = True
    db.commit()
    db.refresh(profile)
    return profile


def delete_sender_profile(db: Session, user: User, profile_id: int) -> None:
    profile = _get_sender_profile_for_user(db, user, profile_id)
    db.delete(profile)
    db.commit()


def delete_recipient_profile(db: Session, user: User, profile_id: int) -> None:
    profile = _get_recipient_profile_for_user(db, user, profile_id)
    db.delete(profile)
    db.commit()


def get_default_sender_profile(db: Session, user: User) -> UserSenderProfile | None:
    return (
        db.query(UserSenderProfile)
        .filter(UserSenderProfile.user_id == user.id, UserSenderProfile.is_default.is_(True))
        .first()
    )


def get_default_recipient_profile(db: Session, user: User) -> UserRecipientProfile | None:
    return (
        db.query(UserRecipientProfile)
        .filter(UserRecipientProfile.user_id == user.id, UserRecipientProfile.is_default.is_(True))
        .first()
    )
