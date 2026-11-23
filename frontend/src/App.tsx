import { useEffect, useState } from "react";
import {
  apiFetch,
  checkBackendAlive,
  clearAuthSession,
  FALLBACK_ROOMS,
  FALLBACK_SESSIONS,
  FALLBACK_USERS,
  getStoredToken,
  getStoredUser,
  saveAuthSession,
  type AuthUser,
  type BookingItem,
  type ChangeRequestItem,
  type EnrichedSession,
  type IssueItem,
  type NotificationItem,
  type Role,
  type RoomItem,
} from "./api";
import { StaffWorkspace } from "./StaffWorkspace";
import { Btn, Card, Chip, Empty, Field, I, IMG, inp, Photo, roomImageByType, roomTypeLabel, U } from "./ui";

const DAYS = [
  { v: 1, l: "Thứ 2" },
  { v: 2, l: "Thứ 3" },
  { v: 3, l: "Thứ 4" },
  { v: 4, l: "Thứ 5" },
  { v: 5, l: "Thứ 6" },
  { v: 6, l: "Thứ 7" },
];

const inpL =
  "h-11 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-[#B08D57] focus:ring-2 focus:ring-[#B08D57]/25";

/* ==================== 1. CỔNG ĐĂNG NHẬP 4 VAI TRÒ & TRA CỨU NHANH MSSV (STU-01) ==================== */
function LoginScreen({
  online,
  onAuthenticated,
}: {
  online: boolean;
  onAuthenticated: (user: AuthUser) => void;
}) {
  const [selectedRole, setSelectedRole] = useState<Role>("STUDENT");
  const [username, setUsername] = useState("sv_minhanh");
  const [password, setPassword] = useState("123");
  const [loading, setLoading] = useState(false);
  const [errMsg, setErrMsg] = useState("");

  // Tra cứu nhanh TKB theo MSSV công khai (STU-01)
  const [mssvQuery, setMssvQuery] = useState("");
  const [lookupOpen, setLookupOpen] = useState(false);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupResult, setLookupResult] = useState<{
    student: { student_code: string; student_name: string; administrative_class?: string } | null;
    sessions: EnrichedSession[];
  } | null>(null);

  const demoMap: Record<Role, { label: string; user: string }> = {
    STUDENT: { label: "Sinh viên", user: "sv_minhanh" },
    LECTURER: { label: "Giảng viên", user: "gv_an" },
    OFFICER: { label: "Cán bộ Đào tạo", user: "officer01" },
    ADMIN: { label: "Quản trị viên", user: "admin" },
  };

  const selectRolePreset = (r: Role) => {
    setSelectedRole(r);
    setUsername(demoMap[r].user);
    setPassword("123");
    setErrMsg("");
  };

  const doLogin = async (uName: string, pw: string) => {
    setErrMsg("");
    setLoading(true);
    try {
      if (!online) {
        const fb = FALLBACK_USERS[uName] || FALLBACK_USERS[demoMap[selectedRole].user];
        saveAuthSession("figma-preview-token", fb);
        onAuthenticated(fb);
        return;
      }
      const res = await apiFetch<{ access_token: string; user: AuthUser }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ username: uName.trim(), password: pw }),
      });
      saveAuthSession(res.access_token, res.user);
      onAuthenticated(res.user);
    } catch (err) {
      setErrMsg(err instanceof Error ? err.message : "Đăng nhập thất bại");
    } finally {
      setLoading(false);
    }
  };

  const runPublicMssvLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mssvQuery.trim()) return;
    setLookupOpen(true);
    if (!online) {
      setLookupResult({
        student: { student_code: mssvQuery.trim(), student_name: "Nguyễn Minh Anh", administrative_class: "K66-CNTT2" },
        sessions: FALLBACK_SESSIONS,
      });
      return;
    }
    setLookupLoading(true);
    try {
      const data = await apiFetch<{
        student: { student_code: string; student_name: string; administrative_class?: string } | null;
        sessions: EnrichedSession[];
      }>(`/api/lookup/timetable?student_code=${encodeURIComponent(mssvQuery.trim())}`);
      setLookupResult(data);
    } catch {
      setLookupResult({ student: null, sessions: [] });
    } finally {
      setLookupLoading(false);
    }
  };

  return (
    <div className="relative grid min-h-screen overflow-hidden lg:grid-cols-[minmax(400px,28%)_minmax(0,1fr)]">
      <Photo src={U("photo-1562774053-701939374585")} c="absolute inset-0 size-full object-cover" />
      <div className="absolute inset-0 bg-gradient-to-t from-[#0B1220]/90 via-[#0B1220]/60 to-[#0B1220]/35" />

      <div className="relative z-10 flex min-w-0 items-center justify-center p-4 sm:p-6 lg:bg-[#FAF7F2] lg:p-7 lg:shadow-2xl">
        <div className="w-full max-w-[420px] rounded-3xl bg-[#FAF7F2] p-6 shadow-[0_10px_40px_rgba(30,58,138,.15)] lg:max-w-none lg:rounded-none lg:p-0 lg:shadow-none">
          <div className="mx-auto grid size-14 place-items-center rounded-full bg-[#0F172A] text-white">
            <I n="grad" s={26} />
          </div>
          <h1 className="mt-3 text-center font-serif text-[28px] font-semibold leading-tight">Phòng học ĐHQG · CAMS</h1>
          <div className="mx-auto mt-2.5 h-px w-12 bg-[#B08D57]" />
          <p className="mt-2 text-center text-xs text-mute">
            Hệ thống Quản lý Xếp phòng Tự động & Phân quyền RBAC 04 Vai trò
          </p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              doLogin(username, password);
            }}
            className="mt-4 space-y-3"
          >
            <div>
              <p className="text-xs font-semibold text-ink">Chọn vai trò (1-chạm điền tài khoản mẫu):</p>
              <div className="mt-1.5 grid grid-cols-2 gap-1.5">
                {(Object.keys(demoMap) as Role[]).map((r) => (
                  <button
                    type="button"
                    key={r}
                    onClick={() => selectRolePreset(r)}
                    className={`min-h-10 rounded-lg border-2 px-2 text-xs font-semibold transition ${
                      selectedRole === r
                        ? "border-[#1D4ED8] bg-[#1D4ED8] text-white"
                        : "border-slate-200 bg-[#F1F5F9] text-[#475569] hover:bg-slate-200"
                    }`}
                  >
                    {demoMap[r].label}
                  </button>
                ))}
              </div>
            </div>

            <Field label="Tài khoản / Email / MSSV">
              <input
                type="text"
                className={inpL}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="sv_minhanh / officer01 / gv_an / admin"
                required
              />
            </Field>
            <Field label="Mật khẩu">
              <input
                type="password"
                className={inpL}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </Field>

            {errMsg && <p className="rounded-lg bg-red-50 p-2.5 text-xs font-semibold text-red-600">{errMsg}</p>}

            <Btn type="submit" className="w-full" loading={loading}>
              <I n="out" s={18} />
              Đăng nhập hệ thống
            </Btn>
          </form>

          {/* Ô Tra cứu công khai theo MSSV (STU-01) */}
          <div className="mt-5 border-t border-slate-200 pt-4">
            <p className="text-xs font-semibold text-navy">🔍 Tra cứu nhanh Thời khóa biểu theo MSSV (STU-01):</p>
            <form onSubmit={runPublicMssvLookup} className="mt-1.5 flex gap-2">
              <input
                className={`${inpL} !h-10 flex-1`}
                value={mssvQuery}
                onChange={(e) => setMssvQuery(e.target.value)}
                placeholder="Nhập MSSV: 21021234 hoặc SV001"
              />
              <Btn type="submit" v="s" className="!h-10 !px-3 !text-xs">
                Tra cứu
              </Btn>
            </form>
          </div>
        </div>
      </div>

      <div className="relative z-10 hidden flex-col justify-end p-12 lg:flex">
        <div className="mb-3 flex gap-2">
          <Chip t={online ? "g" : "y"}>{online ? "Backend Online" : "Figma Preview Mode"}</Chip>
          <Chip t="b">Greedy Best-fit Engine</Chip>
        </div>
        <p className="max-w-lg font-serif text-3xl font-medium leading-snug text-white">
          Tìm phòng, xếp thời khóa biểu tự động và theo dõi lịch học ở một nơi.
        </p>
      </div>

      {/* Popup Kết quả Tra cứu nhanh MSSV */}
      {lookupOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/60 p-4" onClick={() => setLookupOpen(false)}>
          <Card className="max-h-[85vh] w-full max-w-2xl overflow-y-auto space-y-4">
            <div onClick={(e) => e.stopPropagation()} className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-navy">Kết quả tra cứu lịch học cá nhân</h2>
                  {lookupResult?.student && (
                    <p className="text-sm text-mute">
                      Sinh viên: <b>{lookupResult.student.student_name}</b> · MSSV: <b>{lookupResult.student.student_code}</b>{" "}
                      {lookupResult.student.administrative_class ? `(${lookupResult.student.administrative_class})` : ""}
                    </p>
                  )}
                </div>
                <button onClick={() => setLookupOpen(false)} className="rounded-lg p-1.5 hover:bg-soft">
                  <I n="x" />
                </button>
              </div>

              {lookupLoading ? (
                <p className="py-6 text-center text-sm text-mute">Đang tra cứu dữ liệu...</p>
              ) : !lookupResult || lookupResult.sessions.length === 0 ? (
                <Empty t="Không tìm thấy lịch học cho MSSV này" d="Thử nhập MSSV mẫu: 21021234 hoặc SV001" />
              ) : (
                <div className="space-y-2.5">
                  {lookupResult.sessions.map((s) => (
                    <div key={s.id} className="rounded-xl border-l-4 border-brand bg-blue-50/60 p-3 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <b>
                          {s.course_name} ({s.class_code})
                        </b>
                        <Chip t={s.room_code ? "g" : "y"}>
                          {s.room_code ? `Phòng ${s.room_code} · ${s.building}` : "Đang chờ xếp phòng"}
                        </Chip>
                      </div>
                      <p className="mt-1 text-xs text-mute">
                        {s.weekday_label} · {s.shift_label} ({s.time_range}) · GV: {s.lecturer}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ==================== 2. TRANG CHỦ SINH VIÊN & GIẢNG VIÊN ==================== */
function HomeView({
  user,
  sessions,
  notifications,
  go,
}: {
  user: AuthUser;
  sessions: EnrichedSession[];
  notifications: NotificationItem[];
  go: (p: string) => void;
}) {
  const roomChangeAlerts = notifications.filter((n) => n.category.includes("Đổi phòng") || n.category.includes("Xếp phòng"));

  return (
    <div className="space-y-6">
      {/* Banner thông báo biến động phòng học nổi bật ngay đầu trang (STU-03) */}
      {roomChangeAlerts.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950 shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-amber text-ink">
              <I n="bell" s={16} />
            </span>
            <div>
              <b className="block text-xs uppercase tracking-wide text-amber-800">Thông báo biến động phòng học (STU-03)</b>
              <span>{roomChangeAlerts[0].message}</span>
            </div>
          </div>
          <Btn v="g" className="!h-8 !px-3 !text-xs" onClick={() => go("notif")}>
            Xem chi tiết
          </Btn>
        </div>
      )}

      <div className="relative overflow-hidden rounded-2xl">
        <Photo src={IMG.campus} c="absolute inset-0 size-full" />
        <div className="absolute inset-0 bg-gradient-to-r from-navy via-navy/85 to-brand/60" />
        <div className="relative p-6 text-white md:p-9">
          <p className="text-xs font-medium text-blue-100">
            Học kỳ 1 · Năm học 2026–2027 · {user.role === "LECTURER" ? "Phân hệ Giảng viên" : `MSSV ${user.student_code || "21021234"}`}
          </p>
          <h1 className="mt-1 text-2xl font-bold sm:text-[30px]">Xin chào, {user.full_name}</h1>
          <p className="mt-1 text-sm text-blue-100">
            Bạn hiện có <b>{sessions.length}</b> buổi {user.role === "LECTURER" ? "giảng dạy" : "học tập"} trong tuần (
            {sessions.filter((s) => s.room_code).length} buổi đã có phòng học).
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Btn className="!bg-amber !text-ink hover:!bg-amber/90" onClick={() => go("search")}>
              <I n="search" s={18} />
              Tìm phòng trống
            </Btn>
            <Btn v="g" className="!text-white hover:!bg-white/10" onClick={() => go("schedule")}>
              Xem thời khóa biểu tuần
            </Btn>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          ["search", "Phòng trống", "search"],
          ["swap", user.role === "LECTURER" ? "Xin đổi phòng" : "Mượn phòng nhóm", "book"],
          ["warn", "Báo sự cố", "issue"],
          ["hist", "Theo dõi đơn", "history"],
        ].map(([icon, label, page]) => (
          <button
            key={page}
            onClick={() => go(page)}
            className="flex items-center gap-3 rounded-2xl bg-white p-4 text-left text-sm font-semibold shadow-[0_4px_20px_rgba(30,58,138,.07)] transition hover:-translate-y-0.5 hover:shadow-md"
          >
            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-blue-50 text-navy">
              <I n={icon} />
            </span>
            {label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold">
              {user.role === "LECTURER" ? "Lịch giảng dạy cá nhân (LEC-01)" : "Lịch học cá nhân của bạn (STU-01)"}
            </h2>
            <Btn v="g" className="!h-8 !text-xs" onClick={() => go("schedule")}>
              Xem cả tuần
            </Btn>
          </div>
          {sessions.length === 0 ? (
            <Empty t="Chưa có lịch trong học kỳ này" d="Dữ liệu thời khóa biểu sẽ tự động hiển thị sau khi Phòng Đào tạo phân bổ." />
          ) : (
            <div className="space-y-3">
              {sessions.slice(0, 5).map((s) => (
                <div key={s.id} className="flex flex-col gap-1 rounded-xl border-l-4 border-brand bg-blue-50/50 p-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <b className="text-navy">
                      {s.course_name} <span className="text-xs font-normal text-mute">({s.class_code})</span>
                    </b>
                    <p className="text-xs text-mute">
                      {s.weekday_label} · {s.shift_label} ({s.time_range}) · GV: {s.lecturer}
                    </p>
                  </div>
                  <div className="mt-1 sm:mt-0">
                    {s.room_code ? (
                      <Chip t="g">
                        <I n="pin" s={13} />
                        {s.room_code} · {s.building}
                      </Chip>
                    ) : (
                      <Chip t="y">Chờ xếp phòng</Chip>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Thông báo mới</h2>
            <Btn v="g" className="!h-8 !px-2 !text-xs" onClick={() => go("notif")}>
              Tất cả
            </Btn>
          </div>
          {notifications.slice(0, 4).map((n) => (
            <div key={n.id} className={`rounded-xl p-3 text-xs ${n.is_unread ? "bg-blue-50" : "bg-soft/60"}`}>
              <Chip t={n.tone}>{n.category}</Chip>
              <p className="mt-1.5 text-ink">{n.message}</p>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

/* ==================== 3. THỜI KHÓA BIỂU RESPONSIVE 375PX (STU-01, LEC-01) ==================== */
function ScheduleView({
  online,
  user,
  initialSessions,
}: {
  online: boolean;
  user: AuthUser;
  initialSessions: EnrichedSession[];
}) {
  const [mode, setMode] = useState<"week" | "list">("week");
  const [searchCode, setSearchCode] = useState(user.student_code || "");
  const [displayed, setDisplayed] = useState<EnrichedSession[]>(initialSessions);
  const [studentMeta, setStudentMeta] = useState<string>(
    user.role === "STUDENT" ? `${user.full_name} (MSSV: ${user.student_code || "21021234"})` : user.full_name,
  );

  useEffect(() => {
    setDisplayed(initialSessions);
  }, [initialSessions]);

  const handleLookup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!online || !searchCode.trim()) {
      setDisplayed(initialSessions);
      return;
    }
    try {
      const data = await apiFetch<{
        student: { student_code: string; student_name: string; administrative_class?: string } | null;
        sessions: EnrichedSession[];
      }>(`/api/lookup/timetable?q=${encodeURIComponent(searchCode.trim())}`);
      setDisplayed(data.sessions);
      if (data.student) {
        setStudentMeta(`${data.student.student_name} · MSSV ${data.student.student_code} (${data.student.administrative_class || ""})`);
      } else {
        setStudentMeta(`Kết quả lọc theo từ khóa "${searchCode.trim()}"`);
      }
    } catch {
      // Ignore
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold sm:text-[28px]">Thời khóa biểu</h1>
          <p className="text-xs text-mute">{studentMeta}</p>
        </div>
        <div className="flex rounded-xl bg-white p-1 shadow-sm">
          <button
            onClick={() => setMode("week")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${mode === "week" ? "bg-navy text-white" : "text-mute"}`}
          >
            Theo Thứ
          </button>
          <button
            onClick={() => setMode("list")}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${mode === "list" ? "bg-navy text-white" : "text-mute"}`}
          >
            Danh sách
          </button>
        </div>
      </div>

      {/* Thanh tra cứu theo MSSV / Mã lớp / Tên môn / Giảng viên */}
      <Card className="!p-4">
        <form onSubmit={handleLookup} className="flex flex-col gap-2 sm:flex-row">
          <input
            className={`${inp} flex-1`}
            value={searchCode}
            onChange={(e) => setSearchCode(e.target.value)}
            placeholder="Nhập MSSV (VD: 21021234, SV001), mã lớp hoặc tên giảng viên để tra cứu..."
          />
          <div className="flex gap-2">
            <Btn type="submit" className="flex-1 sm:flex-none">
              <I n="search" s={16} />
              Tra cứu TKB
            </Btn>
            <Btn
              v="s"
              onClick={() => {
                setSearchCode(user.student_code || "");
                setDisplayed(initialSessions);
              }}
            >
              Lịch của tôi
            </Btn>
          </div>
        </form>
      </Card>

      {displayed.length === 0 ? (
        <Card>
          <Empty t="Không tìm thấy buổi học phù hợp" d="Kiểm tra lại MSSV hoặc từ khóa tìm kiếm." />
        </Card>
      ) : mode === "week" ? (
        /* Thiết kế grid 1 cột trên di động 375px (không cuộn ngang, chuẩn DoD 7.1) và 6 cột trên màn hình lớn */
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {DAYS.map((d) => {
            const dayItems = displayed.filter((s) => s.weekday === d.v);
            return (
              <Card key={d.v} className="!p-3.5 space-y-2.5">
                <div className="rounded-lg bg-soft py-1.5 text-center text-sm font-bold text-navy">{d.l}</div>
                {dayItems.length === 0 ? (
                  <p className="py-4 text-center text-xs text-mute">Không có lịch</p>
                ) : (
                  dayItems.map((s) => (
                    <div key={s.id} className="rounded-xl border-l-4 border-brand bg-blue-50/70 p-2.5 text-xs space-y-1">
                      <b className="block text-navy">{s.course_name}</b>
                      <span className="block font-medium text-ink">
                        {s.shift_label} ({s.time_range})
                      </span>
                      <span className="block text-mute">
                        Mã: {s.class_code} · {s.lecturer}
                      </span>
                      <span className="inline-block rounded bg-white px-2 py-0.5 font-bold text-green-800">
                        {s.room_code ? `${s.room_code} (${s.building})` : "Chờ xếp phòng"}
                      </span>
                    </div>
                  ))
                )}
              </Card>
            );
          })}
        </div>
      ) : (
        <Card className="space-y-3 !p-4">
          {displayed.map((s) => (
            <div key={s.id} className="flex flex-col justify-between gap-2 rounded-xl border border-slate-100 p-3.5 sm:flex-row sm:items-center">
              <div>
                <b className="text-navy">
                  {s.course_name} · {s.class_code}
                </b>
                <p className="text-xs text-mute">
                  {s.weekday_label} · {s.shift_label} ({s.time_range}) · Giảng viên: {s.lecturer}
                </p>
              </div>
              <Chip t={s.room_code ? "g" : "y"}>
                {s.room_code ? `Phòng ${s.room_code} · ${s.building}` : "Chờ xếp phòng"}
              </Chip>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}

/* ==================== 4. TRA CỨU PHÒNG HỌC ĐANG TRỐNG (STU-02, LEC-02) ==================== */
function SearchRoomsView({
  online,
  userRole,
  onPickRoom,
}: {
  online: boolean;
  userRole: Role;
  onPickRoom: (r: RoomItem, mode: "detail" | "book") => void;
}) {
  const [weekday, setWeekday] = useState(1);
  const [shift, setShift] = useState(1);
  const [building, setBuilding] = useState("Tất cả");
  const [minCap, setMinCap] = useState(10);
  const [roomType, setRoomType] = useState("Tất cả");
  const [onlyFree, setOnlyFree] = useState(false);
  const [q, setQ] = useState("");
  const [rooms, setRooms] = useState<RoomItem[]>(FALLBACK_ROOMS);

  useEffect(() => {
    if (!online) return;
    const params = new URLSearchParams({
      weekday: String(weekday),
      shift: String(shift),
      min_capacity: String(minCap || 1),
      only_free: String(onlyFree),
    });
    if (building !== "Tất cả") params.set("building", building);
    if (roomType !== "Tất cả") params.set("room_type", roomType);
    if (q.trim()) params.set("q", q.trim());

    apiFetch<{ rooms: RoomItem[] }>(`/api/lookup/available-rooms?${params.toString()}`)
      .then((d) => setRooms(d.rooms))
      .catch(() => {});
  }, [online, weekday, shift, building, minCap, roomType, onlyFree, q]);

  const filtered = online
    ? rooms
    : rooms.filter((r) => r.room_code.toLowerCase().includes(q.toLowerCase()) && r.capacity >= minCap);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold sm:text-[28px]">Tra cứu phòng học còn trống</h1>
        <p className="text-xs text-mute">
          {userRole === "STUDENT"
            ? "Tra cứu phòng học không có lớp trong từng ca để tự học, ôn bài hoặc họp nhóm (STU-02)"
            : "Tra cứu phòng trống theo Thứ & Ca để dạy bù hoặc gửi đơn xin đổi phòng (LEC-02)"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[270px_1fr]">
        <Card className="space-y-3.5 self-start !p-5">
          <h2 className="font-semibold">Bộ lọc thông minh</h2>
          <Field label="Thứ trong tuần">
            <select className={inp} value={weekday} onChange={(e) => setWeekday(Number(e.target.value))}>
              {DAYS.map((d) => (
                <option key={d.v} value={d.v}>
                  {d.l}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Ca học kiểm tra">
            <select className={inp} value={shift} onChange={(e) => setShift(Number(e.target.value))}>
              <option value={1}>Ca 1 (07:00 – 09:30)</option>
              <option value={2}>Ca 2 (09:45 – 12:00)</option>
              <option value={3}>Ca 3 (13:00 – 15:30)</option>
              <option value={4}>Ca 4 (15:45 – 18:00)</option>
              <option value={5}>Ca 5 (18:15 – 20:15)</option>
            </select>
          </Field>
          <Field label="Tòa nhà">
            <select className={inp} value={building} onChange={(e) => setBuilding(e.target.value)}>
              {["Tất cả", "Tòa A1", "Tòa A2", "Tòa B1", "Tòa B2", "Tòa C3", "Thư viện"].map((b) => (
                <option key={b} value={b}>
                  {b}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Loại phòng">
            <select className={inp} value={roomType} onChange={(e) => setRoomType(e.target.value)}>
              <option value="Tất cả">Tất cả</option>
              <option value="classroom">Lý thuyết tiêu chuẩn</option>
              <option value="lab">Phòng Lab máy tính</option>
              <option value="hall">Giảng đường</option>
              <option value="group">Phòng học nhóm</option>
            </select>
          </Field>
          <Field label="Sức chứa tối thiểu">
            <input type="number" className={inp} value={minCap} onChange={(e) => setMinCap(Number(e.target.value))} />
          </Field>
          <label className="flex items-center gap-2 pt-1 text-sm font-medium text-navy">
            <input type="checkbox" checked={onlyFree} onChange={(e) => setOnlyFree(e.target.checked)} className="size-4 accent-navy" />
            Chỉ hiện phòng đang trống
          </label>
        </Card>

        <div className="space-y-4">
          <input className={inp} placeholder="Tìm nhanh theo mã phòng hoặc tòa nhà (VD: A2-305, C3)…" value={q} onChange={(e) => setQ(e.target.value)} />
          {filtered.length === 0 ? (
            <Card>
              <Empty t="Không tìm thấy phòng phù hợp" d="Hãy thử chọn ca học khác hoặc giảm điều kiện lọc." />
            </Card>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map((r) => {
                const free = r.is_available !== false;
                return (
                  <Card key={r.id} className="overflow-hidden !p-0 transition hover:shadow-lg">
                    <div className="relative">
                      <Photo src={roomImageByType(r.room_type)} c="aspect-video w-full" />
                      <span className="absolute left-3 top-3">
                        <Chip t={free ? "g" : "r"}>{free ? "Đang trống" : `Bận (${r.occupying_class || "Có lớp"})`}</Chip>
                      </span>
                    </div>
                    <div className="space-y-2 p-4">
                      <div className="flex items-center justify-between">
                        <h3 className="font-bold text-navy">{r.room_code}</h3>
                        <span className="text-xs font-medium text-mute">{r.capacity} chỗ</span>
                      </div>
                      <p className="text-xs text-mute">
                        {r.building} {r.floor ? `· Tầng ${r.floor}` : ""} · {roomTypeLabel(r.room_type)}
                      </p>
                      <p className="truncate text-xs text-mute">{r.equipment || "Tiêu chuẩn"}</p>
                      <div className="flex gap-2 pt-2">
                        <Btn v="s" className="flex-1 !h-9 !text-xs" onClick={() => onPickRoom(r, "detail")}>
                          Chi tiết ca
                        </Btn>
                        <Btn
                          className="flex-1 !h-9 !text-xs"
                          disabled={!free}
                          onClick={() => onPickRoom(r, "book")}
                        >
                          {userRole === "LECTURER" ? "Xin đổi tới" : "Mượn phòng"}
                        </Btn>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function RoomDetailView({
  room,
  onBack,
  onBook,
}: {
  room: RoomItem;
  onBack: () => void;
  onBook: () => void;
}) {
  const busy = room.busy_shifts || [];
  return (
    <div className="space-y-5">
      <Btn v="g" onClick={onBack}>
        ← Quay lại danh sách phòng
      </Btn>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Photo src={roomImageByType(room.room_type)} c="aspect-video w-full rounded-2xl" />
        </div>
        <Card className="space-y-3 self-start">
          <Chip t={room.is_available !== false ? "g" : "r"}>
            {room.is_available !== false ? "Đang còn trống" : "Đang có lớp học"}
          </Chip>
          <h1 className="text-2xl font-bold text-navy">Phòng {room.room_code}</h1>
          <p className="text-sm text-mute">
            {room.building} {room.floor ? `· Tầng ${room.floor}` : ""} · Sức chứa <b>{room.capacity} chỗ</b>
          </p>
          <p className="text-sm text-mute">Phân loại: {roomTypeLabel(room.room_type)}</p>
          <div className="flex flex-wrap gap-1.5">
            {(room.equipment || "Máy chiếu, Điều hòa, Wi-Fi")
              .split(",")
              .filter(Boolean)
              .map((eq) => (
                <Chip key={eq} t="b">
                  {eq.trim()}
                </Chip>
              ))}
          </div>
          <Btn className="w-full" disabled={room.is_available === false} onClick={onBook}>
            Chọn phòng này
          </Btn>
        </Card>
      </div>
      <Card>
        <h2 className="mb-3 text-lg font-semibold">Trạng thái sử dụng theo 6 Ca tiêu chuẩn trong ngày</h2>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
          {[1, 2, 3, 4, 5, 6].map((c) => (
            <div
              key={c}
              className={`rounded-xl py-3 text-center text-xs font-semibold ${
                busy.includes(c) ? "bg-red-100 text-red-800" : "bg-green-100 text-green-800"
              }`}
            >
              Ca {c}
              <span className="block font-normal">{busy.includes(c) ? "Đã có lớp" : "Trống"}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ==================== 5. ĐƠN XIN ĐỔI PHÒNG (LEC-03) / ĐẶT PHÒNG NHÓM ==================== */
function ActionFormView({
  online,
  user,
  sessions,
  rooms,
  preselectedRoom,
  onDone,
  showToast,
}: {
  online: boolean;
  user: AuthUser;
  sessions: EnrichedSession[];
  rooms: RoomItem[];
  preselectedRoom: RoomItem | null;
  onDone: () => void;
  showToast: (m: string) => void;
}) {
  // Chế độ Giảng viên: Gửi đơn xin đổi phòng dạy trực tuyến (LEC-03)
  const [sessionId, setSessionId] = useState<string>(sessions[0] ? String(sessions[0].id) : "");
  const [targetRoomId, setTargetRoomId] = useState<string>(preselectedRoom ? String(preselectedRoom.id) : "");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  // Chế độ Sinh viên: Mượn phòng học nhóm / thảo luận
  const [useDate, setUseDate] = useState("2026-11-28");
  const [shiftLabel, setShiftLabel] = useState("Ca 3 · 13:00");
  const [count, setCount] = useState("8");

  const chosenSession = sessions.find((s) => String(s.id) === sessionId) || sessions[0];
  const suitableRooms = chosenSession
    ? rooms.filter((r) => r.capacity >= chosenSession.student_count && r.id !== chosenSession.room_id)
    : rooms;

  const submitLecturerChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    if (!sessionId || !targetRoomId || reason.trim().length < 5) {
      setErr("Vui lòng chọn buổi dạy, phòng đề nghị và nhập lý do tối thiểu 5 ký tự.");
      return;
    }
    if (!online) {
      showToast("[Preview] Đã gửi đơn xin đổi phòng");
      onDone();
      return;
    }
    setBusy(true);
    try {
      await apiFetch("/api/change-requests", {
        method: "POST",
        body: JSON.stringify({
          session_id: Number(sessionId),
          requested_room_id: Number(targetRoomId),
          reason: reason.trim(),
        }),
      });
      showToast("Đã gửi đơn xin đổi phòng thành công, chờ Phòng Đào tạo duyệt!");
      onDone();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Gửi đơn thất bại");
    } finally {
      setBusy(false);
    }
  };

  const submitStudentBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr("");
    const rId = Number(targetRoomId) || rooms[0]?.id;
    if (!rId || reason.trim().length < 10) {
      setErr("Vui lòng chọn phòng và nhập mục đích học nhóm tối thiểu 10 ký tự.");
      return;
    }
    if (!online) {
      showToast("[Preview] Đã gửi yêu cầu mượn phòng");
      onDone();
      return;
    }
    setBusy(true);
    try {
      await apiFetch("/api/bookings", {
        method: "POST",
        body: JSON.stringify({
          room_id: rId,
          use_date: useDate,
          shift_label: shiftLabel,
          attendee_count: Number(count) || 5,
          purpose: reason.trim(),
        }),
      });
      showToast("Đã gửi yêu cầu mượn phòng học nhóm, chờ xét duyệt!");
      onDone();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Không thể đặt phòng");
    } finally {
      setBusy(false);
    }
  };

  if (user.role === "LECTURER") {
    return (
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold sm:text-[28px]">Gửi đơn xin đổi phòng dạy trực tuyến (LEC-03)</h1>
          <p className="text-xs text-mute">Hệ thống tự động gợi ý các phòng đủ sức chứa cho lớp học phần của bạn</p>
        </div>
        <Card className="max-w-2xl space-y-4">
          <form onSubmit={submitLecturerChange} className="space-y-4">
            <Field label="Chọn lớp / buổi giảng dạy cần đổi phòng">
              <select className={inp} value={sessionId} onChange={(e) => setSessionId(e.target.value)}>
                {sessions.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.class_code} · {s.course_name} ({s.student_count} SV) — {s.weekday_label} {s.shift_label} [Hiện tại:{" "}
                    {s.room_code || "Chưa gán"}]
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Phòng mới mong muốn (Đã lọc phòng đủ sức chứa)">
              <select className={inp} value={targetRoomId} onChange={(e) => setTargetRoomId(e.target.value)}>
                <option value="">— Chọn phòng đề nghị —</option>
                {suitableRooms.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.room_code} ({r.building}) · {r.capacity} chỗ · {roomTypeLabel(r.room_type)}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Lý do xin đổi phòng (Thiết bị hỏng, sĩ số tăng, sự cố kỹ thuật...)">
              <textarea
                rows={4}
                className={`${inp} h-auto py-2`}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="VD: Máy chiếu phòng hiện tại bị mờ, xin chuyển sang phòng có máy chiếu rõ hơn..."
              />
            </Field>
            {err && <p className="text-xs font-semibold text-red-600">{err}</p>}
            <Btn type="submit" loading={busy}>
              Gửi đơn lên Phòng Đào tạo
            </Btn>
          </form>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold sm:text-[28px]">Mượn phòng tự học / Thảo luận nhóm</h1>
        <p className="text-xs text-mute">Gửi đề xuất mượn phòng học nhóm hoặc phòng đọc thư viện</p>
      </div>
      <Card className="max-w-2xl space-y-4">
        <form onSubmit={submitStudentBooking} className="space-y-4">
          <Field label="Chọn phòng học">
            <select
              className={inp}
              value={targetRoomId || (rooms[0]?.id ? String(rooms[0].id) : "")}
              onChange={(e) => setTargetRoomId(e.target.value)}
            >
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.room_code} ({r.building}) · Tối đa {r.capacity} chỗ
                </option>
              ))}
            </select>
          </Field>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Ngày sử dụng">
              <input type="date" className={inp} value={useDate} onChange={(e) => setUseDate(e.target.value)} />
            </Field>
            <Field label="Ca đăng ký">
              <select className={inp} value={shiftLabel} onChange={(e) => setShiftLabel(e.target.value)}>
                <option>Ca 1 · 07:00</option>
                <option>Ca 2 · 09:45</option>
                <option>Ca 3 · 13:00</option>
                <option>Ca 4 · 15:45</option>
              </select>
            </Field>
            <Field label="Số thành viên">
              <input type="number" className={inp} value={count} onChange={(e) => setCount(e.target.value)} />
            </Field>
          </div>
          <Field label="Mục đích học tập / họp nhóm (ít nhất 10 ký tự)">
            <textarea
              rows={3}
              className={`${inp} h-auto py-2`}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="VD: Thảo luận nhóm đồ án môn Cơ sở dữ liệu"
            />
          </Field>
          {err && <p className="text-xs font-semibold text-red-600">{err}</p>}
          <Btn type="submit" loading={busy}>
            Gửi yêu cầu mượn phòng
          </Btn>
        </form>
      </Card>
    </div>
  );
}

/* ==================== 6. LỊCH SỬ ĐƠN (LEC-04), THÔNG BÁO (STU-03) & BÁO SỰ CỐ ==================== */
function HistoryView({
  online,
  user,
  showToast,
}: {
  online: boolean;
  user: AuthUser;
  showToast: (m: string) => void;
}) {
  const [changeReqs, setChangeReqs] = useState<ChangeRequestItem[]>([]);
  const [bookings, setBookings] = useState<BookingItem[]>([]);

  const load = async () => {
    if (!online) return;
    try {
      const [cr, bk] = await Promise.all([
        apiFetch<ChangeRequestItem[]>("/api/change-requests"),
        apiFetch<BookingItem[]>("/api/bookings"),
      ]);
      setChangeReqs(cr);
      setBookings(bk);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    load();
  }, [online]);

  const cancelBk = async (id: number) => {
    try {
      await apiFetch(`/api/bookings/${id}/cancel`, { method: "POST" });
      await load();
      showToast("Đã hủy yêu cầu đặt phòng");
    } catch {
      // Ignore
    }
  };

  const mapTone: Record<string, { t: string; l: string }> = {
    PENDING: { t: "y", l: "Chờ duyệt" },
    APPROVED: { t: "g", l: "Đã duyệt" },
    REJECTED: { t: "r", l: "Bị từ chối" },
    CANCELLED: { t: "x", l: "Đã hủy" },
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold sm:text-[28px]">Theo dõi tiến độ đơn yêu cầu (LEC-04)</h1>

      {user.role === "LECTURER" && (
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Đơn xin đổi phòng giảng dạy</h2>
          {changeReqs.length === 0 ? (
            <Empty t="Chưa có đơn xin đổi phòng" d="Các đơn của bạn sẽ cập nhật trạng thái trực tuyến tại đây." />
          ) : (
            changeReqs.map((r) => (
              <div key={r.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-3 last:border-0">
                <div>
                  <b className="text-navy">
                    {r.class_code} ({r.weekday_label} · {r.time_range})
                  </b>
                  <p className="text-xs text-mute">
                    Phòng {r.old_room_code} → <b>{r.requested_room_code}</b> · Lý do: {r.reason}
                  </p>
                  {r.reject_reason && (
                    <p className="mt-1 text-xs font-semibold text-red-600">Phản hồi từ Phòng Đào tạo: {r.reject_reason}</p>
                  )}
                </div>
                <Chip t={mapTone[r.status]?.t || "x"}>{mapTone[r.status]?.l || r.status}</Chip>
              </div>
            ))
          )}
        </Card>
      )}

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold">Lịch sử mượn phòng học nhóm</h2>
        {bookings.length === 0 ? (
          <Empty t="Chưa có lượt mượn phòng nào" d="Yêu cầu mượn phòng của bạn sẽ hiển thị tại đây." />
        ) : (
          bookings.map((b) => (
            <div key={b.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 py-3 last:border-0">
              <div>
                <b>{b.room_label}</b>
                <p className="text-xs text-mute">
                  {b.use_date} · {b.shift_label} ({b.attendee_count} người) — {b.purpose}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Chip t={mapTone[b.status]?.t || "x"}>{mapTone[b.status]?.l || b.status}</Chip>
                {b.status === "PENDING" && (
                  <Btn v="g" className="!h-8 !px-3 !text-xs !text-red-600" onClick={() => cancelBk(b.id)}>
                    Hủy
                  </Btn>
                )}
              </div>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}

function IssueView({
  online,
  rooms,
  showToast,
}: {
  online: boolean;
  rooms: RoomItem[];
  showToast: (m: string) => void;
}) {
  const [roomName, setRoomName] = useState(rooms[0] ? `${rooms[0].room_code} (${rooms[0].building})` : "A2-305");
  const [issueType, setIssueType] = useState("Thiết bị (máy chiếu, micro)");
  const [desc, setDesc] = useState("");
  const [issues, setIssues] = useState<IssueItem[]>([]);

  const load = () => {
    if (!online) return;
    apiFetch<IssueItem[]>("/api/issues")
      .then(setIssues)
      .catch(() => {});
  };

  useEffect(() => {
    load();
  }, [online]);

  const sendIssue = async () => {
    if (desc.trim().length < 10) return;
    if (!online) {
      showToast("[Preview] Đã ghi nhận báo cáo sự cố");
      setDesc("");
      return;
    }
    await apiFetch("/api/issues", {
      method: "POST",
      body: JSON.stringify({ room_name: roomName, issue_type: issueType, description: desc.trim() }),
    });
    setDesc("");
    load();
    showToast("Đã gửi báo cáo sự cố thành công");
  };

  const stMap: Record<string, [string, string]> = {
    RECEIVED: ["b", "Đã tiếp nhận"],
    IN_PROGRESS: ["y", "Đang xử lý"],
    RESOLVED: ["g", "Đã xử lý"],
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold sm:text-[28px]">Báo cáo sự cố phòng học</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <Field label="Phòng học">
            <select className={inp} value={roomName} onChange={(e) => setRoomName(e.target.value)}>
              {rooms.map((r) => (
                <option key={r.id} value={`${r.room_code} (${r.building})`}>
                  {r.room_code} · {r.building}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Loại sự cố">
            <select className={inp} value={issueType} onChange={(e) => setIssueType(e.target.value)}>
              <option>Thiết bị (máy chiếu, micro)</option>
              <option>Điều hòa / điện</option>
              <option>Máy tính phòng Lab</option>
              <option>Vệ sinh / Bàn ghế</option>
            </select>
          </Field>
          <Field label="Mô tả chi tiết" error={desc.length > 0 && desc.length < 10 ? "Nhập tối thiểu 10 ký tự" : ""}>
            <textarea rows={4} className={`${inp} h-auto py-2`} value={desc} onChange={(e) => setDesc(e.target.value)} />
          </Field>
          <Btn className="w-full" disabled={desc.trim().length < 10} onClick={sendIssue}>
            Gửi báo cáo kỹ thuật
          </Btn>
        </Card>

        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Các sự cố đã ghi nhận</h2>
          {issues.map((it) => (
            <div key={it.id} className="flex items-center justify-between gap-2 border-b border-slate-100 py-2.5 last:border-0 text-sm">
              <div>
                <b>{it.room_name}</b> · <span className="text-xs text-mute">{it.issue_type}</span>
                <p className="text-xs text-mute">{it.description}</p>
              </div>
              <Chip t={stMap[it.status]?.[0] || "b"}>{stMap[it.status]?.[1] || it.status}</Chip>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

/* ==================== MAIN APP ROOT ==================== */
export default function App() {
  const [online, setOnline] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser());
  const [page, setPage] = useState("home");
  const [rooms, setRooms] = useState<RoomItem[]>(FALLBACK_ROOMS);
  const [mySessions, setMySessions] = useState<EnrichedSession[]>(FALLBACK_SESSIONS);
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 1,
      category: "Đổi phòng",
      tone: "b",
      message: "Cơ sở dữ liệu (INT2211-02) học tại B1-204 Thứ 2 Ca 1.",
      is_unread: true,
      created_at: "Hôm nay",
    },
  ]);
  const [selectedRoom, setSelectedRoom] = useState<RoomItem | null>(null);
  const [toast, setToast] = useState("");

  const showToast = (m: string) => {
    setToast(m);
    window.setTimeout(() => setToast(""), 3000);
  };

  // Kiểm tra kết nối Backend & tính hợp lệ của phiên đăng nhập (RBAC Guard)
  useEffect(() => {
    checkBackendAlive().then(async (alive) => {
      setOnline(alive);
      if (alive && getStoredToken()) {
        try {
          const me = await apiFetch<AuthUser>("/api/auth/me");
          setUser(me);
        } catch {
          clearAuthSession();
          setUser(null);
        }
      }
    });
  }, []);

  // Chặn truy cập URL quản trị trái phép từ tài khoản Sinh viên/Giảng viên (Security DoD 7.3)
  useEffect(() => {
    const checkHashGuard = () => {
      const h = window.location.hash.toLowerCase();
      if ((h.includes("admin") || h.includes("staff")) && (!user || (user.role !== "ADMIN" && user.role !== "OFFICER"))) {
        window.location.hash = "";
        if (user) {
          showToast("Truy cập bị từ chối (403 RBAC): Khu vực quản trị chỉ dành cho Admin & Cán bộ Đào tạo!");
        }
      }
    };
    checkHashGuard();
    window.addEventListener("hashchange", checkHashGuard);
    return () => window.removeEventListener("hashchange", checkHashGuard);
  }, [user]);

  // Nạp dữ liệu cá nhân hóa cho Sinh viên / Giảng viên
  useEffect(() => {
    if (!online || !user || user.role === "ADMIN" || user.role === "OFFICER") return;
    const ttUrl =
      user.role === "STUDENT" && user.student_code
        ? `/api/lookup/timetable?student_code=${encodeURIComponent(user.student_code)}`
        : `/api/lookup/timetable?lecturer=${encodeURIComponent(user.full_name)}`;

    Promise.all([
      apiFetch<RoomItem[]>("/api/rooms"),
      apiFetch<{ sessions: EnrichedSession[] }>(ttUrl),
      apiFetch<NotificationItem[]>("/api/notifications"),
    ])
      .then(([rm, tt, nf]) => {
        setRooms(rm);
        setMySessions(tt.sessions);
        if (nf.length > 0) setNotifications(nf);
      })
      .catch(() => {});
  }, [online, user]);

  const handleLogout = () => {
    clearAuthSession();
    setUser(null);
    setPage("home");
  };

  if (!user) {
    return <LoginScreen online={online} onAuthenticated={(u) => setUser(u)} />;
  }

  // Phân luồng RBAC nghiêm ngặt: ADMIN và OFFICER vào StaffWorkspace
  if (user.role === "ADMIN" || user.role === "OFFICER") {
    return <StaffWorkspace user={user} online={online} onLogout={handleLogout} />;
  }

  const navItems: Array<[string, string, string, string]> = [
    ["home", "Trang chủ", "Home", "home"],
    ["schedule", user.role === "LECTURER" ? "Lịch dạy" : "Lịch học", "Schedule", "cal"],
    ["search", "Tìm phòng", "Available Rooms", "search"],
    ["book", user.role === "LECTURER" ? "Xin đổi phòng" : "Mượn phòng", "Request", "swap"],
    ["history", "Theo dõi đơn", "Requests", "hist"],
    ["notif", "Thông báo", "Alerts", "bell"],
    ["issue", "Báo sự cố", "Issues", "warn"],
    ["profile", "Cá nhân", "Profile", "user"],
  ];

  const mobileTabs = ["home", "schedule", "search", "book", "profile"];
  const activeNav = page === "detail" ? "search" : page;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-slate-100 lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-white p-4 shadow-sm lg:flex">
        <div className="mb-5 flex items-center gap-3 px-2">
          <div className="grid size-10 place-items-center rounded-xl bg-navy text-white">
            <I n="grad" />
          </div>
          <div>
            <b className="block text-navy leading-tight">CAMS · UniRoom</b>
            <span className="text-[11px] text-mute">{user.role === "LECTURER" ? "Cổng Giảng viên" : "Cổng Sinh viên"}</span>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          {navItems.map(([k, l, en, icon]) => (
            <button
              key={k}
              onClick={() => setPage(k)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                activeNav === k ? "bg-navy text-white" : "text-mute hover:bg-soft"
              }`}
            >
              <I n={icon} s={18} />
              <span className="text-left leading-tight">
                {l}
                <span className={`block text-[11px] font-normal ${activeNav === k ? "text-blue-100" : "text-slate-500"}`}>
                  {en}
                </span>
              </span>
            </button>
          ))}
        </nav>
        <div className="mt-2 flex items-center gap-3 rounded-xl border-t border-slate-100 pt-3 px-2">
          <span className="grid size-9 place-items-center rounded-full bg-amber text-xs font-bold text-ink">
            {user.full_name.slice(0, 2).toUpperCase()}
          </span>
          <span className="flex-1 truncate text-xs">
            <b className="block truncate">{user.full_name}</b>
            <span className="text-mute">{user.student_code || user.role}</span>
          </span>
          <button aria-label="Đăng xuất" onClick={handleLogout} className="text-mute hover:text-red-600">
            <I n="out" s={18} />
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-20 flex items-center gap-3 bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
        <Chip t={user.role === "LECTURER" ? "b" : "g"}>
          {user.role === "LECTURER" ? "Giảng viên" : `SV · ${user.student_code || "21021234"}`}
        </Chip>
        <Chip t={online ? "g" : "y"}>{online ? "Live API" : "Figma Preview"}</Chip>
        <button
          aria-label="Thông báo"
          onClick={() => setPage("notif")}
          className="relative ml-auto grid size-10 place-items-center rounded-xl hover:bg-soft"
        >
          <I n="bell" />
          {notifications.some((n) => n.is_unread) && (
            <i className="absolute right-2 top-2 size-2 rounded-full bg-red-500" />
          )}
        </button>
        <button onClick={handleLogout} className="text-xs font-semibold text-red-600 lg:hidden">
          Đăng xuất
        </button>
      </header>

      <main className="mx-auto max-w-[1180px] p-4 pb-28 lg:p-8">
        {page === "home" && (
          <HomeView user={user} sessions={mySessions} notifications={notifications} go={setPage} />
        )}
        {page === "schedule" && (
          <ScheduleView online={online} user={user} initialSessions={mySessions} />
        )}
        {page === "search" && (
          <SearchRoomsView
            online={online}
            userRole={user.role}
            onPickRoom={(r, m) => {
              setSelectedRoom(r);
              setPage(m);
            }}
          />
        )}
        {page === "detail" && selectedRoom && (
          <RoomDetailView
            room={selectedRoom}
            onBack={() => setPage("search")}
            onBook={() => setPage("book")}
          />
        )}
        {page === "book" && (
          <ActionFormView
            online={online}
            user={user}
            sessions={mySessions}
            rooms={rooms}
            preselectedRoom={selectedRoom}
            onDone={() => setPage("history")}
            showToast={showToast}
          />
        )}
        {page === "history" && <HistoryView online={online} user={user} showToast={showToast} />}
        {page === "notif" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold sm:text-[28px]">Thông báo biến động phòng & Phê duyệt</h1>
              {online && (
                <Btn
                  v="s"
                  className="!h-9 !text-xs"
                  onClick={() => {
                    apiFetch("/api/notifications/read-all", { method: "POST" }).then(() =>
                      setNotifications((prev) => prev.map((x) => ({ ...x, is_unread: false }))),
                    );
                  }}
                >
                  Đánh dấu đã đọc hết
                </Btn>
              )}
            </div>
            <Card className="space-y-3">
              {notifications.map((n) => (
                <div key={n.id} className={`rounded-xl p-3.5 text-sm ${n.is_unread ? "bg-blue-50" : "bg-soft/40"}`}>
                  <div className="flex items-center justify-between">
                    <Chip t={n.tone}>{n.category}</Chip>
                    <span className="text-xs text-mute">{n.created_at}</span>
                  </div>
                  <p className="mt-1.5">{n.message}</p>
                </div>
              ))}
            </Card>
          </div>
        )}
        {page === "issue" && <IssueView online={online} rooms={rooms} showToast={showToast} />}
        {page === "profile" && (
          <div className="space-y-5">
            <h1 className="text-2xl font-bold sm:text-[28px]">Hồ sơ tài khoản</h1>
            <Card className="max-w-xl space-y-3">
              <div className="flex items-center gap-4">
                <div className="grid size-14 place-items-center rounded-full bg-navy text-lg font-bold text-white">
                  {user.full_name.slice(0, 2).toUpperCase()}
                </div>
                <div>
                  <b className="text-lg">{user.full_name}</b>
                  <p className="text-xs text-mute">
                    @{user.username} · Vai trò: <b>{user.role}</b>
                  </p>
                </div>
              </div>
              {user.student_code && (
                <div className="flex justify-between border-t border-slate-100 pt-3 text-sm">
                  <span className="text-mute">Mã số sinh viên (MSSV)</span>
                  <b>{user.student_code}</b>
                </div>
              )}
              <div className="flex justify-between border-t border-slate-100 pt-3 text-sm">
                <span className="text-mute">Đơn vị / Khoa</span>
                <b>{user.department || "ĐHQG"}</b>
              </div>
              <div className="pt-2">
                <Btn v="s" className="w-full !text-red-600" onClick={handleLogout}>
                  <I n="out" s={18} />
                  Đăng xuất tài khoản
                </Btn>
              </div>
            </Card>
          </div>
        )}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-slate-200 bg-white lg:hidden">
        {mobileTabs.map((k) => {
          const [, l, , icon] = navItems.find((n) => n[0] === k)!;
          return (
            <button
              key={k}
              onClick={() => setPage(k)}
              className={`flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${activeNav === k ? "text-navy" : "text-mute"}`}
            >
              <I n={icon} s={20} />
              {l}
            </button>
          );
        })}
      </nav>

      {toast && (
        <div
          role="status"
          className="fixed bottom-20 left-1/2 z-50 flex -translate-x-1/2 items-center gap-2 rounded-xl bg-ink px-4 py-3 text-sm text-white shadow-lg lg:bottom-8"
        >
          <I n="check" s={16} c="text-green-400" />
          {toast}
        </div>
      )}
    </div>
  );
}
