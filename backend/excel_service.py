"""
Dịch vụ đọc/kiểm tra file Excel (.xlsx) và CSV (.csv) thời khóa biểu (OFF-01).
Tương thích đồng thời:
- Mẫu chuẩn CAMS (class_code, course_name, lecturer, student_count, weekday, start_time, end_time / shift, room_code)
- Mẫu cũ theo course_name hoặc class_code
"""

from __future__ import annotations

import csv
from datetime import datetime, time
from io import BytesIO, StringIO
from typing import Any

from openpyxl import load_workbook

# Khung giờ chuẩn cho Ca 1 -> Ca 9 (ADM-03)
DEFAULT_SHIFT_TIMES: dict[int, tuple[str, str]] = {
    1: ("07:00:00", "09:30:00"),
    2: ("09:45:00", "12:00:00"),
    3: ("13:00:00", "15:30:00"),
    4: ("15:45:00", "18:00:00"),
    5: ("18:15:00", "20:15:00"),
    6: ("20:20:00", "21:50:00"),
    7: ("07:00:00", "08:40:00"),
    8: ("08:50:00", "10:30:00"),
    9: ("10:40:00", "12:15:00"),
}

COLUMN_ALIASES: dict[str, str] = {
    "class_code": "class_code",
    "ma_lop": "class_code",
    "mã lớp": "class_code",
    "mã lớp học phần": "class_code",
    "course_name": "course_name",
    "ten_mon": "course_name",
    "tên môn": "course_name",
    "tên môn học": "course_name",
    "môn học": "course_name",
    "lecturer": "lecturer",
    "giang_vien": "lecturer",
    "giảng viên": "lecturer",
    "tên giảng viên": "lecturer",
    "student_count": "student_count",
    "si_so": "student_count",
    "sĩ số": "student_count",
    "sĩ số sinh viên": "student_count",
    "weekday": "weekday",
    "thu": "weekday",
    "thứ": "weekday",
    "thứ trong tuần": "weekday",
    "shift": "shift",
    "ca": "shift",
    "ca học": "shift",
    "ca_hoc": "shift",
    "start_time": "start_time",
    "gio_bat_dau": "start_time",
    "giờ bắt đầu": "start_time",
    "end_time": "end_time",
    "gio_ket_thuc": "end_time",
    "giờ kết thúc": "end_time",
    "room_code": "room_code",
    "ma_phong": "room_code",
    "phòng": "room_code",
    "mã phòng": "room_code",
    "required_room_type": "required_room_type",
    "loai_phong": "required_room_type",
    "loại phòng": "required_room_type",
    "required_equipment": "required_equipment",
    "thiet_bi": "required_equipment",
    "thiết bị": "required_equipment",
}

WEEKDAY_TEXT_MAP: dict[str, int] = {
    "thứ 2": 1,
    "thu 2": 1,
    "thứ hai": 1,
    "t2": 1,
    "monday": 1,
    "thứ 3": 2,
    "thu 3": 2,
    "thứ ba": 2,
    "t3": 2,
    "tuesday": 2,
    "thứ 4": 3,
    "thu 4": 3,
    "thứ tư": 3,
    "t4": 3,
    "wednesday": 3,
    "thứ 5": 4,
    "thu 5": 4,
    "thứ năm": 4,
    "t5": 4,
    "thursday": 4,
    "thứ 6": 5,
    "thu 6": 5,
    "thứ sáu": 5,
    "t6": 5,
    "friday": 5,
    "thứ 7": 6,
    "thu 7": 6,
    "thứ bảy": 6,
    "t7": 6,
    "saturday": 6,
    "chủ nhật": 7,
    "chu nhat": 7,
    "cn": 7,
    "sunday": 7,
}


