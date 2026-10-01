"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import BottomNav from "@/components/BottomNav";
import Dolphin from "@/components/Dolphin";
import Enso from "@/components/Enso";
import { api, ApiError, Home, MODE_LABEL, Mode, post, Progress, QuizSession } from "@/lib/api";

function greeting(name: string): string {
  const h = new Date().getHours();
  const hello = h < 12 && h >= 5 ? "Good morning" : h >= 12 && h < 18 ? "Good afternoon" : "Good evening";
  return `${hello}, ${name}`;
}

function TaskCard({
  icon, title, subtitle, progress, onClick, disabled,
}: { icon: string; title: string; subtitle: string; progress?: Progress; onClick: () => void; disabled?: boolean }) {
  const pct = progress && progress.total ? (100 * progress.answered) / progress.total : 0;
  return (
    <button className="task" onClick={onClick} disabled={disabled} style={{ opacity: disabled ? 0.45 : 1 }}>
      <span className="ico">{icon}</span>
      <span className="body">
        <span className="title">{title}</span>
        <span className="small muted" style={{ display: "block", marginTop: 2 }}>{subtitle}</span>
        {progress && pct > 0 && <span className="progress" style={{ display: "block", marginTop: 10 }}><span style={{ width: `${pct}%` }} /></span>}
      </span>
      <span className="arrow" aria-hidden="true">→</span>
    </button>
  );
}

export default function HomePage() {
  const router = useRouter();
  const [home, setHome] = useState<Home | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<Mode | null>(null);

  useEffect(() => {
    api<Home>("/home").then(setHome).catch((e) => setError(e.message));
  }, []);

  const start = async (mode: Mode) => {
    setBusy(mode);
    setError(null);
    try {
      const s = await post<QuizSession>("/sessions", { mode });
      router.push(`/quiz/${s.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Try again");
      setBusy(null);
    }
  };

  if (!home) {
    return (
      <main className="shell">
        {error ? <p className="error">{error}</p> : <p className="muted">Loading…</p>}
      </main>
    );
  }

  const name = home.user.display_name.split(" ")[0];
  const { daily, review } = home;
  const dailyDone = daily.session_id !== null && daily.answered >= daily.total;
  const reviewDone = review.total === 0 || review.answered >= review.total;

  const dateLabel = new Date(home.today + "T12:00:00").toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });

  return (
    <main className="shell">
      <div className="eyebrow">{dateLabel}</div>
      <div className="greeting" style={{ marginTop: 10 }}>
        <p className="bubble" style={{ margin: 0, flex: 1 }}>{greeting(name)}</p>
        <Dolphin size={48} mood={dailyDone ? "cheer" : "happy"} />
      </div>

      <div style={{ margin: "36px 0 28px" }}>
        <Enso value={daily.answered} total={daily.total} size={196}>
          <div>
            <div style={{ fontFamily: "var(--serif)", fontSize: 34, lineHeight: 1 }}>{daily.answered}<span className="muted" style={{ fontSize: 20 }}> / {daily.total}</span></div>
          </div>
        </Enso>
      </div>

      <div className="stats" style={{ gridTemplateColumns: "1fr 1fr", marginBottom: 32 }}>
        <div className="stat"><div className="v">{home.streak}</div><div className="l">streak</div></div>
        <div className="stat"><div className="v">{review.total - review.answered}</div><div className="l">to review</div></div>
      </div>

      {home.resume && (
        <button className="btn" style={{ marginBottom: 24 }} onClick={() => router.push(`/quiz/${home.resume!.session_id}`)}>
          Resume · {home.resume.answered}/{home.resume.total}
        </button>
      )}

      {error && <p className="error" role="alert">{error}</p>}

      <div>
        <TaskCard
          icon="01"
          title="Practice"
          subtitle={dailyDone ? `${daily.correct}/${daily.total} correct` : `${daily.total} questions`}
          progress={daily}
          onClick={() => (daily.session_id ? router.push(`/quiz/${daily.session_id}`) : start("daily"))}
          disabled={busy !== null}
        />
        <TaskCard
          icon="02"
          title="Review"
          subtitle={
            review.total === 0
              ? "None due"
              : reviewDone
                ? `${review.correct}/${review.total} correct`
                : `${review.total - review.answered} due`
          }
          progress={review.total ? review : undefined}
          onClick={() => (review.session_id ? router.push(`/quiz/${review.session_id}`) : start("review"))}
          disabled={busy !== null || review.total === 0}
        />
        <TaskCard
          icon="03"
          title="Extra"
          subtitle={
            home.extra.length
              ? `${home.extra.length * 5} done today`
              : "5 questions"
          }
          onClick={() => start("extra")}
          disabled={busy !== null}
        />
      </div>

      <BottomNav />
    </main>
  );
}
