"use client";

import { useEffect, useMemo, useState } from "react";
import BottomNav from "@/components/BottomNav";
import Dolphin from "@/components/Dolphin";
import { api, patch, post, User } from "@/lib/api";

function timezones(current: string): string[] {
  let list: string[] = [];
  try {
    list = (Intl as unknown as { supportedValuesOf(k: string): string[] }).supportedValuesOf("timeZone");
  } catch {}
  if (!list.includes("UTC")) list = ["UTC", ...list];
  if (!list.includes(current)) list = [current, ...list];
  return list;
}

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [form, setForm] = useState({ display_name: "", timezone: "UTC", daily_goal: 5 });
  const [status, setStatus] = useState<{ ok: boolean; msg: string } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api<User>("/me").then((u) => {
      setUser(u);
      setForm({ display_name: u.display_name, timezone: u.timezone, daily_goal: u.daily_goal });
    });
  }, []);

  const zones = useMemo(() => timezones(form.timezone), [form.timezone]);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatus(null);
    try {
      const u = await patch<User>("/me", { ...form, display_name: form.display_name.trim() });
      setUser(u);
      setStatus({ ok: true, msg: "Saved" });
    } catch (err) {
      setStatus({ ok: false, msg: err instanceof Error ? err.message : "Try again" });
    } finally {
      setSaving(false);
    }
  };

  const logout = async () => {
    await post("/auth/logout").catch(() => {});
    window.location.replace("/login");
  };

  if (!user) return <main className="shell"><p className="muted">Loading…</p><BottomNav /></main>;

  return (
    <main className="shell">
      <div className="card row" style={{ marginBottom: 14 }}>
        {user.avatar_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={user.avatar_url} alt="" width={56} height={56} style={{ borderRadius: "50%" }} referrerPolicy="no-referrer" />
        ) : (
          <Dolphin size={56} />
        )}
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: "var(--serif)", fontSize: 19 }}>{user.display_name}</div>
          <div className="small muted">{user.name}{user.email ? ` · ${user.email}` : ""}</div>
        </div>
      </div>

      <form className="card stack" onSubmit={save}>
        <div className="field">
          <label htmlFor="dn">Name</label>
          <input id="dn" value={form.display_name} maxLength={40} required
            onChange={(e) => setForm({ ...form, display_name: e.target.value })} />
        </div>
        <div className="field">
          <label htmlFor="tz">Timezone</label>
          <select id="tz" value={form.timezone} onChange={(e) => setForm({ ...form, timezone: e.target.value })}>
            {zones.map((z) => <option key={z} value={z}>{z.replaceAll("_", " ")}</option>)}
          </select>
        </div>
        <div className="field">
          <label htmlFor="goal">Daily goal · {form.daily_goal}</label>
          <input id="goal" type="range" min={1} max={20} value={form.daily_goal}
            onChange={(e) => setForm({ ...form, daily_goal: Number(e.target.value) })} style={{ padding: 0, accentColor: "var(--accent)" }} />
        </div>
        {status && <p className={status.ok ? "small" : "error"} style={status.ok ? { color: "var(--good)", margin: 0 } : undefined}>{status.msg}</p>}
        <button className="btn" disabled={saving}>{saving ? "…" : "Save"}</button>
      </form>

      <button className="btn ghost" style={{ marginTop: 14 }} onClick={logout}>Sign out</button>
      <BottomNav />
    </main>
  );
}
