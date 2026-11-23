from __future__ import annotations

import os
from io import BytesIO

os.environ["AUTO_SEED"] = "false"

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from ops_router import seed_demo_dataset


@pytest.fixture()
def client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestingSessionLocal() as db:
        seed_demo_dataset(db, reset=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def auth_header(client: TestClient, username: str, password: str = "123") -> dict[str, str]:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_and_rbac_4_roles(client: TestClient):
    # Chưa đăng nhập -> 401
    r = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
    )
    assert r.status_code == 401

    # Sinh viên -> không được tạo phòng (403)
    sv_h = auth_header(client, "sv_minhanh")
    r_sv = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
        headers=sv_h,
    )
    assert r_sv.status_code == 403

    # Giảng viên -> không được chạy auto allocation (403)
    gv_h = auth_header(client, "gv_an")
    assert client.post("/api/allocation/run", json={"apply": False}, headers=gv_h).status_code == 403

    # Cán bộ Đào tạo -> được tạo phòng nhưng không được xem danh sách tài khoản Admin (403)
    off_h = auth_header(client, "officer01")
    r_off = client.post(
        "/api/rooms",
        json={"room_code": "X-101", "building": "Tòa X", "capacity": 40, "room_type": "classroom"},
        headers=off_h,
    )
    assert r_off.status_code == 201
    assert client.get("/api/auth/users", headers=off_h).status_code == 403

    # Admin -> toàn quyền ADM-01 (xem, tạo, khóa/mở khóa, cấp lại mật khẩu)
    adm_h = auth_header(client, "admin")
    users_res = client.get("/api/auth/users", headers=adm_h)
    assert users_res.status_code == 200
    assert len(users_res.json()) >= 4

    new_u = client.post(
        "/api/auth/users",
        json={"username": "gv_moi", "password": "456", "full_name": "TS. Trần Bình", "role": "LECTURER"},
        headers=adm_h,
    )
    assert new_u.status_code == 201
    uid = new_u.json()["id"]

    # Khóa tài khoản -> đăng nhập bị 403
    client.patch(f"/api/auth/users/{uid}/toggle-active", headers=adm_h)
    assert client.post("/api/auth/login", json={"username": "gv_moi", "password": "456"}).status_code == 403


def test_delete_room_with_schedule_returns_409_not_500(client: TestClient):
    off_h = auth_header(client, "officer01")
    rooms = client.get("/api/rooms").json()
    b1_204 = next(r for r in rooms if r["room_code"] == "B1-204")
    res = client.delete(f"/api/rooms/{b1_204['id']}", headers=off_h)
    assert res.status_code == 409


