"use client";

import { useEffect, useState } from "react";

type Status = "checking" | "connected" | "unavailable";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const controller = new AbortController();

    async function checkBackend() {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, {
          signal: controller.signal,
          cache: "no-store",
        });

        setStatus(response.ok ? "connected" : "unavailable");
      } catch {
        if (!controller.signal.aborted) {
          setStatus("unavailable");
        }
      }
    }

    checkBackend();

    return () => controller.abort();
  }, []);

  const isConnected = status === "connected";

  return (
    <div
      className="inline-flex min-h-10 items-center gap-2 rounded-full border border-slate-200 bg-white px-4 text-sm font-medium text-slate-700 shadow-sm"
      aria-live="polite"
    >
      <span
        className={`h-2.5 w-2.5 rounded-full ${
          isConnected
            ? "bg-emerald-500"
            : status === "checking"
              ? "bg-amber-400"
              : "bg-rose-500"
        }`}
      />
      {isConnected ? "Backend: Connected" : "Backend: Unavailable"}
    </div>
  );
}
