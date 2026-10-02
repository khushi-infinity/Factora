import { Suspense, lazy } from 'react'

import BackendStatus from './components/BackendStatus'
import PanelBoundary from './components/PanelBoundary'
import PlannedPages from './components/PlannedPages'
import StackCheck from './components/StackCheck'

// three.js is ~1 MB minified: load the 3D panel on demand so it stays out of the initial bundle.
const TwinPreview3D = lazy(() => import('./components/TwinPreview3D'))

/**
 * M1 shell only. No product pages yet (PROJECT_SPEC.md §11 → M6): this page exists to prove
 * the toolchain works end to end — Vite + React + Tailwind render, Recharts and
 * react-three-fiber mount, and the SPA can reach the FastAPI BFF.
 */
export default function App() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-4">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-50">
              Factora <span className="text-sky-400">/</span> Operational Digital Twin
            </h1>
            <p className="mt-0.5 text-xs text-slate-400">
              Snowflake CoCo CLI Hackathon 2026 · GCC Edition — predictive maintenance for the plant floor
            </p>
          </div>
          <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
            M1 scaffold — no product pages yet
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-5 px-6 py-6 lg:grid-cols-2">
        <BackendStatus />
        <StackCheck />
        <PanelBoundary label="3D twin toolchain">
          <Suspense fallback={<PanelFallback title="3D twin toolchain" />}>
            <TwinPreview3D />
          </Suspense>
        </PanelBoundary>
        <PlannedPages />
      </main>

      <footer className="mx-auto max-w-6xl px-6 pb-10 text-xs leading-relaxed text-slate-500">
        <p>
          <span className="font-medium text-slate-400">Boundary rules</span> (PROJECT_SPEC.md §3.5): this SPA
          never talks to Snowflake. It calls the FastAPI BFF, which owns every query and is the only place the
          connector is imported. Health scores, predictions, explanations and costs are computed in Snowflake —
          never inside a React component.
        </p>
      </footer>
    </div>
  )
}

function PanelFallback({ title }: { title: string }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <h2 className="text-sm font-semibold text-slate-100">{title}</h2>
      <p className="mt-3 text-xs text-slate-400">Loading the three.js bundle…</p>
    </section>
  )
}
