from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import User, RoleEnum, AuditLog
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserOut
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if payload.role not in [r.value for r in RoleEnum]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(AuditLog(user_id=user.id, action="register", entity="user", entity_id=user.id))
    db.commit()
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    access = create_access_token(user.id, user.role.value)
    refresh = create_refresh_token(user.id, user.role.value)
    db.add(AuditLog(user_id=user.id, action="login", entity="user", entity_id=user.id))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == data["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    access = create_access_token(user.id, user.role.value)
    new_refresh = create_refresh_token(user.id, user.role.value)
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(AuditLog(user_id=user.id, action="logout", entity="user", entity_id=user.id))
    db.commit()
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
