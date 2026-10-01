"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ApproachVisual from "@/components/ApproachVisual";
import Dolphin from "@/components/Dolphin";
import Enso from "@/components/Enso";
import { Bulb, Check, ChevronLeft, Cross, ImageIcon, More, Speaker } from "@/components/Icons";
import { AnswerResult, api, MODE_LABEL, post, QuizItem, QuizSession, Verdict } from "@/lib/api";

const VERDICT_LABEL: Record<Verdict, string> = { optimal: "Best", suboptimal: "Suboptimal", incorrect: "Wrong" };

function readStoredVisuals(): boolean {
  try {
    return localStorage.getItem("quiz.visuals") !== "off";
  } catch {
    return true;
  }
}

export default function QuizPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [session, setSession] = useState<QuizSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Order of item indexes still to show; "Skip" moves the current one to the back.
  const [queue, setQueue] = useState<number[]>([]);
  const [pending, setPending] = useState<number | null>(null);
  const [sheet, setSheet] = useState<"hint" | "explain" | null>(null);
  const [menu, setMenu] = useState(false);
  const [visuals, setVisuals] = useState(true);
  const [toast, setToast] = useState<string | null>(null);
  const [lastAnswered, setLastAnswered] = useState<number | null>(null);
  const finishedRef = useRef(false);

  useEffect(() => setVisuals(readStoredVisuals()), []);

  useEffect(() => {
    api<QuizSession>(`/sessions/${id}`)
      .then((s) => {
        setSession(s);
        const unanswered = s.items.map((_, i) => i).filter((i) => !s.items[i].result);
        setQueue(unanswered);
        const answered = s.items.map((_, i) => i).filter((i) => s.items[i].result);
        setLastAnswered(answered.length ? answered[answered.length - 1] : null);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const flash = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2200);
  };

  const index = queue[0];
  const item: QuizItem | undefined = session && index !== undefined ? session.items[index] : undefined;
  const result = item?.result ?? null;
  const total = session?.items.length ?? 0;
  const answeredCount = session?.items.filter((i) => i.result).length ?? 0;
  const allAnswered = session !== null && answeredCount === total;

  const finish = useCallback(async () => {
    if (finishedRef.current) return;
    finishedRef.current = true;
    try {
      await post(`/sessions/${id}/finish`);
    } catch {
      finishedRef.current = false;
    }
  }, [id]);

  // Refresh mastery once the last answer is in.
  useEffect(() => {
    if (allAnswered) finish();
  }, [allAnswered, finish]);

  const exit = async () => {
    await finish();
    router.push("/");
  };

  const choose = async (choiceId: number) => {
    if (!session || !item || result || pending !== null) return;
    setPending(choiceId);
    try {
      const r = await post<AnswerResult>(`/sessions/${id}/answer`, { question_id: item.question.id, choice_id: choiceId });
      setSession((s) => {
        if (!s) return s;
        const items = s.items.slice();
        items[index] = { ...items[index], result: r };
        return { ...s, items };
      });
      setLastAnswered(index);
    } catch (e) {
      flash(e instanceof Error ? e.message : "Try again");
    } finally {
      setPending(null);
    }
  };

  const next = () => {
    setSheet(null);
    setQueue((q) => q.slice(1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const skip = () => {
    if (!item || result) return;
    if (queue.length < 2) return flash("Last question");
    setQueue((q) => [...q.slice(1), q[0]]);
    flash("Skipped");
  };

  const toggleVisuals = () => {
    setVisuals((v) => {
      try {
        localStorage.setItem("quiz.visuals", v ? "off" : "on");
      } catch {}
      return !v;
    });
  };

  const speak = () => {
    if (!item || typeof window === "undefined" || !("speechSynthesis" in window)) return flash("Not supported");
    window.speechSynthesis.cancel();
    const q = item.question;
    window.speechSynthesis.speak(new SpeechSynthesisUtterance(`${q.title}. ${q.summary} ${q.criterion}`));
  };

  // Keyboard: 1-4 choose, Enter / → next, H hint, Esc closes sheets.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!item) return;
      if (e.key === "Escape") return setSheet(null);
      if (!result && ["1", "2", "3", "4"].includes(e.key)) choose(item.choices[Number(e.key) - 1].id);
      if (result && (e.key === "Enter" || e.key === "ArrowRight")) next();
      if (e.key.toLowerCase() === "h") setSheet("hint");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const recap = useMemo(() => {
    if (!session || lastAnswered === null) return null;
    const prev = session.items[lastAnswered];
    if (!prev.result || lastAnswered === index) return null;
    const best = prev.choices.find((c) => c.id === prev.result!.correct_choice_id);
    return { title: prev.question.title, best: best?.label ?? "", ok: prev.result.is_correct };
  }, [session, lastAnswered, index]);

  if (error) {
    return (
      <main className="shell">
        <p className="error">{error}</p>
        <button className="btn ghost" onClick={() => router.push("/")}>Back home</button>
      </main>
    );
  }
  if (!session) return <main className="shell"><p className="muted">Loading…</p></main>;

  // ---------- completion screen
  // The queue only holds unanswered items (plus the one just answered), so empty means complete.
  if (!item) {
    const correct = session.items.filter((i) => i.result?.is_correct).length;
    const ratio = total ? correct / total : 0;
    return (
      <main className="shell" style={{ textAlign: "center", paddingTop: 48 }}>
        <Enso value={correct} total={total} size={170}>
          <div style={{ fontFamily: "var(--serif)", fontSize: 34, lineHeight: 1 }}>{correct}<span className="muted" style={{ fontSize: 20 }}> / {total}</span></div>
        </Enso>
        <div style={{ marginTop: 16 }}><Dolphin size={44} mood={ratio >= 0.6 ? "cheer" : "think"} /></div>
        <div className="card stack" style={{ textAlign: "left", margin: "20px 0" }}>
          {session.items.map((it) => {
            const best = it.choices.find((c) => c.id === it.result?.correct_choice_id);
            return (
              <div key={it.question.id} className="row" style={{ justifyContent: "space-between" }}>
                <span style={{ minWidth: 0 }}>
                  <b>{it.question.title}</b>
                  <span className="small muted" style={{ display: "block" }}>{best?.label}</span>
                </span>
                <span style={{ color: it.result?.is_correct ? "var(--good)" : "var(--bad)" }}>
                  {it.result?.is_correct ? <Check size={20} /> : <Cross size={20} />}
                </span>
              </div>
            );
          })}
        </div>
        <div className="stack">
          <button className="btn" onClick={exit}>Done</button>
          <button className="btn ghost" onClick={() => router.push("/dashboard")}>Progress</button>
        </div>
      </main>
    );
  }

  const q = item.question;
  const feedback = result ? Object.fromEntries(result.feedback.map((f) => [f.choice_id, f])) : {};
  const mine = result ? feedback[result.choice_id] : null;
  const bestChoice = result ? item.choices.find((c) => c.id === result.correct_choice_id) : null;

  return (
    <main className="shell" style={{ paddingBottom: 120 }}>
      {/* top bar: back, previous recap, progress */}
      <div className="card topbar">
        <div className="row" style={{ gap: 6 }}>
          <button className="icon-btn" onClick={exit} aria-label="Save and exit" style={{ marginLeft: -10 }}>
            <ChevronLeft />
          </button>
          <div className="recap" style={{ flex: 1 }}>
            {recap ? (
              <>
                <span style={{ color: recap.ok ? "var(--good)" : "var(--bad)", fontWeight: 700 }}>{recap.ok ? "✓" : "✗"}</span>{" "}
                {recap.title}: {recap.best}
              </>
            ) : (
              MODE_LABEL[session.mode]
            )}
          </div>
        </div>
        <div className="row" style={{ marginTop: 10, paddingLeft: 38 }}>
          <div className="progress" style={{ flex: 1 }} role="progressbar" aria-valuenow={answeredCount} aria-valuemax={total}>
            <span style={{ width: `${Math.max(4, (100 * answeredCount) / total)}%` }} />
          </div>
          <span className="small muted" style={{ minWidth: 34, textAlign: "right" }}>{answeredCount}/{total}</span>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", margin: "14px 0 10px", position: "relative" }}>
        <button className="icon-btn round" onClick={() => setMenu((m) => !m)} aria-label="More options" aria-expanded={menu}>
          <More />
        </button>
        {menu && (
          <div className="menu" onMouseLeave={() => setMenu(false)}>
            <a href={q.source_url} target="_blank" rel="noreferrer">LeetCode ↗</a>
            <button onClick={() => { setMenu(false); setSheet("hint"); }}>Hint</button>
            <button onClick={exit}>Exit</button>
            {q.company_tags.map((t) => (
              <div key={t.company} className="note">
                {t.company} · {t.provenance}{t.observed_on ? ` · ${t.observed_on}` : ""}
              </div>
            ))}
            {item.reason && <div className="note">{item.reason}</div>}
          </div>
        )}
      </div>

      {/* the "picture": problem statement framed like a photo card */}
      <div className="problem-frame">
        <div className="problem-inner">
          {q.summary}
          {q.example && <pre>{q.example}</pre>}
        </div>
      </div>

      <h1 className="q-title">{q.title}</h1>
      <div className="q-meta">
        <span className={`chip ${q.difficulty}`}>{q.difficulty}</span>
        {q.lc_number && <span className="chip">#{q.lc_number}</span>}
        {q.topics.map((t) => <span key={t.id} className="chip">{t.name}</span>)}
      </div>
      <p className="q-criterion">{q.criterion}</p>

      <div className="choices">
        {item.choices.map((c, i) => {
          const f = feedback[c.id];
          let cls = "choice";
          if (pending === c.id) cls += " pending";
          if (result) {
            if (c.id === result.correct_choice_id) cls += " optimal";
            else if (c.id === result.choice_id) cls += " wrong";
            else cls += " dim";
          }
          return (
            <button key={c.id} className={cls} onClick={() => choose(c.id)} disabled={!!result || pending !== null}
              aria-label={`Option ${i + 1}: ${c.label}. ${c.time} time, ${c.space} space.`}>
              {result && f && (c.id === result.correct_choice_id || c.id === result.choice_id) && (
                <span className={`badge ${f.verdict}`}>{VERDICT_LABEL[f.verdict]}</span>
              )}
              {visuals && <span className="visual"><ApproachVisual kind={c.visual} /></span>}
              <span className="label">{c.label}</span>
              {!visuals && <span className="detail">{c.detail}</span>}
              <span className="cx"><span>⏱ {c.time}</span><span>▦ {c.space}</span></span>
            </button>
          );
        })}
      </div>

      {result && mine && (
        <div className="card pop" style={{ marginTop: 14 }}>
          <div className="row" style={{ alignItems: "flex-start" }}>
            <Dolphin size={52} mood={result.is_correct ? "cheer" : "think"} />
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: "var(--serif)", fontWeight: 500, fontSize: 18, color: result.is_correct ? "var(--good)" : mine.verdict === "suboptimal" ? "var(--warn)" : "var(--bad)" }}>
                {VERDICT_LABEL[mine.verdict]}
              </div>
              <p style={{ margin: "4px 0 0", fontSize: 14.5, lineHeight: 1.5 }}>{mine.explanation}</p>
              {!result.is_correct && bestChoice && (
                <p className="small" style={{ margin: "8px 0 0" }}>
                  <b>{bestChoice.label}</b> — {feedback[bestChoice.id].explanation}
                </p>
              )}
            </div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} onClick={next}>
            {queue.length > 1 ? "Next" : "Finish"}
          </button>
        </div>
      )}

      {/* bottom toolbar, mirroring the reference layout */}
      <div className="toolbar">
        <div className="toolbar-inner">
          <button className={`icon-btn ${visuals ? "on" : ""}`} onClick={toggleVisuals} aria-label={visuals ? "Show text descriptions" : "Show approach pictures"} title="Pictures / text">
            <ImageIcon />
          </button>
          <button className="icon-btn" onClick={skip} disabled={!!result} aria-label="Skip for now" title="Skip">
            <span className="skip-glyph">Skip</span>
          </button>
          <button className="icon-btn" onClick={() => (result ? setSheet("explain") : setSheet("hint"))} aria-label="Socratic explanation" title="Ask the tutor">
            <span className="ai-glyph">Ai</span>
          </button>
          <button className={`icon-btn ${sheet === "hint" ? "on" : ""}`} onClick={() => setSheet("hint")} aria-label="Hint" title="Hint (H)">
            <Bulb />
          </button>
          <button className="icon-btn" onClick={speak} aria-label="Read aloud" title="Read aloud">
            <Speaker />
          </button>
        </div>
      </div>

      {sheet && (
        <>
          <div className="sheet-backdrop" onClick={() => setSheet(null)} />
          <div className="sheet" role="dialog" aria-label={sheet === "hint" ? "Hint" : "Explanations"}>
            <div className="grabber" />
            {sheet === "hint" || !result ? (
              <div className="row" style={{ alignItems: "flex-start", marginBottom: 8 }}>
                <Dolphin size={56} mood="think" />
                <div className="bubble" style={{ flex: 1 }}>
                  {q.hint}
                </div>
              </div>
            ) : (
              <>
                {item.choices
                  .slice()
                  .sort((a, b) => (a.id === result.correct_choice_id ? -1 : b.id === result.correct_choice_id ? 1 : 0))
                  .map((c) => {
                    const f = feedback[c.id];
                    return (
                      <div key={c.id} className={`fb ${c.id === result.choice_id ? "mine" : ""}`}>
                        <div className="fb-head">
                          <span>{c.label}</span>
                          <span className={`badge ${f.verdict}`}>
                            {VERDICT_LABEL[f.verdict]}
                          </span>
                        </div>
                        <div className="small muted" style={{ marginBottom: 6 }}>{c.time} · {c.space}</div>
                        {f.explanation}
                      </div>
                    );
                  })}
              </>
            )}
          </div>
        </>
      )}

      {toast && <div className="toast" role="status">{toast}</div>}
    </main>
  );
}
