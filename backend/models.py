from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)

from database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Room(Base):
    __tablename__ = "rooms"

    __table_args__ = (
        CheckConstraint(
            "capacity > 0",
            name="ck_rooms_capacity_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    room_code = Column(String(20), unique=True, nullable=False)
    building = Column(String(100), nullable=False)
    floor = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=False)

    room_type = Column(
        String(50),
        nullable=False,
        default="classroom",
    )

    equipment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class CourseClass(Base):
    __tablename__ = "course_classes"

    __table_args__ = (
        CheckConstraint(
            "student_count > 0",
            name="ck_course_classes_student_count_positive",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    class_code = Column(String(30), unique=True, nullable=False)
    course_name = Column(String(150), nullable=False)
    lecturer = Column(String(100), nullable=True)
    student_count = Column(Integer, nullable=False)

    required_room_type = Column(
        String(50),
        nullable=False,
        default="classroom",
    )

    required_equipment = Column(Text, nullable=True)


class TimetableSession(Base):
    __tablename__ = "timetable_sessions"

    __table_args__ = (
        CheckConstraint(
            "weekday >= 1 AND weekday <= 7",
            name="ck_timetable_sessions_weekday",
        ),
        CheckConstraint(
            "end_time > start_time",
            name="ck_timetable_sessions_time",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    class_id = Column(
        Integer,
        ForeignKey("course_classes.id"),
        nullable=False,
        index=True,
    )

    weekday = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id"),
        nullable=True,
        index=True,
    )


class StudentEnrollment(Base):
    """Bảng đăng ký lớp học phần của sinh viên phục vụ tra cứu nhanh theo MSSV (STU-01)."""

    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_code = Column(String(30), nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    administrative_class = Column(String(50), nullable=True)
    department = Column(String(100), nullable=True)
    class_id = Column(
        Integer,
        ForeignKey("course_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class ShiftConfig(Base):
    """Cấu hình khung thời gian & ca tiết học chuẩn của trường (ADM-03)."""

    __tablename__ = "shift_configs"

    id = Column(Integer, primary_key=True, index=True)
    shift_number = Column(Integer, unique=True, nullable=False)
    shift_name = Column(String(50), nullable=False)
    period_range = Column(String(50), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)


class SystemSetting(Base):
    """Cài đặt mốc thời hạn First Closure Date & Final Closure Date (ADM-04, BR-03)."""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    semester_name = Column(String(100), nullable=False, default="Học kỳ 1 · Năm học 2026–2027")
    first_closure_date = Column(String(20), nullable=False, default="2026-12-15")
    final_closure_date = Column(String(20), nullable=False, default="2026-12-31")
    enforce_closure = Column(Boolean, nullable=False, default=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RoomChangeRequest(Base):
    """Đơn xin đổi phòng học của giảng viên (LEC-03, LEC-04, OFF-07)."""

    __tablename__ = "room_change_requests"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer,
        ForeignKey("timetable_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lecturer_name = Column(String(100), nullable=False)
    requester_username = Column(String(50), nullable=True)
    old_room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    requested_room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED
    reject_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    reviewed_at = Column(DateTime, nullable=True)


class RoomBooking(Base):
    """Yêu cầu đặt/mượn phòng học nhóm hoặc học bù trên cổng thông tin."""

    __tablename__ = "room_bookings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_username = Column(String(50), nullable=False, index=True)
    requester_name = Column(String(100), nullable=False)
    use_date = Column(String(20), nullable=False)
    shift_label = Column(String(50), nullable=False)
    attendee_count = Column(Integer, nullable=False)
    purpose = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING, APPROVED, REJECTED, CANCELLED
    created_at = Column(DateTime, default=utcnow)


class IssueReport(Base):
    """Báo cáo sự cố cơ sở vật chất / thiết bị phòng học."""

    __tablename__ = "issue_reports"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    room_name = Column(String(100), nullable=False)
    reporter_name = Column(String(100), nullable=False)
    issue_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="RECEIVED")  # RECEIVED, IN_PROGRESS, RESOLVED
    created_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    """Nhật ký kiểm toán hệ thống bất biến (ADM-05, BR-04)."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, nullable=True)
    actor_name = Column(String(100), nullable=False)
    actor_role = Column(String(30), nullable=False)
    action = Column(String(50), nullable=False, index=True)
    target = Column(String(150), nullable=False)
    old_value = Column(String(150), nullable=True)
    new_value = Column(String(150), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, index=True)


class Notification(Base):
    """Thông báo biến động phòng học & kết quả phê duyệt (STU-03, LEC-04)."""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    target_role = Column(String(30), nullable=True)
    target_username = Column(String(50), nullable=True)
    category = Column(String(50), nullable=False)
    tone = Column(String(10), nullable=False, default="b")
    message = Column(Text, nullable=False)
    is_unread = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utcnow, index=True)


class NotificationRead(Base):
    """Lưu trạng thái đã đọc thông báo riêng cho từng người dùng."""

    __tablename__ = "notification_reads"

    __table_args__ = (
        UniqueConstraint(
            "notification_id",
            "user_id",
            name="uq_notification_reads_notification_user",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    notification_id = Column(
        Integer,
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    read_at = Column(DateTime, nullable=False, default=utcnow)
