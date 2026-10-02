import { useCallback, useEffect, useState } from 'react'

import { fetchHealth, type HealthPayload } from '../lib/api'
import { dependencyTone, formatUptime, summariseHealth, type Tone } from '../lib/health'

type State =
  | { kind: 'loading' }
  | { kind: 'ok'; payload: HealthPayload; roundTripMs: number }
  | { kind: 'error'; message: string }

const TONE_CHIP: Record<Tone, string> = {
  ok: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
  warn: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
  error: 'border-rose-500/40 bg-rose-500/10 text-rose-300',
  neutral: 'border-slate-600/60 bg-slate-500/10 text-slate-300',
}

const BACKEND_START_COMMAND = 'cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000'

export default function BackendStatus() {
  const [state, setState] = useState<State>({ kind: 'loading' })

  const load = useCallback(async () => {
    setState({ kind: 'loading' })
    const started = performance.now()
    try {
      const payload = await fetchHealth()
      setState({ kind: 'ok', payload, roundTripMs: Math.round(performance.now() - started) })
    } catch (error) {
      setState({ kind: 'error', message: error instanceof Error ? error.message : 'Unknown error' })
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Backend API</h2>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">
            GET /api/health → FastAPI on 127.0.0.1:8000
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-md border border-slate-700 bg-slate-800/60 px-2.5 py-1 text-xs font-medium text-slate-200 transition hover:border-sky-500/60 hover:text-white"
        >
          Re-check
        </button>
      </div>

      <div className="mt-4">
        {state.kind === 'loading' && (
          <p className="text-sm text-slate-400">Contacting the API…</p>
        )}

        {state.kind === 'error' && (
          <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 p-3">
            <p className="text-sm font-medium text-rose-200">API unreachable</p>
            <p className="mt-1 font-mono text-[11px] text-rose-200/80">{state.message}</p>
            <p className="mt-2 text-xs text-rose-200/70">
              Start it with:
              <code className="ml-1 rounded bg-slate-950/60 px-1.5 py-0.5 font-mono text-[11px]">
                {BACKEND_START_COMMAND}
              </code>
            </p>
          </div>
        )}

        {state.kind === 'ok' && (
          <div className="space-y-4">
            <div
              className={`inline-flex rounded-full border px-3 py-1 text-xs font-medium ${
                TONE_CHIP[summariseHealth(state.payload).tone]
              }`}
            >
              {summariseHealth(state.payload).label}
            </div>

            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
              <Fact label="Service" value={state.payload.service} />
              <Fact label="Version" value={state.payload.version} />
              <Fact label="Environment" value={state.payload.environment} />
              <Fact label="Demo mode" value={state.payload.demo_mode} />
              <Fact label="API uptime" value={formatUptime(state.payload.uptime_s)} />
              <Fact label="Round trip" value={`${state.roundTripMs} ms`} />
            </dl>

            <div className="space-y-2">
              {state.payload.dependencies.map((dependency) => (
                <div
                  key={dependency.name}
                  className="flex flex-wrap items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/40 px-3 py-2"
                >
                  <span className="font-mono text-[11px] text-slate-300">{dependency.name}</span>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                      TONE_CHIP[dependencyTone(dependency.status)]
                    }`}
                  >
                    {dependency.status.replace('_', ' ')}
                  </span>
                  {dependency.latency_ms !== null && (
                    <span className="text-[10px] text-slate-500">{dependency.latency_ms} ms</span>
                  )}
                  {dependency.detail && (
                    <span className="w-full text-[11px] text-slate-400">{dependency.detail}</span>
                  )}
                </div>
              ))}
              {state.payload.dependencies.length === 0 && (
                <p className="text-xs text-slate-400">No dependencies reported.</p>
              )}
            </div>

            <p className="text-[11px] text-slate-500">
              Snowflake credentials are read by the backend from the repo-root <code>.env</code> only, and are
              never sent to this browser.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] uppercase tracking-wide text-slate-500">{label}</dt>
      <dd className="font-mono text-[11px] text-slate-200">{value}</dd>
    </div>
  )
}
