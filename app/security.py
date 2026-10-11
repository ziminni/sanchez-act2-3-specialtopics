import hashlib
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_db
from .models import Token, User, now

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)
DUMMY_HASH = password_hash.hash('unused-dummy-password-for-timing')


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not credentials:
        raise HTTPException(401, 'Authentication required.', headers={'WWW-Authenticate': 'Bearer'})
    token = db.scalar(select(Token).where(Token.digest == digest_token(credentials.credentials), Token.expires_at > now()))
    user = db.get(User, token.user_id) if token else None
    if not user or user.status != 'ACTIVE':
        raise HTTPException(401, 'Invalid or expired token.', headers={'WWW-Authenticate': 'Bearer'})
    return user


def require_staff(user):
    if user.role not in {'ADMIN', 'REGISTRAR'}:
        raise HTTPException(403, 'This action requires administrator or registrar access.')
