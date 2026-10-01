"use client";

import Script from "next/script";
import { useCallback, useEffect, useRef, useState } from "react";
import Dolphin from "@/components/Dolphin";
import Enso from "@/components/Enso";
import { api, browserTimezone, post } from "@/lib/api";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize(opts: { client_id: string; callback: (r: { credential: string }) => void; ux_mode?: string }): void;
          renderButton(el: HTMLElement, opts: Record<string, unknown>): void;
        };
      };
    };
  }
}

interface AuthConfig {
  google_client_id: string | null;
  dev_login: boolean;
}

export default function LoginPage() {
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [gsiReady, setGsiReady] = useState(false);
  const buttonRef = useRef<HTMLDivElement>(null);

  const loadConfig = useCallback(() => {
    setError(null);
    api<AuthConfig>("/auth/config")
      .then(setConfig)
      .catch(() => setError("Can't connect"));
  }, []);

  useEffect(loadConfig, [loadConfig]);

  const finish = () => window.location.replace("/");

  const onGoogle = useCallback(async (credential: string) => {
    setBusy(true);
    setError(null);
    try {
      await post("/auth/google", { credential, timezone: browserTimezone() });
      finish();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed");
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!gsiReady || !config?.google_client_id || !buttonRef.current || !window.google) return;
    window.google.accounts.id.initialize({
      client_id: config.google_client_id,
      callback: (r) => onGoogle(r.credential),
    });
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: "outline",
      size: "large",
      shape: "pill",
      text: "continue_with",
      width: 300,
    });
  }, [gsiReady, config, onGoogle]);

  const devLogin = async () => {
    setBusy(true);
    setError(null);
    try {
      await post("/auth/dev", { timezone: browserTimezone() });
      finish();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Sign-in failed");
      setBusy(false);
    }
  };

  return (
    <main className="shell" style={{ display: "flex", flexDirection: "column", justifyContent: "center", paddingBottom: 32 }}>
      {config?.google_client_id && (
        <Script src="https://accounts.google.com/gsi/client" strategy="afterInteractive" onReady={() => setGsiReady(true)}
          onError={() => setError("Google sign-in unavailable")} />
      )}
      <div style={{ textAlign: "center" }}>
        <Enso value={1} total={1} size={168}><Dolphin size={96} /></Enso>
        <h1 className="h1" style={{ fontSize: 34, marginTop: 20 }}>Pattern Quiz</h1>
        <p className="muted" style={{ fontSize: 16, margin: "10px 0 32px" }}>Pick the best approach.</p>
      </div>

      <div className="stack" style={{ alignItems: "center" }}>
        {config?.google_client_id && <div ref={buttonRef} style={{ minHeight: 44 }} aria-busy={busy} />}
        {config?.dev_login && (
          <button className={config.google_client_id ? "btn ghost" : "btn"} onClick={devLogin} disabled={busy}>
            {busy ? "…" : "Try demo"}
          </button>
        )}
        {config && !config.google_client_id && !config.dev_login && (
          <p className="error">Sign-in unavailable</p>
        )}
        {error && (
          <div className="error" role="alert" style={{ width: "100%" }}>
            {error}{" "}
            <button onClick={config ? () => setError(null) : loadConfig} style={{ border: 0, background: "none", textDecoration: "underline", cursor: "pointer", color: "inherit", padding: 0 }}>
              Retry
            </button>
          </div>
        )}
      </div>

      <p className="small muted" style={{ textAlign: "center", marginTop: 24 }}>Your email stays private.</p>
    </main>
  );
}
