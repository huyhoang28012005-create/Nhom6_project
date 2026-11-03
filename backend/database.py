
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Đọc cấu hình từ file .env nếu có
load_dotenv()

# Dùng SQLite khi chưa cấu hình database khác
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./cams.db",
)

# SQLite cần cấu hình riêng khi sử dụng với FastAPI
connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

# Tạo đối tượng quản lý các phiên làm việc với database
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# Lớp nền cho các bảng dữ liệu sau này
class Base(DeclarativeBase):
    pass


# Cung cấp database session cho các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
