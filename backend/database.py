
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
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

# 1. Tạo engine TRƯỚC
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)

# 2. Sau khi có engine mới đăng ký sự kiện kiểm tra khóa ngoại
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection,
        connection_record,
    ):
        previous_autocommit = getattr(
            dbapi_connection,
            "autocommit",
            None,
        )

        if previous_autocommit is not None:
            dbapi_connection.autocommit = True

        cursor = dbapi_connection.cursor()

        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

            if previous_autocommit is not None:
                dbapi_connection.autocommit = previous_autocommit


# 3. Tạo đối tượng quản lý các phiên làm việc với database
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# 4. Lớp nền cho các bảng dữ liệu
class Base(DeclarativeBase):
    pass


# 5. Cung cấp database session cho các API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
