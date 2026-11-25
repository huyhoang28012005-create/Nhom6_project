import { useEffect, useState } from "react";
import {
  ApiError,
  apiFetch,
  downloadFromApi,
  FALLBACK_ROOMS,
  FALLBACK_SESSIONS,
  type AllocationRunResponse,
  type AuditLogItem,
  type AuthUser,
  type BookingItem,
  type ChangeRequestItem,
  type CourseClassItem,
  type EnrichedSession,
  type Role,
  type RoomItem,
  type StatsOverview,
  type SystemSettingsData,
} from "./api";
import { Btn, Card, Chip, Empty, Field, I, inp, roomTypeLabel, ToastBanner } from "./ui";

const WEEKDAYS = [
  { v: 1, l: "Thứ 2" },
  { v: 2, l: "Thứ 3" },
  { v: 3, l: "Thứ 4" },
  { v: 4, l: "Thứ 5" },
  { v: 5, l: "Thứ 6" },
  { v: 6, l: "Thứ 7" },
];

const SHIFTS = [
  { n: 1, name: "Ca 1", periods: "Tiết 1–3", start: "07:00:00", end: "09:30:00", short: "07:00–09:30" },
  { n: 2, name: "Ca 2", periods: "Tiết 4–6", start: "09:45:00", end: "12:00:00", short: "09:45–12:00" },
  { n: 3, name: "Ca 3", periods: "Tiết 7–9", start: "13:00:00", end: "15:30:00", short: "13:00–15:30" },
  { n: 4, name: "Ca 4", periods: "Tiết 10–12", start: "15:45:00", end: "18:00:00", short: "15:45–18:00" },
  { n: 5, name: "Ca 5", periods: "Tiết 13–15", start: "18:15:00", end: "20:15:00", short: "18:15–20:15" },
  { n: 6, name: "Ca 6", periods: "Ca phụ tối", start: "20:20:00", end: "21:50:00", short: "20:20–21:50" },
];

function timesOverlap(aStart: string, aEnd: string, bStart: string, bEnd: string): boolean {
  return aStart < bEnd && aEnd > bStart;
}

