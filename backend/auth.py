"""
CAMS - Classroom Allocation Management System
Module: Authentication & Role-Based Access Control (RBAC) + ADM-01 User Management
Author: Dang Huy Hoang (Full-stack / DevOps Engineer - Nhom 6)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time as time_mod
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import Session

from database import Base, get_db
from models import AuditLog

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    os.getenv("AUTH_SECRET_KEY", "cams_nhom6_secret_key_2026_scrum_do_not_share"),
)
TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) * 60

ROLE_ADMIN = "ADMIN"
ROLE_OFFICER = "OFFICER"
ROLE_LECTURER = "LECTURER"
ROLE_STUDENT = "STUDENT"

ALL_ROLES = [ROLE_ADMIN, ROLE_OFFICER, ROLE_LECTURER, ROLE_STUDENT]


# ==============================================================================
# 1. BĂM MẬT KHẨU PBKDF2-HMAC-SHA256 & HMAC TOKEN (ZERO DEPENDENCY)
# ==============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> str:
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode("utf-8")
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"{salt}${base64.b64encode(key).decode('utf-8')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, _ = hashed_password.split("$", 1)
        expected = hash_password(plain_password, salt=salt)
        return hmac.compare_digest(expected, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_in: int = TOKEN_EXPIRE_SECONDS) -> str:
    payload = data.copy()
    payload["exp"] = int(time_mod.time()) + expires_in
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    payload_b64 = (
        base64.urlsafe_b64encode(payload_json.encode("utf-8"))
        .decode("utf-8")
        .rstrip("=")
    )
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.strip().split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts

        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            payload_b64.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        rem = len(sig_b64) % 4
        if rem > 0:
            sig_b64 += "=" * (4 - rem)
        actual_sig = base64.urlsafe_b64decode(sig_b64.encode("utf-8"))

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        rem_p = len(payload_b64) % 4
        if rem_p > 0:
            payload_b64 += "=" * (4 - rem_p)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode("utf-8")).decode("utf-8")
        payload = json.loads(payload_json)

        if payload.get("exp", 0) < int(time_mod.time()):
            return None

        return payload
    except Exception:
        return None


# ==============================================================================
# 2. MODEL CSDL USER & PYDANTIC SCHEMAS (ADM-01)
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default=ROLE_STUDENT)
    student_code = Column(String(30), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=100)
    email: Optional[str] = None
    student_code: Optional[str] = None
    department: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=1, max_length=100)
    email: Optional[str] = None
    role: str = ROLE_STUDENT
    student_code: Optional[str] = None
    department: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[str] = None
    role: Optional[str] = None
    student_code: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=3, max_length=100)


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    student_code: Optional[str] = None
    department: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse


def write_audit_log(
    db: Session,
    user: Optional[User],
    action: str,
    target: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    reason: Optional[str] = None,
) -> None:
    log = AuditLog(
        actor_id=user.id if user else None,
        actor_name=user.full_name if user else "Hệ thống",
        actor_role=user.role if user else "SYSTEM",
        action=action,
        target=target,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )
    db.add(log)


# ==============================================================================
# 3. RBAC DEPENDENCIES CHO FASTAPI
# ==============================================================================

def _extract_raw_token(
    authorization: Optional[str],
    query_token: Optional[str],
) -> Optional[str]:
    if authorization:
        parts = authorization.strip().split(" ")
        return parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization.strip()
    if query_token:
        return query_token.strip()
    return None


def get_optional_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> Optional[User]:
    raw_token = _extract_raw_token(authorization, token)
    if not raw_token:
        return None
    payload = decode_access_token(raw_token)
    if not payload:
        return None
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_current_user(
    authorization: Optional[str] = Header(None),
    token: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> User:
    raw_token = _extract_raw_token(authorization, token)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập: Không tìm thấy Authorization Bearer token",
        )

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên làm việc không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )
    return user


def require_role(allowed_roles: List[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Truy cập bị từ chối: Chức năng này chỉ dành cho vai trò {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


# ==============================================================================
# 4. FASTAPI ROUTER: AUTH & QUẢN TRỊ TÀI KHOẢN (ADM-01)
# ==============================================================================

auth_router = APIRouter(prefix="/api/auth", tags=["Auth & RBAC (ADM-01)"])


DEMO_ACCOUNTS = [
    {
        "username": "admin",
        "password": "123",
        "full_name": "Quản trị viên Hệ thống",
        "role": ROLE_ADMIN,
        "email": "admin@cams.edu.vn",
        "department": "Trung tâm CNTT",
        "student_code": None,
    },
    {
        "username": "officer01",
        "password": "123",
        "full_name": "Lê Thu Trang (Cán bộ Đào tạo)",
        "role": ROLE_OFFICER,
        "email": "daotao@cams.edu.vn",
        "department": "Phòng Đào tạo",
        "student_code": None,
    },
    {
        "username": "gv_an",
        "password": "123",
        "full_name": "TS. Nguyễn Văn An",
        "role": ROLE_LECTURER,
        "email": "an.nv@cams.edu.vn",
        "department": "Khoa Công nghệ thông tin",
        "student_code": None,
    },
    {
        "username": "sv_minhanh",
        "password": "123",
        "full_name": "Nguyễn Minh Anh",
        "role": ROLE_STUDENT,
        "email": "minhanh@cams.edu.vn",
        "department": "Khoa Công nghệ thông tin · K66-CNTT2",
        "student_code": "21021234",
    },
]


def ensure_demo_users(db: Session) -> list[str]:
    created: list[str] = []
    for acc in DEMO_ACCOUNTS:
        existing = db.query(User).filter(User.username == acc["username"]).first()
        if not existing:
            db.add(
                User(
                    username=acc["username"],
                    hashed_password=hash_password(acc["password"]),
                    full_name=acc["full_name"],
                    email=acc["email"],
                    role=acc["role"],
                    department=acc["department"],
                    student_code=acc["student_code"],
                    is_active=True,
                )
            )
            created.append(acc["username"])
    if created:
        db.commit()
    return created


@auth_router.post("/login", response_model=LoginResponse, summary="Đăng nhập nhận Token")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    identifier = creds.username.strip()
    user = (
        db.query(User)
        .filter(
            (User.username == identifier)
            | (User.email == identifier)
            | (User.student_code == identifier)
        )
        .first()
    )
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đang bị tạm khóa. Vui lòng liên hệ Admin.",
        )

    token = create_access_token(
        {
            "sub": user.id,
            "username": user.username,
            "role": user.role,
        }
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user,
    }


@auth_router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_student_account(body: RegisterRequest, db: Session = Depends(get_db)):
    username = body.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại")
    user = User(
        username=username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        email=body.email.strip() if body.email else None,
        role=ROLE_STUDENT,
        student_code=body.student_code.strip() if body.student_code else username,
        department=body.department.strip() if body.department else "Sinh viên",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@auth_router.get("/me", response_model=UserResponse, summary="Lấy thông tin người dùng hiện tại")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.get("/users", response_model=List[UserResponse], summary="Danh sách tài khoản (Chỉ Admin)")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role([ROLE_ADMIN])),
):
    return db.query(User).order_by(User.id).all()


@auth_router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo tài khoản mới (ADM-01 - Chỉ Admin)",
)
def create_user_by_admin(
    body: UserCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([ROLE_ADMIN])),
):
    role = body.role.strip().upper()
    if role not in ALL_ROLES:
        raise HTTPException(status_code=422, detail=f"Vai trò phải thuộc {ALL_ROLES}")
    username = body.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=409, detail="Tên đăng nhập đã tồn tại")

    new_user = User(
        username=username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        email=body.email.strip() if body.email else None,
        role=role,
        student_code=body.student_code.strip() if body.student_code else None,
        department=body.department.strip() if body.department else None,
        is_active=True,
    )
    db.add(new_user)
    write_audit_log(
        db,
        admin_user,
        action="CREATE_USER",
        target=f"User @{username}",
        new_value=role,
        reason="Quản trị viên tạo tài khoản mới",
    )
    db.commit()
    db.refresh(new_user)
    return new_user


@auth_router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Cập nhật thông tin & phân quyền tài khoản (ADM-01 - Chỉ Admin)",
)
def update_user_by_admin(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([ROLE_ADMIN])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    old_role = user.role
    if body.role is not None:
        role = body.role.strip().upper()
        if role not in ALL_ROLES:
            raise HTTPException(status_code=422, detail=f"Vai trò phải thuộc {ALL_ROLES}")
        if user.id == admin_user.id and role != ROLE_ADMIN:
            raise HTTPException(status_code=409, detail="Không thể tự hạ quyền Admin của chính mình")
        user.role = role

    if body.is_active is not None:
        if user.id == admin_user.id and not body.is_active:
            raise HTTPException(status_code=409, detail="Không thể tự khóa tài khoản của chính mình")
        user.is_active = body.is_active

    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.email is not None:
        user.email = body.email.strip() or None
    if body.student_code is not None:
        user.student_code = body.student_code.strip() or None
    if body.department is not None:
        user.department = body.department.strip() or None

    write_audit_log(
        db,
        admin_user,
        action="UPDATE_USER",
        target=f"User @{user.username}",
        old_value=f"{old_role}",
        new_value=f"{user.role} ({'Active' if user.is_active else 'Locked'})",
        reason="Cập nhật hồ sơ / quyền người dùng",
    )
    db.commit()
    db.refresh(user)
    return user


@auth_router.post(
    "/users/{user_id}/reset-password",
    summary="Cấp lại mật khẩu người dùng (ADM-01 - Chỉ Admin)",
)
def reset_user_password(
    user_id: int,
    body: PasswordResetRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([ROLE_ADMIN])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    user.hashed_password = hash_password(body.new_password)
    write_audit_log(
        db,
        admin_user,
        action="RESET_PASSWORD",
        target=f"User @{user.username}",
        reason="Admin cấp lại mật khẩu",
    )
    db.commit()
    return {"message": f"Đã cấp lại mật khẩu cho tài khoản {user.username}"}


@auth_router.patch(
    "/users/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Khóa / Mở khóa tài khoản (ADM-01 - Chỉ Admin)",
)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([ROLE_ADMIN])),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if user.id == admin_user.id:
        raise HTTPException(status_code=409, detail="Không thể tự khóa tài khoản của chính mình")

    old_state = "Active" if user.is_active else "Locked"
    user.is_active = not user.is_active
    new_state = "Active" if user.is_active else "Locked"
    write_audit_log(
        db,
        admin_user,
        action="TOGGLE_USER_STATUS",
        target=f"User @{user.username}",
        old_value=old_state,
        new_value=new_state,
    )
    db.commit()
    db.refresh(user)
    return user


@auth_router.post("/seed", summary="Khởi tạo 04 tài khoản mẫu để nghiệm thu Sprint")
def seed_demo_users_endpoint(db: Session = Depends(get_db)):
    created = ensure_demo_users(db)
    return {
        "message": "Đã khởi tạo thành công tài khoản mẫu 4 vai trò",
        "created_users": created,
        "accounts": [
            {"username": a["username"], "password": a["password"], "role": a["role"], "full_name": a["full_name"]}
            for a in DEMO_ACCOUNTS
        ],
    }
