export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      // Required on mutating requests; see backend CSRF check.
      "X-Requested-With": "quiz",
      ...(init.headers || {}),
    },
  });
  if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth")) {
    window.location.href = "/login";
    throw new ApiError(401, "Not signed in.");
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {}
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

export const post = <T,>(path: string, body?: unknown) =>
  api<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export const patch = <T,>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });

export function browserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

// ---- types

export type Mode = "daily" | "review" | "extra";

export interface User {
  id: number;
  name: string;
  display_name: string;
  email: string | null;
  avatar_url: string | null;
  timezone: string;
  daily_goal: number;
}

export interface Progress {
  session_id: number | null;
  mode?: Mode;
  total: number;
  answered: number;
  correct: number;
}

export interface Home {
  user: User;
  today: string;
  streak: number;
  daily: Progress;
  review: Progress;
  extra: Progress[];
  resume: Progress | null;
}

export interface ChoiceView {
  id: number;
  label: string;
  detail: string;
  time: string;
  space: string;
  visual: string;
}

export type Verdict = "optimal" | "suboptimal" | "incorrect";

export interface AnswerResult {
  choice_id: number;
  is_correct: boolean;
  correct_choice_id: number;
  feedback: { choice_id: number; verdict: Verdict; explanation: string }[];
}

export interface QuizItem {
  question: {
    id: number;
    title: string;
    lc_number: number | null;
    difficulty: "Easy" | "Medium" | "Hard";
    summary: string;
    example: string;
    criterion: string;
    hint: string;
    source_url: string;
    topics: { id: string; name: string }[];
    company_tags: { company: string; provenance: string; observed_on: string | null }[];
  };
  reason: string | null;
  choices: ChoiceView[];
  result: AnswerResult | null;
}

export interface QuizSession {
  id: number;
  mode: Mode;
  local_date: string;
  finished: boolean;
  items: QuizItem[];
}

export interface DashboardStats {
  totals: {
    answered: number;
    correct: number;
    accuracy: number | null;
    active_days: number;
    streak: number;
    this_week_answered: number;
    this_week_accuracy: number | null;
    last_week_answered: number;
    last_week_accuracy: number | null;
  };
  topic_accuracy: { topic: string; name: string; attempts: number; correct: number; accuracy: number }[];
  per_day: { date: string; answered: number; correct: number }[];
  weekly_topic_accuracy: Record<string, { week: string; attempts: number; accuracy: number | null }[]>;
}

export interface TopicGraph {
  nodes: { id: string; name: string; x: number; y: number; questions: number; attempts: number; mastery: number | null }[];
  edges: { from: string; to: string }[];
}

export const MODE_LABEL: Record<Mode, string> = {
  daily: "Practice",
  review: "Review",
  extra: "Extra",
};