/* ==================== 1. DASHBOARD THỐNG KÊ (SPRINT 3) ==================== */
function DashboardTab({
  online,
  sessions,
  rooms,
  onRefreshAll,
  flash,
}: {
  online: boolean;
  sessions: EnrichedSession[];
  rooms: RoomItem[];
  onRefreshAll: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [stats, setStats] = useState<StatsOverview | null>(null);
  const [seeding, setSeeding] = useState(false);

  useEffect(() => {
    if (!online) return;
    apiFetch<StatsOverview>("/api/stats/overview")
      .then(setStats)
      .catch(() => {});
  }, [online, sessions.length, rooms.length]);

  const assignedCount = stats ? stats.assigned_sessions : sessions.filter((s) => s.room_id !== null).length;
  const totalSessions = stats ? stats.total_sessions : sessions.length;
  const unassignedCount = stats ? stats.unassigned_sessions : totalSessions - assignedCount;
  const rate = totalSessions ? Math.round((assignedCount / totalSessions) * 1000) / 10 : 0;
  const totalRooms = stats ? stats.total_rooms : rooms.length;
  const avgUtil = stats ? stats.average_utilization_pct : 18.5;
  const pendingReqs = stats ? stats.pending_change_requests + stats.pending_bookings : 2;

  const resetDemo = async () => {
    if (!online) {
      flash("a", "Đang ở chế độ Preview Offline trên Figma");
      return;
    }
    setSeeding(true);
    try {
      await apiFetch("/api/demo/seed?reset=true", { method: "POST" });
      await onRefreshAll();
      const fresh = await apiFetch<StatsOverview>("/api/stats/overview");
      setStats(fresh);
      flash("g", "Đã làm mới bộ dữ liệu mẫu Demo (11 phòng, 12 lớp, 14 buổi học)");
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Không thể làm mới dữ liệu");
    } finally {
      setSeeding(false);
    }
  };

  const weekdayBars =
    stats?.by_weekday ||
    WEEKDAYS.map((w) => ({
      weekday: w.v,
      label: w.l,
      total_sessions: sessions.filter((s) => s.weekday === w.v).length,
      assigned_sessions: sessions.filter((s) => s.weekday === w.v && s.room_id).length,
    }));
  const maxWd = Math.max(1, ...weekdayBars.map((x) => x.total_sessions));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold">Thống kê & Hiệu suất khai thác phòng</h1>
          <p className="text-sm text-mute">Tổng hợp mức sử dụng phòng học, tỷ lệ phân bổ tự động và ghế trống lãng phí</p>
        </div>
        <Btn v="s" loading={seeding} onClick={resetDemo}>
          <I n="hist" s={16} />
          Khởi tạo lại dữ liệu mẫu Demo
        </Btn>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="!p-5">
          <p className="text-xs font-semibold uppercase text-mute">Danh mục phòng học</p>
          <p className="mt-2 text-3xl font-bold text-navy">{totalRooms} phòng</p>
          <p className="mt-1 text-xs text-mute">Hiệu suất khai thác TB: <b>{avgUtil}%</b> / tuần</p>
        </Card>
        <Card className="!p-5">
          <p className="text-xs font-semibold uppercase text-mute">Tiến độ xếp phòng TKB</p>
          <p className="mt-2 text-3xl font-bold text-green-700">
            {assignedCount}/{totalSessions} <span className="text-lg">({rate}%)</span>
          </p>
          <p className="mt-1 text-xs text-mute">Còn {unassignedCount} buổi đang chờ xếp phòng</p>
        </Card>
        <Card className="!p-5">
          <p className="text-xs font-semibold uppercase text-mute">Độ lãng phí chỗ ngồi</p>
          <p className="mt-2 text-3xl font-bold text-brand">{stats?.total_wasted_seats ?? 32} ghế</p>
          <p className="mt-1 text-xs text-mute">Tối ưu theo giải thuật Greedy Best-fit</p>
        </Card>
        <Card className="!p-5">
          <p className="text-xs font-semibold uppercase text-mute">Yêu cầu chờ xử lý</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">{pendingReqs} đơn</p>
          <p className="mt-1 text-xs text-mute">Quá tải sức chứa: {stats?.overloaded_sessions ?? 0} buổi</p>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Mật độ buổi học theo Thứ trong tuần</h2>
          <div className="space-y-3">
            {weekdayBars.map((w) => (
              <div key={w.weekday} className="space-y-1">
                <div className="flex justify-between text-xs font-medium">
                  <span>{w.label}</span>
                  <span className="text-mute">
                    Đã xếp {w.assigned_sessions}/{w.total_sessions} buổi
                  </span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-soft">
                  <div
                    className="h-full rounded-full bg-navy transition-all"
                    style={{ width: `${Math.max(4, (w.total_sessions / maxWd) * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold">Khai thác theo Tòa nhà</h2>
          <div className="space-y-3">
            {(stats?.by_building || []).length === 0 ? (
              <p className="text-sm text-mute">Đang hiển thị dữ liệu mẫu cục bộ.</p>
            ) : (
              stats!.by_building.map((b) => (
                <div key={b.building} className="flex items-center justify-between rounded-xl border border-slate-100 p-3 text-sm">
                  <div>
                    <b>{b.building}</b>
                    <p className="text-xs text-mute">
                      {b.room_count} phòng · Tổng {b.total_capacity} chỗ
                    </p>
                  </div>
                  <div className="text-right">
                    <Chip t={b.utilization_pct > 15 ? "g" : "b"}>{b.sessions_count} ca/tuần</Chip>
                    <p className="mt-1 text-xs text-mute">Khai thác {b.utilization_pct}%</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {stats && stats.by_room.length > 0 && (
        <Card className="overflow-x-auto !p-0">
          <div className="p-6 pb-3">
            <h2 className="text-lg font-semibold">Chi tiết mức sử dụng từng Phòng học</h2>
          </div>
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="border-y border-slate-100 bg-soft/60 text-xs uppercase text-mute">
              <tr>
                <th className="px-4 py-2.5">Mã phòng</th>
                <th className="px-4 py-2.5">Tòa nhà</th>
                <th className="px-4 py-2.5">Loại phòng</th>
                <th className="px-4 py-2.5">Sức chứa</th>
                <th className="px-4 py-2.5">Số ca đã xếp</th>
                <th className="px-4 py-2.5">Độ lấp đầy ghế</th>
                <th className="px-4 py-2.5">Ghế dư</th>
              </tr>
            </thead>
            <tbody>
              {stats.by_room.map((r) => (
                <tr key={r.room_id} className="border-b border-slate-100 last:border-0">
                  <td className="px-4 py-3 font-semibold text-navy">{r.room_code}</td>
                  <td className="px-4 py-3">{r.building}</td>
                  <td className="px-4 py-3">{roomTypeLabel(r.room_type)}</td>
                  <td className="px-4 py-3">{r.capacity} chỗ</td>
                  <td className="px-4 py-3">
                    <Chip t={r.sessions_count > 0 ? "g" : "x"}>{r.sessions_count} ca</Chip>
                  </td>
                  <td className="px-4 py-3">{r.seat_fill_pct}%</td>
                  <td className="px-4 py-3 text-mute">{r.wasted_seats}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

/* ==================== 2. IMPORT EXCEL TKB (OFF-01, BR-03) ==================== */
function ImportTKBTab({
  online,
  settings,
  onImported,
  flash,
}: {
  online: boolean;
  settings: SystemSettingsData | null;
  onImported: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [previewClosed, setPreviewClosed] = useState(false);
  const [resultMsg, setResultMsg] = useState<{ count?: number; errors?: Array<{ row: number; message: string }> } | null>(null);

  const realClosed = settings?.is_past_first_closure ?? false;
  const closed = realClosed || previewClosed;

  const handleUpload = async () => {
    if (!file) {
      flash("a", "Vui lòng chọn file Excel (.xlsx) hoặc CSV (.csv) trước khi tải lên");
      return;
    }
    if (!online) {
      flash("g", `[Preview Figma] Đã mô phỏng đọc file ${file.name}`);
      return;
    }
    setBusy(true);
    setResultMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await apiFetch<{ message: string; imported_count: number }>("/api/timetable/import", {
        method: "POST",
        body: fd,
      });
      setResultMsg({ count: res.imported_count });
      setFile(null);
      await onImported();
      flash("g", `Đã nhập thành công ${res.imported_count} buổi học ở trạng thái Chờ xếp phòng!`);
    } catch (err) {
      if (err instanceof ApiError && err.errors) {
        setResultMsg({ errors: err.errors });
        flash("r", `${err.message} (${err.errors.length} dòng lỗi)`);
      } else {
        flash("r", err instanceof Error ? err.message : "Tải file thất bại");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold">Import thời khóa biểu thô (OFF-01)</h1>
          <p className="text-sm text-mute">Hỗ trợ file .xlsx và .csv theo mã lớp, môn học, giảng viên, sĩ số, thứ & ca học</p>
        </div>
        <div className="flex rounded-xl bg-white p-1 shadow-sm">
          {[
            ["Theo thời hạn thật", false],
            ["Xem thử khóa BR-03", true],
          ].map(([l, v]) => (
            <button
              key={String(l)}
              onClick={() => setPreviewClosed(v as boolean)}
              className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${previewClosed === v ? "bg-navy text-white" : "text-mute"}`}
            >
              {l as string}
            </button>
          ))}
        </div>
      </div>

      <div className={`flex items-center gap-3 rounded-xl p-4 text-sm ${closed ? "bg-red-50 text-red-800" : "bg-blue-50 text-navy"}`}>
        <I n={closed ? "lock" : "clock"} />
        <span>
          Hạn chót nạp thời khóa biểu (<b>First Closure Date - BR-03</b>):{" "}
          <b>{settings?.first_closure_date || "2026-12-15"}</b> —{" "}
          {closed ? "Đã khóa chức năng nạp TKB và xếp tự động" : `Đang mở (còn ${settings?.days_until_first_closure ?? 22} ngày)`}
        </span>
      </div>

      <Card className={`space-y-4 ${closed ? "opacity-65" : ""}`}>
        <label
          className={`grid cursor-pointer place-items-center rounded-2xl border-2 border-dashed px-4 py-10 text-center transition ${
            closed ? "pointer-events-none border-slate-300 bg-slate-100" : "border-brand/50 bg-blue-50/40 hover:bg-blue-50"
          }`}
        >
          <input
            type="file"
            accept=".xlsx,.csv"
            disabled={closed}
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <span className={`grid size-14 place-items-center rounded-full ${closed ? "bg-slate-300 text-slate-600" : "bg-navy text-white"}`}>
            <I n="down" s={26} c="rotate-180" />
          </span>
          <p className="mt-3 font-semibold">
            {file ? `Đã chọn tệp: ${file.name}` : "Nhấn để chọn hoặc kéo thả file Excel (.xlsx) / CSV (.csv)"}
          </p>
          <p className="mt-1 text-xs text-mute">
            Cột hỗ trợ: <code>class_code, course_name, lecturer, student_count, weekday, shift (hoặc start_time, end_time), room_code</code>
          </p>
        </label>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="button"
            onClick={() =>
              online
                ? downloadFromApi("/api/timetable/template", "CAMS_timetable_template.xlsx").catch((e) => flash("r", e.message))
                : flash("a", "Hãy chạy Backend để tải file Excel mẫu")
            }
            className="flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
          >
            <I n="down" s={16} />
            Tải file mẫu chuẩn CAMS_timetable_template.xlsx
          </button>

          <Btn disabled={closed || !file} loading={busy} onClick={handleUpload} className="!bg-brand hover:!bg-blue-600">
            <I n="down" s={18} c="rotate-180" />
            Tải lên & Kiểm tra dữ liệu
          </Btn>
        </div>
      </Card>

      {resultMsg && (
        <Card className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Kết quả kiểm tra & nạp dữ liệu</h2>
            {resultMsg.count !== undefined && <Chip t="g">Thành công {resultMsg.count} buổi học</Chip>}
            {resultMsg.errors && <Chip t="r">Phát hiện {resultMsg.errors.length} lỗi dữ liệu</Chip>}
          </div>
          {resultMsg.errors && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-red-50 text-xs uppercase text-red-800">
                  <tr>
                    <th className="px-3 py-2">Dòng trên Excel</th>
                    <th className="px-3 py-2">Chi tiết lỗi vi phạm</th>
                  </tr>
                </thead>
                <tbody>
                  {resultMsg.errors.map((er, idx) => (
                    <tr key={idx} className="border-t border-red-100">
                      <td className="px-3 py-2 font-semibold">Dòng {er.row}</td>
                      <td className="px-3 py-2 text-red-700">{er.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

/* ==================== 3. TỰ ĐỘNG XẾP PHÒNG & LƯỚI TKB (OFF-02..OFF-06, BR-01, BR-02) ==================== */
function AssignTab({
  online,
  sessions,
  rooms,
  settings,
  onReload,
  flash,
}: {
  online: boolean;
  sessions: EnrichedSession[];
  rooms: RoomItem[];
  settings: SystemSettingsData | null;
  onReload: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [allocating, setAllocating] = useState(false);
  const [allocReport, setAllocReport] = useState<AllocationRunResponse | null>(null);
  const [editing, setEditing] = useState<EnrichedSession | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState<string>("");
  const [onlyFreeFilter, setOnlyFreeFilter] = useState<boolean>(true);
  const [savingManual, setSavingManual] = useState(false);
  const [overloadConfirm, setOverloadConfirm] = useState<{ room: RoomItem; diff: number } | null>(null);

  const unassignedCount = sessions.filter((s) => !s.room_id).length;
  const firstClosed = settings?.is_past_first_closure ?? false;
  const finalClosed = settings?.is_past_final_closure ?? false;

  const runEngine = async (applyToDb: boolean) => {
    if (!online) {
      flash("g", `[Preview Figma] Thuật toán Best-fit đã xếp thử ${unassignedCount} buổi học`);
      return;
    }
    setAllocating(true);
    try {
      const res = await apiFetch<AllocationRunResponse>("/api/allocation/run", {
        method: "POST",
        body: JSON.stringify({ session_ids: null, apply: applyToDb }),
      });
      setAllocReport(res);
      if (applyToDb) {
        await onReload();
        flash(
          res.summary.unassigned > 0 ? "a" : "g",
          `Đã tự động gán phòng thành công cho ${res.summary.assigned}/${res.summary.total} buổi học!`,
        );
      } else {
        flash("g", `Xem trước Best-fit: Có thể xếp ${res.summary.assigned}/${res.summary.total} buổi chờ xếp phòng.`);
      }
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Lỗi chạy thuật toán xếp phòng");
    } finally {
      setAllocating(false);
    }
  };

  const openManualModal = (s: EnrichedSession) => {
    setEditing(s);
    setSelectedRoomId(s.room_id ? String(s.room_id) : "");
    setOverloadConfirm(null);
  };

  const submitManualChange = async (forceOverload = false) => {
    if (!editing) return;
    const newRoomId = selectedRoomId ? Number(selectedRoomId) : null;
    const targetRoom = rooms.find((r) => r.id === newRoomId) || null;

    // Kiểm tra cảnh báo quá tải sức chứa màu vàng (BR-02 / OFF-06) trước khi lưu
    if (targetRoom && editing.student_count > targetRoom.capacity && !forceOverload) {
      setOverloadConfirm({
        room: targetRoom,
        diff: editing.student_count - targetRoom.capacity,
      });
      return;
    }

    if (!online) {
      flash("g", "[Preview Figma] Đã mô phỏng cập nhật phòng học");
      setEditing(null);
      return;
    }

    setSavingManual(true);
    try {
      await apiFetch(`/api/timetable/sessions/${editing.id}?allow_overload=${forceOverload ? "true" : "false"}`, {
        method: "PUT",
        body: JSON.stringify({
          class_id: editing.class_id,
          weekday: editing.weekday,
          start_time: editing.start_time,
          end_time: editing.end_time,
          room_id: newRoomId,
        }),
      });
      await onReload();
      setEditing(null);
      setOverloadConfirm(null);
      flash(
        forceOverload ? "a" : "g",
        forceOverload
          ? `Đã lưu phòng ${targetRoom?.room_code} kèm cờ cảnh báo quá tải sức chứa (BR-02)`
          : `Đã cập nhật phòng ${targetRoom ? targetRoom.room_code : "Chờ xếp"} cho lớp ${editing.class_code}`,
      );
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Không thể đổi phòng (Xung đột BR-01)");
    } finally {
      setSavingManual(false);
    }
  };

  // Xác định danh sách phòng cho modal đổi phòng thủ công (OFF-04 Smart Filter)
  const candidateRooms = editing
    ? rooms.filter((r) => {
        if (!onlyFreeFilter) return true;
        const occupied = sessions.some(
          (other) =>
            other.id !== editing.id &&
            other.room_id === r.id &&
            other.weekday === editing.weekday &&
            timesOverlap(editing.start_time, editing.end_time, other.start_time, other.end_time),
        );
        return !occupied;
      })
    : [];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[28px] font-bold">Xếp phòng & Lưới Thời khóa biểu</h1>
          <p className="text-sm text-mute">
            Thuật toán <b>Greedy Best-fit</b> ưu tiên lớp khó xếp & thiết bị đặc thù ·{" "}
            <b>{unassignedCount}</b> buổi đang chờ xếp phòng
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Btn v="s" disabled={allocating || firstClosed} loading={allocating} onClick={() => runEngine(false)}>
            Xem trước Best-fit
          </Btn>
          <Btn
            disabled={allocating || firstClosed}
            loading={allocating}
            onClick={() => runEngine(true)}
            className="!bg-amber !text-ink hover:!bg-amber/90"
          >
            <I n="bolt" s={18} />
            Tự động xếp phòng ({unassignedCount} buổi)
          </Btn>
        </div>
      </div>

      {/* Báo cáo kết quả chạy Auto Allocation Engine (OFF-02) */}
      {allocReport && (
        <Card className="border-2 border-brand/30 bg-blue-50/40 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="text-lg font-bold text-navy">
              {allocReport.applied ? "✅ Đã áp dụng kết quả Tự động xếp phòng" : "🔍 Kết quả Xem trước (Chưa lưu DB)"}
            </h2>
            <div className="flex flex-wrap gap-2">
              <Chip t="g">Xếp thành công: {allocReport.summary.assigned}/{allocReport.summary.total}</Chip>
              <Chip t={allocReport.summary.unassigned > 0 ? "r" : "b"}>
                Thiếu phòng: {allocReport.summary.unassigned}
              </Chip>
              <Chip t="b">Ghế trống dư: {allocReport.summary.total_wasted_seats}</Chip>
            </div>
          </div>

          {allocReport.assigned.length > 0 && (
            <div className="flex flex-wrap gap-2 text-xs">
              {allocReport.assigned.map((p) => (
                <span key={p.session_id} className="rounded-lg bg-white px-2.5 py-1 font-medium shadow-xs">
                  <b>{p.class_code}</b> → <span className="font-bold text-green-700">{p.room_code}</span>{" "}
                  <span className="text-mute">(dư {p.wasted_seats} ghế)</span>
                </span>
              ))}
            </div>
          )}

          {allocReport.unassigned.length > 0 && (
            <div className="rounded-xl bg-red-50 p-3 text-xs text-red-800 space-y-1">
              <b>Danh sách lớp chưa xếp được phòng & nguyên nhân:</b>
              {allocReport.unassigned.map((u) => (
                <p key={u.session_id}>
                  • <b>{u.class_code}</b>: {u.reasons.map((r) => r.message).join("; ")}
                </p>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Thanh chuyển đổi chế độ xem + Chú giải trạng thái màu chuẩn OFF-03 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-xl bg-white p-1 shadow-sm">
          {[
            ["grid", "Ma trận Thứ × Ca (OFF-03)"],
            ["table", "Danh sách & Điều chỉnh nhanh"],
          ].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setViewMode(k as "grid" | "table")}
              className={`rounded-lg px-3.5 py-1.5 text-sm font-medium ${viewMode === k ? "bg-navy text-white" : "text-mute"}`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs font-medium text-mute">
          <span className="flex items-center gap-1.5">
            <i className="inline-block size-3 rounded bg-green-500" />
            Xếp chuẩn (Đủ chỗ)
          </span>
          <span className="flex items-center gap-1.5">
            <i className="inline-block size-3 rounded bg-amber-400" />
            Cảnh báo quá tải (BR-02)
          </span>
          <span className="flex items-center gap-1.5">
            <i className="inline-block size-3 rounded bg-slate-400" />
            Chờ xếp phòng
          </span>
        </div>
      </div>

      {viewMode === "grid" ? (
        <Card className="overflow-x-auto !p-4">
          <table className="w-full min-w-[880px] border-collapse text-left text-xs">
            <thead>
              <tr>
                <th className="w-28 rounded-tl-xl bg-soft p-2.5 font-semibold text-ink">Ca / Thứ</th>
                {WEEKDAYS.map((w) => (
                  <th key={w.v} className="bg-soft p-2.5 text-center font-semibold text-ink">
                    {w.l}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SHIFTS.slice(0, 5).map((sh) => (
                <tr key={sh.n} className="border-t border-slate-200 align-top">
                  <td className="bg-soft/40 p-2.5">
                    <b className="text-sm text-navy">{sh.name}</b>
                    <span className="block text-[11px] text-mute">{sh.periods}</span>
                    <span className="block text-[11px] text-mute">{sh.short}</span>
                  </td>
                  {WEEKDAYS.map((w) => {
                    const cellSessions = sessions.filter((s) => s.weekday === w.v && (s.shift || 1) === sh.n);
                    return (
                      <td key={w.v} className="min-w-[135px] border-l border-slate-100 p-2 space-y-2">
                        {cellSessions.length === 0 ? (
                          <div className="h-14 rounded-lg border border-dashed border-slate-200/80" />
                        ) : (
                          cellSessions.map((cs) => {
                            const style =
                              cs.status === "OVERLOADED"
                                ? "border-amber-500 bg-amber-50 text-amber-950"
                                : cs.status === "ASSIGNED"
                                  ? "border-green-600 bg-green-50 text-green-950"
                                  : "border-slate-400 bg-slate-100 text-slate-800";
                            return (
                              <button
                                key={cs.id}
                                type="button"
                                onClick={() => openManualModal(cs)}
                                className={`block w-full rounded-xl border-l-4 p-2 text-left transition hover:shadow-md ${style}`}
                              >
                                <div className="flex items-center justify-between gap-1">
                                  <b className="truncate">{cs.class_code}</b>
                                  <span className="shrink-0 rounded bg-white/80 px-1.5 py-0.5 text-[11px] font-bold">
                                    {cs.room_code || "Chờ xếp"}
                                  </span>
                                </div>
                                <p className="mt-0.5 truncate font-medium">{cs.course_name}</p>
                                <p className="mt-0.5 text-[11px] opacity-80">
                                  {cs.student_count} SV{cs.room_capacity ? `/${cs.room_capacity}` : ""} · {cs.lecturer}
                                </p>
                              </button>
                            );
                          })
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : (
        <Card className="overflow-x-auto !p-0">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead className="bg-soft text-xs uppercase text-mute">
              <tr>
                <th className="px-4 py-3">Mã lớp</th>
                <th className="px-4 py-3">Môn học</th>
                <th className="px-4 py-3">Giảng viên</th>
                <th className="px-4 py-3">Sĩ số / Yêu cầu</th>
                <th className="px-4 py-3">Thứ & Ca</th>
                <th className="px-4 py-3">Phòng hiện tại</th>
                <th className="px-4 py-3">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s) => (
                <tr key={s.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-semibold text-navy">{s.class_code}</td>
                  <td className="px-4 py-3">{s.course_name}</td>
                  <td className="px-4 py-3">{s.lecturer}</td>
                  <td className="px-4 py-3 text-xs">
                    <b>{s.student_count} SV</b> · {roomTypeLabel(s.required_room_type)}
                    {s.required_equipment && <span className="block text-mute">{s.required_equipment}</span>}
                  </td>
                  <td className="px-4 py-3">
                    {s.weekday_label} · {s.shift_label}
                    <span className="block text-xs text-mute">{s.time_range}</span>
                  </td>
                  <td className="px-4 py-3">
                    {s.room_code ? (
                      <Chip t={s.status === "OVERLOADED" ? "y" : "g"}>
                        {s.room_code} ({s.room_capacity} chỗ)
                      </Chip>
                    ) : (
                      <Chip t="x">Chờ xếp phòng</Chip>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Btn v="s" className="!h-9 !px-3 !text-xs" disabled={finalClosed} onClick={() => openManualModal(s)}>
                      Đổi phòng
                    </Btn>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Modal Điều chỉnh phòng thủ công với Smart Filter (OFF-04, OFF-05, OFF-06) */}
      {editing && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/50 p-4" onClick={() => setEditing(null)}>
          <Card className="w-full max-w-lg space-y-4" >
            <div onClick={(e) => e.stopPropagation()} className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold">Điều chỉnh xếp phòng thủ công</h2>
                  <p className="text-sm text-mute">
                    {editing.class_code} · {editing.course_name} ({editing.student_count} SV) — {editing.weekday_label} ({editing.time_range})
                  </p>
                </div>
                <button onClick={() => setEditing(null)} className="rounded-lg p-1.5 hover:bg-soft">
                  <I n="x" />
                </button>
              </div>

              <label className="flex items-center gap-2 rounded-xl bg-blue-50/70 p-3 text-xs font-medium text-navy">
                <input
                  type="checkbox"
                  checked={onlyFreeFilter}
                  onChange={(e) => setOnlyFreeFilter(e.target.checked)}
                  className="size-4 accent-navy"
                />
                Bộ lọc thông minh (OFF-04): Chỉ hiển thị phòng đang thực sự còn trống trong ca này (Bỏ chọn để test chặn xung đột BR-01)
              </label>

              <Field label="Chọn phòng học phân bổ">
                <select
                  className={inp}
                  value={selectedRoomId}
                  onChange={(e) => {
                    setSelectedRoomId(e.target.value);
                    setOverloadConfirm(null);
                  }}
                >
                  <option value="">— Bỏ gán phòng (Đưa về Chờ xếp phòng) —</option>
                  {candidateRooms.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.room_code} ({r.building}) · {r.capacity} chỗ · {roomTypeLabel(r.room_type)}
                      {r.capacity < editing.student_count ? " ⚠️ Quá tải sĩ số" : ""}
                    </option>
                  ))}
                </select>
              </Field>

              {overloadConfirm && (
                <div className="rounded-xl border border-amber-400 bg-amber-50 p-3.5 text-sm text-amber-950 space-y-2">
                  <p className="font-bold">
                    ⚠️ Cảnh báo quá tải sức chứa (BR-02 / OFF-06):
                  </p>
                  <p>
                    Sĩ số lớp (<b>{editing.student_count} SV</b>) vượt quá sức chứa phòng{" "}
                    <b>{overloadConfirm.room.room_code}</b> (<b>{overloadConfirm.room.capacity} chỗ</b>) — thiếu{" "}
                    <b>{overloadConfirm.diff} chỗ ngồi</b>. Bạn có chắc chắn vẫn muốn gán phòng này không?
                  </p>
                  <Btn
                    loading={savingManual}
                    onClick={() => submitManualChange(true)}
                    className="!bg-amber !text-ink hover:!bg-amber/90"
                  >
                    Xác nhận vẫn lưu kèm cờ cảnh báo vàng
                  </Btn>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Btn v="s" onClick={() => setEditing(null)}>
                  Hủy
                </Btn>
                <Btn loading={savingManual} disabled={finalClosed} onClick={() => submitManualChange(false)}>
                  Lưu thay đổi
                </Btn>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ==================== 4. XÉT DUYỆT ĐƠN ĐỔI PHÒNG & MƯỢN PHÒNG (OFF-07) ==================== */
function ApproveTab({
  online,
  onReload,
  flash,
}: {
  online: boolean;
  onReload: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [reqs, setReqs] = useState<ChangeRequestItem[]>([]);
  const [bookings, setBookings] = useState<BookingItem[]>([]);
  const [tab, setTab] = useState<"ALL" | "PENDING" | "APPROVED" | "REJECTED">("ALL");
  const [rejectModal, setRejectModal] = useState<ChangeRequestItem | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadData = async () => {
    if (!online) return;
    try {
      const [cr, bk] = await Promise.all([
        apiFetch<ChangeRequestItem[]>("/api/change-requests"),
        apiFetch<BookingItem[]>("/api/bookings"),
      ]);
      setReqs(cr);
      setBookings(bk);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    loadData();
  }, [online]);

  const handleReview = async (item: ChangeRequestItem, action: "APPROVE" | "REJECT", reason?: string) => {
    if (!online) return;
    setBusyId(item.id);
    try {
      await apiFetch(`/api/change-requests/${item.id}/review`, {
        method: "POST",
        body: JSON.stringify({ action, reject_reason: reason, allow_overload: true }),
      });
      await loadData();
      await onReload();
      setRejectModal(null);
      setRejectReason("");
      flash("g", action === "APPROVE" ? `Đã duyệt đổi sang phòng ${item.requested_room_code}` : "Đã từ chối đơn đổi phòng");
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Xử lý đơn thất bại");
    } finally {
      setBusyId(null);
    }
  };

  const handleBookingReview = async (b: BookingItem, action: "APPROVE" | "REJECT") => {
    if (!online) return;
    try {
      await apiFetch(`/api/bookings/${b.id}/review`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      await loadData();
      flash("g", action === "APPROVE" ? "Đã duyệt yêu cầu mượn phòng" : "Đã từ chối mượn phòng");
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Lỗi xử lý");
    }
  };

  const filtered = reqs.filter((r) => tab === "ALL" || r.status === tab);
  const statusChip: Record<string, { t: string; l: string }> = {
    PENDING: { t: "y", l: "Chờ duyệt" },
    APPROVED: { t: "g", l: "Đã duyệt" },
    REJECTED: { t: "r", l: "Từ chối" },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[28px] font-bold">Xét duyệt Đơn xin đổi phòng (OFF-07)</h1>
        <p className="text-sm text-mute">Khi bấm Duyệt, hệ thống tự động kiểm tra xung đột BR-01, đổi phòng TKB, ghi Audit Log và gửi thông báo</p>
      </div>

      <div className="flex flex-wrap gap-1 rounded-xl bg-white p-1 shadow-sm w-fit">
        {[
          ["ALL", "Tất cả"],
          ["PENDING", "Chờ duyệt"],
          ["APPROVED", "Đã duyệt"],
          ["REJECTED", "Từ chối"],
        ].map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k as typeof tab)}
            className={`rounded-lg px-3.5 py-1.5 text-sm font-medium ${tab === k ? "bg-navy text-white" : "text-mute"}`}
          >
            {l}
          </button>
        ))}
      </div>

      <Card className="overflow-x-auto !p-0">
        {filtered.length === 0 ? (
          <Empty t="Không có đơn xin đổi phòng nào" d="Các đơn do Giảng viên gửi sẽ hiển thị tại đây." />
        ) : (
          <table className="w-full min-w-[880px] text-left text-sm">
            <thead className="bg-soft text-xs uppercase text-mute">
              <tr>
                <th className="px-4 py-3">Giảng viên</th>
                <th className="px-4 py-3">Lớp & Buổi dạy</th>
                <th className="px-4 py-3">Phòng cũ → Đề nghị</th>
                <th className="px-4 py-3">Lý do</th>
                <th className="px-4 py-3">Trạng thái</th>
                <th className="px-4 py-3">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-semibold">{r.lecturer_name}</td>
                  <td className="px-4 py-3">
                    <b className="text-navy">{r.class_code}</b> ({r.student_count} SV)
                    <span className="block text-xs text-mute">
                      {r.weekday_label} · {r.time_range}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-mute">{r.old_room_code}</span> →{" "}
                    <b className="text-navy">{r.requested_room_code}</b> ({r.requested_room_capacity} chỗ)
                  </td>
                  <td className="max-w-[260px] px-4 py-3 text-xs text-mute">
                    {r.reason}
                    {r.reject_reason && <span className="mt-1 block font-semibold text-red-600">Lý do từ chối: {r.reject_reason}</span>}
                  </td>
                  <td className="px-4 py-3">
                    <Chip t={statusChip[r.status]?.t || "x"}>{statusChip[r.status]?.l || r.status}</Chip>
                  </td>
                  <td className="px-4 py-3">
                    {r.status === "PENDING" && (
                      <div className="flex gap-2">
                        <Btn
                          className="!h-8 !bg-green-600 !px-3 !text-xs hover:!bg-green-700"
                          loading={busyId === r.id}
                          onClick={() => handleReview(r, "APPROVE")}
                        >
                          Duyệt
                        </Btn>
                        <Btn
                          v="s"
                          className="!h-8 !border-red-300 !px-3 !text-xs !text-red-700"
                          disabled={busyId === r.id}
                          onClick={() => {
                            setRejectModal(r);
                            setRejectReason("");
                          }}
                        >
                          Từ chối
                        </Btn>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Yêu cầu mượn phòng học nhóm từ Sinh viên */}
      {bookings.filter((b) => b.status === "PENDING").length > 0 && (
        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Yêu cầu mượn phòng học nhóm / tự học đang chờ duyệt</h2>
          {bookings
            .filter((b) => b.status === "PENDING")
            .map((b) => (
              <div key={b.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 p-3 text-sm">
                <div>
                  <b>{b.room_label}</b> · {b.use_date} ({b.shift_label}) · {b.attendee_count} người
                  <p className="text-xs text-mute">
                    Người gửi: {b.requester_name} — Mục đích: {b.purpose}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Btn className="!h-8 !bg-green-600 !px-3 !text-xs" onClick={() => handleBookingReview(b, "APPROVE")}>
                    Duyệt mượn
                  </Btn>
                  <Btn v="s" className="!h-8 !px-3 !text-xs !text-red-600" onClick={() => handleBookingReview(b, "REJECT")}>
                    Từ chối
                  </Btn>
                </div>
              </div>
            ))}
        </Card>
      )}

      {/* Modal bắt buộc nhập lý do từ chối (OFF-07) */}
      {rejectModal && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/50 p-4">
          <Card className="w-full max-w-md space-y-4">
            <h2 className="text-lg font-bold">Từ chối đơn đổi phòng ({rejectModal.class_code})</h2>
            <Field label="Lý do từ chối (Bắt buộc nhập theo OFF-07)">
              <textarea
                rows={3}
                className={`${inp} h-auto py-2`}
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="VD: Phòng A2-305 đang bảo trì hệ thống âm thanh vào chiều Thứ 2..."
              />
            </Field>
            <div className="flex justify-end gap-2">
              <Btn v="s" onClick={() => setRejectModal(null)}>
                Hủy
              </Btn>
              <Btn
                className="!bg-red-600 hover:!bg-red-700"
                disabled={rejectReason.trim().length < 4}
                loading={busyId === rejectModal.id}
                onClick={() => handleReview(rejectModal, "REJECT", rejectReason)}
              >
                Xác nhận từ chối
              </Btn>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ==================== 5. QUẢN LÝ DANH MỤC PHÒNG & LỚP HỌC PHẦN (ADM-02) ==================== */
function CatalogTab({
  online,
  rooms,
  onReload,
  flash,
}: {
  online: boolean;
  rooms: RoomItem[];
  onReload: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [sub, setSub] = useState<"rooms" | "classes">("rooms");
  const [classes, setClasses] = useState<CourseClassItem[]>([]);

  const [rCode, setRCode] = useState("");
  const [rBld, setRBld] = useState("Tòa A1");
  const [rCap, setRCap] = useState("50");
  const [rType, setRType] = useState("classroom");
  const [rEq, setREq] = useState("Máy chiếu, Điều hòa, Wi-Fi");

  const [cCode, setCCode] = useState("");
  const [cName, setCName] = useState("");
  const [cLec, setCLec] = useState("");
  const [cCount, setCCount] = useState("45");
  const [cType, setCType] = useState("classroom");
  const [cEq, setCEq] = useState("Máy chiếu");
  const [cWd, setCWd] = useState("2");
  const [cShift, setCShift] = useState("1");

  const loadClasses = async () => {
    if (!online) return;
    try {
      const list = await apiFetch<CourseClassItem[]>("/api/classes");
      setClasses(list);
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    loadClasses();
  }, [online]);

  const addRoom = async () => {
    if (!rCode.trim()) {
      flash("a", "Vui lòng nhập mã phòng");
      return;
    }
    try {
      await apiFetch("/api/rooms", {
        method: "POST",
        body: JSON.stringify({
          room_code: rCode.trim(),
          building: rBld.trim(),
          capacity: Number(rCap) || 40,
          room_type: rType,
          equipment: rEq.trim() || null,
        }),
      });
      setRCode("");
      await onReload();
      flash("g", `Đã thêm phòng học ${rCode.trim()}`);
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Không thể tạo phòng");
    }
  };

  const removeRoom = async (id: number, code: string) => {
    try {
      await apiFetch(`/api/rooms/${id}`, { method: "DELETE" });
      await onReload();
      flash("g", `Đã xóa phòng ${code}`);
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Không thể xóa phòng");
    }
  };

  const addClassAndSession = async () => {
    if (!cCode.trim() || !cName.trim()) {
      flash("a", "Vui lòng nhập Mã lớp và Tên môn học");
      return;
    }
    try {
      const created = await apiFetch<CourseClassItem>("/api/classes", {
        method: "POST",
        body: JSON.stringify({
          class_code: cCode.trim(),
          course_name: cName.trim(),
          lecturer: cLec.trim() || null,
          student_count: Number(cCount) || 40,
          required_room_type: cType,
          required_equipment: cEq.trim() || null,
        }),
      });
      const sh = SHIFTS.find((x) => x.n === Number(cShift)) || SHIFTS[0];
      await apiFetch("/api/timetable/sessions", {
        method: "POST",
        body: JSON.stringify({
          class_id: created.id,
          weekday: Number(cWd),
          start_time: sh.start,
          end_time: sh.end,
          room_id: null,
        }),
      });
      setCCode("");
      setCName("");
      await loadClasses();
      await onReload();
      flash("g", `Đã tạo lớp ${created.class_code} và đưa vào danh sách Chờ xếp phòng!`);
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Không thể tạo lớp học phần");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-[28px] font-bold">Danh mục Phòng học & Lớp học phần (ADM-02)</h1>
        <div className="flex rounded-xl bg-white p-1 shadow-sm">
          <button
            onClick={() => setSub("rooms")}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium ${sub === "rooms" ? "bg-navy text-white" : "text-mute"}`}
          >
            Phòng học ({rooms.length})
          </button>
          <button
            onClick={() => setSub("classes")}
            className={`rounded-lg px-4 py-1.5 text-sm font-medium ${sub === "classes" ? "bg-navy text-white" : "text-mute"}`}
          >
            Lớp học phần ({classes.length})
          </button>
        </div>
      </div>

      {sub === "rooms" ? (
        <>
          <Card className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <Field label="Mã phòng">
              <input className={inp} value={rCode} onChange={(e) => setRCode(e.target.value)} placeholder="VD: B1-302" />
            </Field>
            <Field label="Tòa nhà">
              <input className={inp} value={rBld} onChange={(e) => setRBld(e.target.value)} />
            </Field>
            <Field label="Sức chứa">
              <input type="number" className={inp} value={rCap} onChange={(e) => setRCap(e.target.value)} />
            </Field>
            <Field label="Loại phòng">
              <select className={inp} value={rType} onChange={(e) => setRType(e.target.value)}>
                <option value="classroom">Lý thuyết tiêu chuẩn</option>
                <option value="lab">Phòng Lab máy tính</option>
                <option value="hall">Giảng đường bậc thang</option>
                <option value="group">Phòng học nhóm</option>
              </select>
            </Field>
            <Field label="Thiết bị">
              <input className={inp} value={rEq} onChange={(e) => setREq(e.target.value)} />
            </Field>
            <div className="flex items-end">
              <Btn className="w-full" onClick={addRoom}>
                <I n="plus" s={16} />
                Thêm phòng
              </Btn>
            </div>
          </Card>

          <Card className="overflow-x-auto !p-0">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-soft text-xs uppercase text-mute">
                <tr>
                  <th className="px-4 py-3">Mã phòng</th>
                  <th className="px-4 py-3">Tòa nhà</th>
                  <th className="px-4 py-3">Loại phòng</th>
                  <th className="px-4 py-3">Sức chứa</th>
                  <th className="px-4 py-3">Thiết bị</th>
                  <th className="px-4 py-3 text-right">Xóa</th>
                </tr>
              </thead>
              <tbody>
                {rooms.map((r) => (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-semibold text-navy">{r.room_code}</td>
                    <td className="px-4 py-3">{r.building}</td>
                    <td className="px-4 py-3">{roomTypeLabel(r.room_type)}</td>
                    <td className="px-4 py-3">{r.capacity} chỗ</td>
                    <td className="px-4 py-3 text-xs text-mute">{r.equipment || "—"}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => removeRoom(r.id, r.room_code)}
                        className="rounded-lg p-1.5 text-mute hover:bg-red-50 hover:text-red-600"
                        title="Xóa phòng"
                      >
                        <I n="trash" s={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      ) : (
        <>
          <Card className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Field label="Mã lớp học phần">
              <input className={inp} value={cCode} onChange={(e) => setCCode(e.target.value)} placeholder="VD: INT3405-01" />
            </Field>
            <Field label="Tên môn học">
              <input className={inp} value={cName} onChange={(e) => setCName(e.target.value)} placeholder="Học máy" />
            </Field>
            <Field label="Giảng viên">
              <input className={inp} value={cLec} onChange={(e) => setCLec(e.target.value)} placeholder="TS. Nguyễn Văn An" />
            </Field>
            <Field label="Sĩ số SV">
              <input type="number" className={inp} value={cCount} onChange={(e) => setCCount(e.target.value)} />
            </Field>
            <Field label="Loại phòng yêu cầu">
              <select className={inp} value={cType} onChange={(e) => setCType(e.target.value)}>
                <option value="classroom">Lý thuyết tiêu chuẩn</option>
                <option value="lab">Phòng Lab máy tính</option>
                <option value="hall">Giảng đường</option>
              </select>
            </Field>
            <Field label="Thiết bị yêu cầu">
              <input className={inp} value={cEq} onChange={(e) => setCEq(e.target.value)} />
            </Field>
            <Field label="Thứ & Ca học">
              <div className="grid grid-cols-2 gap-2">
                <select className={inp} value={cWd} onChange={(e) => setCWd(e.target.value)}>
                  {WEEKDAYS.map((w) => (
                    <option key={w.v} value={w.v}>
                      {w.l}
                    </option>
                  ))}
                </select>
                <select className={inp} value={cShift} onChange={(e) => setCShift(e.target.value)}>
                  {SHIFTS.slice(0, 5).map((s) => (
                    <option key={s.n} value={s.n}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
            </Field>
            <div className="flex items-end">
              <Btn className="w-full" onClick={addClassAndSession}>
                <I n="plus" s={16} />
                Thêm lớp & buổi học
              </Btn>
            </div>
          </Card>

          <Card className="overflow-x-auto !p-0">
            <table className="w-full min-w-[700px] text-left text-sm">
              <thead className="bg-soft text-xs uppercase text-mute">
                <tr>
                  <th className="px-4 py-3">Mã lớp</th>
                  <th className="px-4 py-3">Tên môn</th>
                  <th className="px-4 py-3">Giảng viên</th>
                  <th className="px-4 py-3">Sĩ số</th>
                  <th className="px-4 py-3">Yêu cầu phòng & Thiết bị</th>
                </tr>
              </thead>
              <tbody>
                {classes.map((c) => (
                  <tr key={c.id} className="border-t border-slate-100">
                    <td className="px-4 py-3 font-semibold text-navy">{c.class_code}</td>
                    <td className="px-4 py-3">{c.course_name}</td>
                    <td className="px-4 py-3">{c.lecturer || "—"}</td>
                    <td className="px-4 py-3">{c.student_count} SV</td>
                    <td className="px-4 py-3 text-xs text-mute">
                      {roomTypeLabel(c.required_room_type)} {c.required_equipment ? `· ${c.required_equipment}` : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </>
      )}
    </div>
  );
}

/* ==================== 6. XUẤT BẢNG XẾP PHÒNG EXCEL / CSV (OFF-08) ==================== */
function ExportTab({
  online,
  rooms,
  flash,
}: {
  online: boolean;
  rooms: RoomItem[];
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [fmt, setFmt] = useState<"xlsx" | "csv">("xlsx");
  const [building, setBuilding] = useState("Tất cả");
  const [busy, setBusy] = useState(false);

  const buildings = ["Tất cả", ...Array.from(new Set(rooms.map((r) => r.building)))];

  const handleExport = async () => {
    if (!online) {
      flash("a", "Hãy chạy Backend để tải file Excel thực tế");
      return;
    }
    setBusy(true);
    try {
      const q = new URLSearchParams({ fmt });
      if (building !== "Tất cả") q.set("building", building);
      await downloadFromApi(`/api/timetable/export?${q.toString()}`, `CAMS_timetable_export.${fmt}`);
      flash("g", `Đã xuất và tải xuống CAMS_timetable_export.${fmt}`);
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Xuất file thất bại");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-5">
      <h1 className="text-[28px] font-bold">Xuất Bảng Xếp phòng hoàn chỉnh (OFF-08)</h1>
      <Card className="grid gap-4 md:grid-cols-3">
        <Field label="Học kỳ">
          <select className={inp}>
            <option>Học kỳ 1 · 2026–2027</option>
            <option>Học kỳ 2 · 2025–2026</option>
          </select>
        </Field>
        <Field label="Lọc theo Tòa nhà">
          <select className={inp} value={building} onChange={(e) => setBuilding(e.target.value)}>
            {buildings.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Định dạng tệp">
          <div className="grid grid-cols-2 gap-2">
            {(["xlsx", "csv"] as const).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFmt(f)}
                className={`h-11 rounded-xl border-2 text-sm font-semibold ${
                  fmt === f ? "border-navy bg-blue-50 text-navy" : "border-slate-200"
                }`}
              >
                {f === "xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"}
              </button>
            ))}
          </div>
        </Field>
        <div className="md:col-span-3">
          <Btn loading={busy} onClick={handleExport}>
            <I n="down" s={18} />
            Tải xuống Thời khóa biểu chính thức
          </Btn>
        </div>
      </Card>
    </div>
  );
}

/* ==================== 7. QUẢN TRỊ USER RBAC (ADM-01) & CẤU HÌNH / AUDIT LOG (ADM-03..05) ==================== */
function UsersAdminTab({
  online,
  flash,
}: {
  online: boolean;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [uName, setUName] = useState("");
  const [uPass, setUPass] = useState("123");
  const [uFull, setUFull] = useState("");
  const [uRole, setURole] = useState<Role>("OFFICER");
  const [uStudentCode, setUStudentCode] = useState("");

  const load = async () => {
    if (!online) return;
    try {
      setUsers(await apiFetch<AuthUser[]>("/api/auth/users"));
    } catch {
      // Ignore
    }
  };

  useEffect(() => {
    load();
  }, [online]);

  const createUser = async () => {
    if (!uName.trim() || !uFull.trim()) {
      flash("a", "Nhập đủ tài khoản và họ tên");
      return;
    }
    try {
      await apiFetch("/api/auth/users", {
        method: "POST",
        body: JSON.stringify({
          username: uName.trim(),
          password: uPass,
          full_name: uFull.trim(),
          role: uRole,
          student_code: uStudentCode.trim() || null,
        }),
      });
      setUName("");
      setUFull("");
      setUStudentCode("");
      await load();
      flash("g", "Đã tạo tài khoản mới thành công");
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Lỗi tạo tài khoản");
    }
  };

  const toggleActive = async (u: AuthUser) => {
    try {
      await apiFetch(`/api/auth/users/${u.id}/toggle-active`, { method: "PATCH" });
      await load();
      flash("g", `Đã ${u.is_active ? "khóa" : "mở khóa"} tài khoản @${u.username}`);
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Thao tác thất bại");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[28px] font-bold">Quản lý Tài khoản & Phân quyền RBAC (ADM-01)</h1>
        <p className="text-sm text-mute">Phân quyền nghiêm ngặt 4 vai trò, mật khẩu băm PBKDF2-HMAC-SHA256</p>
      </div>

      <Card className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
        <Field label="Tên đăng nhập">
          <input className={inp} value={uName} onChange={(e) => setUName(e.target.value)} placeholder="officer02" />
        </Field>
        <Field label="Họ và tên">
          <input className={inp} value={uFull} onChange={(e) => setUFull(e.target.value)} placeholder="Trần Ngọc Duy" />
        </Field>
        <Field label="Vai trò (Role)">
          <select className={inp} value={uRole} onChange={(e) => setURole(e.target.value as Role)}>
            <option value="ADMIN">ADMIN (Quản trị)</option>
            <option value="OFFICER">OFFICER (Đào tạo)</option>
            <option value="LECTURER">LECTURER (Giảng viên)</option>
            <option value="STUDENT">STUDENT (Sinh viên)</option>
          </select>
        </Field>
        <Field label="MSSV (Nếu SV)">
          <input className={inp} value={uStudentCode} onChange={(e) => setUStudentCode(e.target.value)} placeholder="SV002" />
        </Field>
        <Field label="Mật khẩu">
          <input className={inp} value={uPass} onChange={(e) => setUPass(e.target.value)} />
        </Field>
        <div className="flex items-end">
          <Btn className="w-full" onClick={createUser}>
            <I n="plus" s={16} />
            Tạo tài khoản
          </Btn>
        </div>
      </Card>

      <Card className="overflow-x-auto !p-0">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-soft text-xs uppercase text-mute">
            <tr>
              <th className="px-4 py-3">Username</th>
              <th className="px-4 py-3">Họ tên</th>
              <th className="px-4 py-3">Vai trò</th>
              <th className="px-4 py-3">MSSV / Đơn vị</th>
              <th className="px-4 py-3">Trạng thái</th>
              <th className="px-4 py-3 text-right">Khóa / Mở</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-slate-100">
                <td className="px-4 py-3 font-semibold text-navy">@{u.username}</td>
                <td className="px-4 py-3">{u.full_name}</td>
                <td className="px-4 py-3">
                  <Chip t={u.role === "ADMIN" ? "r" : u.role === "OFFICER" ? "y" : u.role === "LECTURER" ? "b" : "g"}>
                    {u.role}
                  </Chip>
                </td>
                <td className="px-4 py-3 text-xs text-mute">
                  {u.student_code ? `MSSV: ${u.student_code} · ` : ""}
                  {u.department || "—"}
                </td>
                <td className="px-4 py-3">
                  <Chip t={u.is_active ? "g" : "x"}>{u.is_active ? "Hoạt động" : "Đang khóa"}</Chip>
                </td>
                <td className="px-4 py-3 text-right">
                  <Btn v="s" className="!h-8 !px-3 !text-xs" onClick={() => toggleActive(u)}>
                    {u.is_active ? "Khóa" : "Mở khóa"}
                  </Btn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function GovernanceTab({
  online,
  settings,
  onReloadSettings,
  flash,
}: {
  online: boolean;
  settings: SystemSettingsData | null;
  onReloadSettings: () => Promise<void>;
  flash: (t: "r" | "a" | "g", m: string) => void;
}) {
  const [firstDate, setFirstDate] = useState(settings?.first_closure_date || "2026-12-15");
  const [finalDate, setFinalDate] = useState(settings?.final_closure_date || "2026-12-31");
  const [enforce, setEnforce] = useState(settings?.enforce_closure ?? true);
  const [logs, setLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    if (settings) {
      setFirstDate(settings.first_closure_date);
      setFinalDate(settings.final_closure_date);
      setEnforce(settings.enforce_closure);
    }
  }, [settings]);

  useEffect(() => {
    if (!online) return;
    apiFetch<AuditLogItem[]>("/api/audit-logs?limit=50")
      .then(setLogs)
      .catch(() => {});
  }, [online, settings]);

  const saveSettings = async () => {
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          first_closure_date: firstDate,
          final_closure_date: finalDate,
          enforce_closure: enforce,
        }),
      });
      await onReloadSettings();
      const freshLogs = await apiFetch<AuditLogItem[]>("/api/audit-logs?limit=50");
      setLogs(freshLogs);
      flash("g", "Đã lưu cấu hình Closure Dates (ADM-04 / BR-03)");
    } catch (err) {
      flash("r", err instanceof Error ? err.message : "Lỗi cập nhật cấu hình");
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-[28px] font-bold">Cấu hình Hệ thống & Nhật ký Kiểm toán (ADM-03, ADM-04, ADM-05)</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold">Mốc thời hạn Closure Dates (BR-03)</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="First Closure Date (Khóa nạp & xếp TKB)">
              <input type="date" className={inp} value={firstDate} onChange={(e) => setFirstDate(e.target.value)} />
            </Field>
            <Field label="Final Closure Date (Chế độ Read-only)">
              <input type="date" className={inp} value={finalDate} onChange={(e) => setFinalDate(e.target.value)} />
            </Field>
          </div>
          <label className="flex items-center gap-2 text-sm font-medium">
            <input type="checkbox" checked={enforce} onChange={(e) => setEnforce(e.target.checked)} className="size-4 accent-navy" />
            Kích hoạt kiểm soát tự động chính sách khóa hệ thống theo ngày (BR-03)
          </label>
          <Btn onClick={saveSettings}>Lưu cấu hình thời hạn</Btn>
        </Card>

        <Card className="space-y-3">
          <h2 className="text-lg font-semibold">Khung Ca tiết học chuẩn của trường (ADM-03)</h2>
          <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
            {(settings?.shifts || SHIFTS.map((s) => ({ shift_number: s.n, shift_name: s.name, period_range: s.periods, start_time: s.start.slice(0, 5), end_time: s.end.slice(0, 5) }))).map(
              (sh) => (
                <div key={sh.shift_number} className="rounded-xl bg-soft p-3">
                  <b className="text-navy">{sh.shift_name}</b> ({sh.period_range})
                  <p className="mt-0.5 text-mute">
                    {sh.start_time} – {sh.end_time}
                  </p>
                </div>
              ),
            )}
          </div>
        </Card>
      </div>

      <Card className="overflow-x-auto !p-0">
        <div className="flex items-center justify-between p-6 pb-3">
          <div>
            <h2 className="text-lg font-semibold">Nhật ký Kiểm toán Hệ thống (Audit Trail - BR-04)</h2>
            <p className="text-xs text-mute">Bản ghi chỉ đọc, tự động lưu vết mọi thao tác gán/đổi phòng, phê duyệt và quản trị</p>
          </div>
          <Chip t="b">{logs.length} bản ghi gần nhất</Chip>
        </div>
        <table className="w-full min-w-[820px] text-left text-xs">
          <thead className="bg-soft uppercase text-mute">
            <tr>
              <th className="px-4 py-2.5">Thời gian</th>
              <th className="px-4 py-2.5">Người thực hiện</th>
              <th className="px-4 py-2.5">Hành động</th>
              <th className="px-4 py-2.5">Đối tượng</th>
              <th className="px-4 py-2.5">Giá trị cũ → Mới</th>
              <th className="px-4 py-2.5">Ghi chú / Lý do</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((lg) => (
              <tr key={lg.id} className="border-t border-slate-100">
                <td className="px-4 py-2.5 whitespace-nowrap text-mute">{lg.created_at}</td>
                <td className="px-4 py-2.5 font-medium">
                  {lg.actor_name} <span className="text-mute">({lg.actor_role})</span>
                </td>
                <td className="px-4 py-2.5">
                  <Chip t="b">{lg.action}</Chip>
                </td>
                <td className="px-4 py-2.5 font-semibold text-navy">{lg.target}</td>
                <td className="px-4 py-2.5">
                  {lg.old_value} → <b>{lg.new_value}</b>
                </td>
                <td className="px-4 py-2.5 text-mute">{lg.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

/* ==================== STAFF / ADMIN SHELL ==================== */
export function StaffWorkspace({
  user,
  online,
  onLogout,
}: {
  user: AuthUser;
  online: boolean;
  onLogout: () => void;
}) {
  const [tab, setTab] = useState("assign");
  const [rooms, setRooms] = useState<RoomItem[]>(FALLBACK_ROOMS);
  const [sessions, setSessions] = useState<EnrichedSession[]>(FALLBACK_SESSIONS);
  const [settings, setSettings] = useState<SystemSettingsData | null>(null);
  const [toast, setToast] = useState<{ t: "r" | "a" | "g"; m: string } | null>(null);

  const flash = (t: "r" | "a" | "g", m: string) => {
    setToast({ t, m });
    window.setTimeout(() => setToast(null), 3500);
  };

  const reloadAll = async () => {
    if (!online) return;
    try {
      const [rm, tt, cfg] = await Promise.all([
        apiFetch<RoomItem[]>("/api/rooms"),
        apiFetch<{ sessions: EnrichedSession[] }>("/api/lookup/timetable"),
        apiFetch<SystemSettingsData>("/api/settings"),
      ]);
      setRooms(rm);
      setSessions(tt.sessions);
      setSettings(cfg);
    } catch {
      // Keep fallback
    }
  };

  useEffect(() => {
    reloadAll();
  }, [online]);

  const navItems: Array<[string, string, string, string]> = [
    ["dashboard", "Thống kê", "Analytics", "chart"],
    ["import", "Import TKB", "Import Excel", "down"],
    ["assign", "Xếp phòng", "Auto & Grid", "bolt"],
    ["approve", "Duyệt đổi phòng", "Approvals", "check"],
    ["catalog", "Phòng & Lớp", "Rooms & Classes", "grid"],
    ["export", "Xuất Excel", "Export", "list"],
    ["governance", "Cấu hình & Log", "Closure & Audit", "cog"],
  ];
  if (user.role === "ADMIN") {
    navItems.push(["users", "Tài khoản RBAC", "User Admin", "shield"]);
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/60 to-slate-100 lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col bg-white p-4 shadow-sm lg:flex">
        <div className="mb-3 flex items-center gap-3 px-2">
          <div className="grid size-10 place-items-center rounded-xl bg-navy text-white">
            <I n="grad" />
          </div>
          <div>
            <b className="block text-navy leading-tight">CAMS · UniRoom</b>
            <span className="text-[11px] text-mute">{online ? "🟢 Đã kết nối Backend" : "🟠 Figma Preview"}</span>
          </div>
        </div>
        <span className="mx-2 mb-4 w-fit rounded-full bg-amber/20 px-3 py-1 text-xs font-semibold text-amber-900">
          {user.role === "ADMIN" ? "Quản trị viên (Admin)" : "Cán bộ Đào tạo"}
        </span>
        <nav className="flex-1 space-y-1 overflow-y-auto">
          {navItems.map(([k, l, en, icon]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition ${
                tab === k ? "bg-navy text-white" : "text-mute hover:bg-soft"
              }`}
            >
              <I n={icon} s={18} />
              <span className="text-left leading-tight">
                {l}
                <span className={`block text-[11px] font-normal ${tab === k ? "text-blue-100" : "text-slate-500"}`}>
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
            <span className="text-mute">@{user.username}</span>
          </span>
          <button aria-label="Đăng xuất" onClick={onLogout} className="text-mute hover:text-red-600" title="Đăng xuất">
            <I n="out" s={18} />
          </button>
        </div>
      </aside>

      <header className="sticky top-0 z-20 flex items-center justify-between bg-white/90 px-4 py-3 backdrop-blur lg:px-8">
        <div className="flex items-center gap-2">
          <span className="rounded-full bg-amber/20 px-3 py-1 text-xs font-semibold text-amber-900">
            {user.role === "ADMIN" ? "ADMIN" : "OFFICER"} · {user.full_name}
          </span>
          <Chip t={online ? "g" : "y"}>{online ? "API Live" : "Figma Mock"}</Chip>
        </div>
        <button onClick={onLogout} className="text-sm font-semibold text-red-600 hover:underline">
          Đăng xuất
        </button>
      </header>

      <main className="mx-auto max-w-[1220px] p-4 pb-28 lg:p-8">
        {tab === "dashboard" && (
          <DashboardTab online={online} sessions={sessions} rooms={rooms} onRefreshAll={reloadAll} flash={flash} />
        )}
        {tab === "import" && (
          <ImportTKBTab online={online} settings={settings} onImported={reloadAll} flash={flash} />
        )}
        {tab === "assign" && (
          <AssignTab online={online} sessions={sessions} rooms={rooms} settings={settings} onReload={reloadAll} flash={flash} />
        )}
        {tab === "approve" && <ApproveTab online={online} onReload={reloadAll} flash={flash} />}
        {tab === "catalog" && <CatalogTab online={online} rooms={rooms} onReload={reloadAll} flash={flash} />}
        {tab === "export" && <ExportTab online={online} rooms={rooms} flash={flash} />}
        {tab === "governance" && (
          <GovernanceTab online={online} settings={settings} onReloadSettings={reloadAll} flash={flash} />
        )}
        {tab === "users" && user.role === "ADMIN" && <UsersAdminTab online={online} flash={flash} />}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-slate-200 bg-white lg:hidden">
        {navItems.slice(0, 5).map(([k, l, , icon]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${tab === k ? "text-navy" : "text-mute"}`}
          >
            <I n={icon} s={20} />
            {l}
          </button>
        ))}
      </nav>

      {toast && (
        <div className="fixed bottom-20 left-1/2 z-50 -translate-x-1/2 lg:bottom-8">
          <ToastBanner {...toast} />
        </div>
      )}
    </div>
  );
}
