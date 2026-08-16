from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.database.models import User
from app.schemas.auth import UserRegister


def register_user(db: Session, user_in: UserRegister) -> User:
    """Register a new user after verifying username and email uniqueness."""
    # Check existing username
    existing_username = db.execute(
        select(User).where(User.username == user_in.username)
    ).scalar_one_or_none()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already registered"
        )

    # Check existing email
    existing_email = db.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered"
        )

    # Hash plain text password with Argon2
    hashed_pwd = get_password_hash(user_in.password)
    
    # Create User instance
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pwd
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password."""
    statement = select(User).where(User.username == username)
    user = db.execute(statement).scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
        
    return user
