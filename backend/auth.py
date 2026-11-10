"""
CAMS - Classroom Allocation Management System
Module: Authentication & Role-Based Access Control (RBAC)
Author: Dang Huy Hoang (Full-stack / DevOps Engineer - Nhom 6)
Description:
    Module cung cấp cơ chế Xác thực (Login / Token) và Phân quyền (RBAC)
    cho 04 vai trò: ADMIN, OFFICER, LECTURER, STUDENT.
    Tương thích 100% với cấu trúc FastAPI + SQLAlchemy + SQLite của Pham Minh Giang.
"""

import os
import time
import base64
import hmac
import hashlib
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Session
from datetime import datetime, timezone

# Khóa bí mật dùng ký token (trong thực tế có thể đọc từ .env)
SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "cams_nhom6_secret_key_2026_scrum_do_not_share")
TOKEN_EXPIRE_SECONDS = 7200  # Token hết hạn sau 2 giờ

# 4 Vai trò chuẩn hóa trong hệ thống CAMS
ROLE_ADMIN = "ADMIN"        # Quản trị viên hệ thống
ROLE_OFFICER = "OFFICER"    # Cán bộ / Nhân viên đào tạo
ROLE_LECTURER = "LECTURER"  # Giảng viên
ROLE_STUDENT = "STUDENT"    # Sinh viên

ALL_ROLES = [ROLE_ADMIN, ROLE_OFFICER, ROLE_LECTURER, ROLE_STUDENT]


# ==============================================================================
# 1. HÀM BĂM MẬT KHẨU & TẠO TOKEN TỰ THÂN (ZERO DEPENDENCY)
# ==============================================================================

def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Băm mật khẩu bằng PBKDF2-HMAC-SHA256 (chuẩn an toàn, không cần thư viện ngoài)."""
    if not salt:
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${base64.b64encode(key).decode('utf-8')}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác thực mật khẩu người dùng nhập với chuỗi băm trong CSDL."""
    try:
        salt, _ = hashed_password.split('$', 1)
        expected = hash_password(plain_password, salt=salt)
        return hmac.compare_digest(expected, hashed_password)
    except Exception:
        return False


def create_access_token(data: dict, expires_in: int = TOKEN_EXPIRE_SECONDS) -> str:
    """
    Tạo token xác thực dạng HMAC Token (cấu trúc tương đương JWT: header.payload.signature).
    Tự sinh và xác thực không phụ thuộc vào gói pyjwt hay python-jose.
    """
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in

    payload_json = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Giải mã và kiểm tra tính hợp lệ của token."""
    try:
        parts = token.strip().split('.')
        if len(parts) != 2:
            return None
        payload_b64, sig_b64 = parts

        # Kiểm tra chữ ký hợp lệ
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Thêm padding cho base64 nếu cần
        rem = len(sig_b64) % 4
        if rem > 0:
            sig_b64 += '=' * (4 - rem)
        actual_sig = base64.urlsafe_b64decode(sig_b64.encode('utf-8'))

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Đọc dữ liệu payload
        rem_p = len(payload_b64) % 4
        if rem_p > 0:
            payload_b64 += '=' * (4 - rem_p)
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)

        # Kiểm tra token đã hết hạn chưa
        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


# ==============================================================================
# 2. MODEL CSDL USER & PYDANTIC SCHEMAS
# ==============================================================================

# Nếu đã có Base từ database.py của Giang thì import, nếu chưa thì tạo độc lập
try:
    from database import Base, get_db
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
    def get_db():
        raise NotImplementedError("Vui lòng truyền session database từ CAMS backend")


class User(Base):
    """Bảng người dùng và vai trò phân quyền."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default=ROLE_STUDENT)  # ADMIN, OFFICER, LECTURER, STUDENT
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = None
    role: str = ROLE_STUDENT


class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserResponse


# ==============================================================================
# 3. TRẠM GÁC CỔNG BẢO MẬT (RBAC DEPENDENCIES CHO FASTAPI)
# ==============================================================================

def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Middleware Dependency: Bắt buộc request phải có Header 'Authorization: Bearer <token>'
    hoặc trả về mã lỗi 401 Unauthorized nếu thiếu/hết hạn.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập: Không tìm thấy Authorization header"
        )
    
    parts = authorization.split(" ")
    token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else authorization

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên làm việc không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị vô hiệu hóa"
        )
    return user


def require_role(allowed_roles: List[str]):
    """
    Dependency Factory: Kiểm tra quyền hạn vai trò (RBAC).
    Nếu vai trò hiện tại không nằm trong danh sách cho phép -> Trả về 403 Forbidden.
    
    Cách dùng trên các endpoint:
        @app.post("/api/rooms", dependencies=[Depends(require_role(["ADMIN", "OFFICER"]))])
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Truy cập bị từ chối: Chức năng này chỉ dành cho vai trò: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# ==============================================================================
# 4. FASTAPI ROUTER: CÁC API AUTH & QUẢN TRỊ USER
# ==============================================================================

auth_router = APIRouter(prefix="/api/auth", tags=["1. Xác thực & Phân quyền (Auth/RBAC)"])


@auth_router.post("/login", response_model=LoginResponse, summary="Đăng nhập nhận Token")
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Xác thực tài khoản và cấp Access Token mang theo Role."""
    user = db.query(User).filter(User.username == creds.username.strip()).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đang bị tạm khóa. Vui lòng liên hệ Admin."
        )

    # Sinh token chứa ID và Role
    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "Bearer",
        "user": user
    }


@auth_router.get("/me", response_model=UserResponse, summary="Lấy thông tin người dùng hiện tại")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Kiểm tra token còn hạn hay không và trả về thông tin người dùng đang đăng nhập."""
    return current_user


@auth_router.get("/users", response_model=List[UserResponse], summary="Danh sách tài khoản (Chỉ Admin)")
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role([ROLE_ADMIN]))
):
    """Chỉ tài khoản ADMIN mới có quyền xem danh sách người dùng trong hệ thống."""
    return db.query(User).order_by(User.id).all()


@auth_router.post("/seed", summary="Khởi tạo 04 tài khoản mẫu để nghiệm thu Sprint")
def seed_demo_users(db: Session = Depends(get_db)):
    """Khởi tạo nhanh 4 tài khoản đại diện cho 4 vai trò để phục vụ kiểm thử."""
    demo_accounts = [
        {"username": "admin", "password": "123", "full_name": "Quản trị viên Hệ thống", "role": ROLE_ADMIN, "email": "admin@cams.edu.vn"},
        {"username": "officer01", "password": "123", "full_name": "Cán bộ Đào tạo Duy", "role": ROLE_OFFICER, "email": "daotao@cams.edu.vn"},
        {"username": "gv_quang", "password": "123", "full_name": "TS. Phạm Minh Quang", "role": ROLE_LECTURER, "email": "quang.pm@cams.edu.vn"},
        {"username": "sv_hoang", "password": "123", "full_name": "Sinh viên Đặng Huy Hoàng", "role": ROLE_STUDENT, "email": "hoang.dh@cams.edu.vn"},
    ]

    created = []
    for acc in demo_accounts:
        existing = db.query(User).filter(User.username == acc["username"]).first()
        if not existing:
            new_u = User(
                username=acc["username"],
                hashed_password=hash_password(acc["password"]),
                full_name=acc["full_name"],
                email=acc["email"],
                role=acc["role"]
            )
            db.add(new_u)
            created.append(acc["username"])
    
    db.commit()
    return {
        "message": "Đã khởi tạo thành công tài khoản mẫu",
        "created_users": created,
        "default_password_all": "123"
    }