def parse_time(value: Any) -> str:
    """Chuyển dữ liệu thời gian Excel thành chuỗi HH:MM:SS."""
    if isinstance(value, datetime):
        value = value.time()

    if isinstance(value, time):
        return value.strftime("%H:%M:%S")

    if isinstance(value, str):
        cleaned = value.strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(cleaned, fmt).time().strftime("%H:%M:%S")
            except ValueError:
                pass
        try:
            parsed_time = time.fromisoformat(cleaned)
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            raise ValueError(f"Thời gian '{cleaned}' không đúng định dạng HH:MM")

    raise ValueError("Thời gian không hợp lệ")


def parse_weekday(value: Any) -> int:
    """Chuyển thứ trong tuần thành số nguyên từ 1 đến 7 (1 = Thứ Hai, 7 = Chủ nhật)."""
    if isinstance(value, bool) or value is None:
        raise ValueError("Thứ phải là số từ 1 đến 7 (1 = Thứ 2, ..., 7 = CN)")

    if isinstance(value, str):
        key = value.strip().casefold()
        if key in WEEKDAY_TEXT_MAP:
            return WEEKDAY_TEXT_MAP[key]

    try:
        number = int(value)
        if float(value) != number:
            raise ValueError()
        if 1 <= number <= 7:
            return number
        raise ValueError()
    except (ValueError, TypeError):
        raise ValueError("Thứ phải là số nguyên từ 1 đến 7 (hoặc 'Thứ 2'..'CN')")


def parse_shift(value: Any) -> tuple[str, str]:
    """Chuyển Ca học (1..9 hoặc 'Ca 1'..'Ca 9') thành cặp (start_time, end_time)."""
    if value is None or isinstance(value, bool):
        raise ValueError("Ca học không hợp lệ (1–9)")
    raw = str(value).strip().casefold()
    if raw.startswith("ca"):
        raw = raw.replace("ca", "", 1).strip()
    if "·" in raw:
        raw = raw.split("·", 1)[0].strip()
    try:
        shift_no = int(float(raw))
    except ValueError:
        raise ValueError(f"Ca học '{value}' không hợp lệ (chấp nhận Ca 1 – Ca 9)")

    if shift_no not in DEFAULT_SHIFT_TIMES:
        raise ValueError(f"Ca học {shift_no} nằm ngoài phạm vi Ca 1 – Ca 9")
    return DEFAULT_SHIFT_TIMES[shift_no]


def _normalize_headers(raw_headers: tuple[Any, ...] | list[Any]) -> dict[str, int]:
    positions: dict[str, int] = {}
    for idx, val in enumerate(raw_headers):
        if val is None:
            continue
        key = str(val).strip().casefold()
        canonical = COLUMN_ALIASES.get(key)
        if canonical and canonical not in positions:
            positions[canonical] = idx
    return positions


def _extract_raw_rows(file_content: bytes, filename: str = "timetable.xlsx") -> tuple[list[Any], list[tuple[Any, ...]]]:
    if filename.lower().endswith(".csv"):
        text = file_content.decode("utf-8-sig")
        reader = list(csv.reader(StringIO(text)))
        if not reader:
            return [], []
        return reader[0], [tuple(r) for r in reader[1:]]

    workbook = load_workbook(
        filename=BytesIO(file_content),
        read_only=True,
        data_only=True,
    )
    try:
        worksheet = workbook.active
        if worksheet is None:
            raise ValueError("File Excel không có worksheet")
        all_rows = list(worksheet.iter_rows(values_only=True))
        if not all_rows:
            return [], []
        return list(all_rows[0]), list(all_rows[1:])
    finally:
        workbook.close()


