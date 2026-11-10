
from datetime import datetime, time
from io import BytesIO

from openpyxl import load_workbook


# Các cột bắt buộc trong file Excel
REQUIRED_COLUMNS = [
    "course_name",
    "weekday",
    "start_time",
    "end_time",
    "room_code",
]


def parse_time(value):
    """
    Chuyển dữ liệu thời gian Excel thành chuỗi HH:MM:SS.
    Hỗ trợ datetime.time, datetime và chuỗi thời gian.
    """

    if isinstance(value, datetime):
        value = value.time()

    if isinstance(value, time):
        return value.strftime("%H:%M:%S")

    if isinstance(value, str):
        value = value.strip()

        try:
            parsed_time = time.fromisoformat(value)
            return parsed_time.strftime("%H:%M:%S")
        except ValueError:
            raise ValueError("Thời gian không đúng định dạng")

    raise ValueError("Thời gian không hợp lệ")


def parse_weekday(value):
    """
    Chuyển thứ trong tuần thành số nguyên từ 1 đến 7.
    Quy ước: 1 = Thứ Hai, 7 = Chủ nhật.
    """

    if isinstance(value, bool):
        raise ValueError("Thứ phải là số từ 1 đến 7")

    try:
        number = int(value)

        if float(value) != number:
            raise ValueError()

        if number < 1 or number > 7:
            raise ValueError()

        return number

    except (ValueError, TypeError):
        raise ValueError("Thứ phải là số nguyên từ 1 đến 7")


def read_timetable_excel(file_content: bytes):
    """
    Đọc file Excel và kiểm tra cấu trúc, dữ liệu cơ bản.

    Kết quả trả về:
    {
        "rows": [...],
        "errors": [...]
    }
    """

    rows = []
    errors = []

    try:
        workbook = load_workbook(
            filename=BytesIO(file_content),
            read_only=True,
            data_only=True,
        )

        worksheet = workbook.active

        if worksheet is None:
            return {
                "rows": [],
                "errors": [
                    {
                        "row": 1,
                        "message": "File Excel không có worksheet",
                    }
                ],
            }

        headers = [
            str(value).strip().lower() if value is not None else ""
            for value in next(
                worksheet.iter_rows(
                    min_row=1,
                    max_row=1,
                    values_only=True,
                ),
                (),
            )
        ]

        # Kiểm tra các cột bắt buộc
        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in headers
        ]

        if missing_columns:
            return {
                "rows": [],
                "errors": [
                    {
                        "row": 1,
                        "message": (
                            "Thiếu các cột: "
                            + ", ".join(missing_columns)
                        ),
                    }
                ],
            }

        # Lấy vị trí của từng cột
        column_positions = {
            column: headers.index(column)
            for column in REQUIRED_COLUMNS
        }

        # Đọc từng dòng dữ liệu
        for row_number, values in enumerate(
            worksheet.iter_rows(
                min_row=2,
                values_only=True,
            ),
            start=2,
        ):

            # Bỏ qua dòng trống
            if all(
                value is None or str(value).strip() == ""
                for value in values
            ):
                continue

           
            try:
                course_name = values[
                    column_positions["course_name"]
                ]

                if course_name is None or not str(course_name).strip():
                    raise ValueError("Tên môn học không được để trống")

                weekday = parse_weekday(
                    values[column_positions["weekday"]]
                )

                start_time = parse_time(
                    values[column_positions["start_time"]]
                )

                end_time = parse_time(
                    values[column_positions["end_time"]]
                )

                if end_time <= start_time:
                    raise ValueError(
                        "Giờ kết thúc phải sau giờ bắt đầu"
                    )

                room_code = values[
                    column_positions["room_code"]
                ]

                if room_code is not None:
                    room_code = str(room_code).strip() or None

                rows.append({
                    "course_name": str(course_name).strip(),
                    "weekday": weekday,
                    "start_time": start_time,
                    "end_time": end_time,
                    "room_code": room_code,
                })

            except (ValueError, TypeError, IndexError) as exc:
                errors.append({
                    "row": row_number,
                    "message": str(exc),
                })

        workbook.close()

    except Exception as exc:
        return {
            "rows": [],
            "errors": [
                {
                    "row": 0,
                    "message": f"Không thể đọc file Excel: {exc}",
                }
            ],
        }

    return {
        "rows": rows,
        "errors": errors,
    }