def test_end_to_end_import_allocate_export_and_stats(client: TestClient):
    off_h = auth_header(client, "officer01")

    # 1. Import thêm 2 lớp từ file Excel chuẩn
    wb = Workbook()
    ws = wb.active
    ws.append(["class_code", "course_name", "lecturer", "student_count", "weekday", "shift", "room_code", "required_room_type", "required_equipment"])
    ws.append(["NEW-101", "Kiến trúc máy tính", "TS. Lê Hải", 42, "Thứ 6", "Ca 3", "", "classroom", "Máy chiếu"])
    ws.append(["NEW-LAB", "Thực hành Kiến trúc MT", "TS. Lê Hải", 38, 6, 3, "", "lab", "Máy tính"])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    imp = client.post(
        "/api/timetable/import",
        files={"file": ("tkb_moi.xlsx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=off_h,
    )
    assert imp.status_code == 201, imp.text
    assert imp.json()["imported_count"] == 2

    # 2. Chạy Auto Allocation xem trước (apply=False) rồi áp dụng (apply=True)
    preview = client.post("/api/allocation/run", json={"apply": False}, headers=off_h)
    assert preview.status_code == 200
    assert preview.json()["applied"] is False
    assert preview.json()["summary"]["assigned"] >= 8

    apply_res = client.post("/api/allocation/run", json={"apply": True}, headers=off_h)
    assert apply_res.status_code == 200
    assert apply_res.json()["applied"] is True
    assert apply_res.json()["summary"]["unassigned"] == 0

    # 3. Xuất Excel & kiểm tra header Content-Disposition chuẩn
    exp = client.get("/api/timetable/export?fmt=xlsx", headers=off_h)
    assert exp.status_code == 200
    assert exp.headers["content-disposition"] == 'attachment; filename="CAMS_timetable_export.xlsx"'

    # 4. Thống kê Sprint 3 phản ánh 100% lớp đã gán phòng
    stats = client.get("/api/stats/overview", headers=off_h)
    assert stats.status_code == 200
    data = stats.json()
    assert data["assignment_rate"] == 100.0
    assert data["unassigned_sessions"] == 0


def test_collision_br01_capacity_br02_and_change_request_audit_br04(client: TestClient):
    off_h = auth_header(client, "officer01")
    gv_h = auth_header(client, "gv_an")

    sessions = client.get("/api/timetable/sessions").json()
    rooms = {r["room_code"]: r for r in client.get("/api/rooms").json()}

    # Tạo 1 buổi khác cùng Thứ 2 (weekday=1), 07:00-09:30 cố tình gán trùng vào B1-204 -> chặn cứng 409 (BR-01)
    classes = client.get("/api/classes").json()
    eng = next(c for c in classes if c["class_code"] == "ENG1001-03")
    collision = client.post(
        "/api/timetable/sessions",
        json={
            "class_id": eng["id"],
            "weekday": 1,
            "start_time": "07:00:00",
            "end_time": "09:30:00",
            "room_id": rooms["B1-204"]["id"],
        },
        headers=off_h,
    )
    assert collision.status_code == 409
    assert "B1-204" in collision.json()["detail"]

    # BR-02: Gán lớp MAT1101-05 (95 SV) vào A1-402 (70 chỗ) mặc định bị từ chối 409, nhưng allow_overload=true cho phép
    s_mat = next(s for s in sessions if s["room_id"] == rooms["B2-110"]["id"])
    overload_block = client.put(
        f"/api/timetable/sessions/{s_mat['id']}",
        json={**s_mat, "room_id": rooms["A1-402"]["id"]},
        headers=off_h,
    )
    assert overload_block.status_code == 409

    overload_ok = client.put(
        f"/api/timetable/sessions/{s_mat['id']}?allow_overload=true",
        json={**s_mat, "room_id": rooms["A1-402"]["id"]},
        headers=off_h,
    )
    assert overload_ok.status_code == 200

    # LEC-03 & OFF-07: Giảng viên gửi đơn xin đổi phòng -> Cán bộ Đào tạo duyệt -> Ghi Audit Log (BR-04)
    s_csdl = next(s for s in sessions if s["room_id"] == rooms["B1-204"]["id"])
    cr = client.post(
        "/api/change-requests",
        json={
            "session_id": s_csdl["id"],
            "requested_room_id": rooms["A2-305"]["id"],
            "reason": "Cần giảng đường lớn có micro cho buổi thuyết trình",
        },
        headers=gv_h,
    )
    assert cr.status_code == 201
    req_id = cr.json()["id"]

    rev = client.post(
        f"/api/change-requests/{req_id}/review",
        json={"action": "APPROVE"},
        headers=off_h,
    )
    assert rev.status_code == 200

    updated_s = client.get(f"/api/timetable/sessions/{s_csdl['id']}").json()
    assert updated_s["room_id"] == rooms["A2-305"]["id"]

    logs = client.get("/api/audit-logs", headers=off_h).json()
    assert any(lg["action"] == "APPROVE_CHANGE_REQUEST" for lg in logs)


def test_closure_dates_br03_and_student_lookup_stu01(client: TestClient):
    off_h = auth_header(client, "officer01")

    # Tra cứu lịch sinh viên công khai theo MSSV 21021234 (STU-01)
    stu = client.get("/api/lookup/timetable?student_code=21021234")
    assert stu.status_code == 200
    assert stu.json()["student"]["student_name"] == "Nguyễn Minh Anh"
    assert stu.json()["total"] >= 4

    # ADM-04: Final <= First bị từ chối 422
    bad_cfg = client.put(
        "/api/settings",
        json={"first_closure_date": "2026-12-20", "final_closure_date": "2026-12-10", "enforce_closure": True},
        headers=off_h,
    )
    assert bad_cfg.status_code == 422

    # BR-03: Đặt cả hai mốc về quá khứ -> Khóa Auto Allocation và khóa sửa phòng
    lock_cfg = client.put(
        "/api/settings",
        json={"first_closure_date": "2020-01-01", "final_closure_date": "2020-02-01", "enforce_closure": True},
        headers=off_h,
    )
    assert lock_cfg.status_code == 200

    assert client.post("/api/allocation/run", json={"apply": True}, headers=off_h).status_code == 403
