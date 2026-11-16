
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Time,
    ForeignKey,
    CheckConstraint,
)

from database import Base


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