def read_timetable_excel(file_content: bytes, filename: str = "timetable.xlsx") -> dict[str, list[dict[str, Any]]]:
    """
    Đọc file Excel (.xlsx) hoặc CSV (.csv) và kiểm tra cấu trúc cơ bản.
    Trả về {"rows": [...], "errors": [...]}.
    """
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    try:
        raw_headers, data_rows = _extract_raw_rows(file_content, filename=filename)
        if not raw_headers:
            return {
                "rows": [],
                "errors": [{"row": 1, "message": "File không có dòng tiêu đề cột"}],
            }

        col = _normalize_headers(raw_headers)

        missing: list[str] = []
        if "class_code" not in col and "course_name" not in col:
            missing.append("class_code (hoặc course_name)")
        if "weekday" not in col:
            missing.append("weekday")
        if "shift" not in col and ("start_time" not in col or "end_time" not in col):
            missing.append("start_time + end_time (hoặc shift)")

        if missing:
            return {
                "rows": [],
                "errors": [{"row": 1, "message": "Thiếu các cột bắt buộc: " + ", ".join(missing)}],
            }

        def cell(values: tuple[Any, ...], name: str) -> Any:
            idx = col.get(name)
            if idx is None or idx >= len(values):
                return None
            return values[idx]

        for row_number, values in enumerate(data_rows, start=2):
            if all(v is None or str(v).strip() == "" for v in values):
                continue

            try:
                raw_code = cell(values, "class_code")
                class_code = str(raw_code).strip() if raw_code is not None and str(raw_code).strip() else None

                raw_course = cell(values, "course_name")
                course_name = str(raw_course).strip() if raw_course is not None and str(raw_course).strip() else None

                if not class_code and not course_name:
                    raise ValueError("Mã lớp học phần hoặc Tên môn học không được để trống")

                weekday = parse_weekday(cell(values, "weekday"))

                raw_start = cell(values, "start_time")
                raw_end = cell(values, "end_time")
                raw_shift = cell(values, "shift")

                if raw_start is not None and str(raw_start).strip() != "" and raw_end is not None and str(raw_end).strip() != "":
                    start_time = parse_time(raw_start)
                    end_time = parse_time(raw_end)
                elif raw_shift is not None and str(raw_shift).strip() != "":
                    start_time, end_time = parse_shift(raw_shift)
                else:
                    raise ValueError("Thiếu giờ bắt đầu/kết thúc hoặc ca học")

                if end_time <= start_time:
                    raise ValueError("Giờ kết thúc phải sau giờ bắt đầu")

                raw_room = cell(values, "room_code")
                room_code = str(raw_room).strip() if raw_room is not None and str(raw_room).strip() else None

                raw_lecturer = cell(values, "lecturer")
                lecturer = str(raw_lecturer).strip() if raw_lecturer is not None and str(raw_lecturer).strip() else None

                raw_count = cell(values, "student_count")
                student_count: int | None = None
                if raw_count is not None and str(raw_count).strip() != "":
                    try:
                        student_count = int(float(raw_count))
                        if student_count <= 0:
                            raise ValueError()
                    except ValueError:
                        raise ValueError("Sĩ số sinh viên phải là số nguyên dương")

                raw_type = cell(values, "required_room_type")
                required_room_type = (
                    str(raw_type).strip()
                    if raw_type is not None and str(raw_type).strip()
                    else None
                )

                raw_eq = cell(values, "required_equipment")
                required_equipment = (
                    str(raw_eq).strip()
                    if raw_eq is not None and str(raw_eq).strip()
                    else None
                )

                rows.append(
                    {
                        "class_code": class_code,
                        "course_name": course_name,
                        "lecturer": lecturer,
                        "student_count": student_count,
                        "weekday": weekday,
                        "start_time": start_time,
                        "end_time": end_time,
                        "room_code": room_code,
                        "required_room_type": required_room_type,
                        "required_equipment": required_equipment,
                    }
                )
            except (ValueError, TypeError, IndexError) as exc:
                errors.append({"row": row_number, "message": str(exc)})

    except Exception as exc:
        return {
            "rows": [],
            "errors": [{"row": 0, "message": f"Không thể đọc file: {exc}"}],
        }

    return {"rows": rows, "errors": errors}
