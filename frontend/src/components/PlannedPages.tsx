/**
 * Route inventory copied from PROJECT_SPEC.md §2 — shown so the shell is honest about what is
 * missing. Scope labels are the spec's, not a promise about this build.
 */
const PLANNED_ROUTES = [
  { path: '/', page: 'Factory Twin', scope: 'MVP' },
  { path: '/machines/:machineId', page: 'Machine 360', scope: 'MVP' },
  { path: '/predictions', page: 'Risk Board', scope: 'MVP' },
  { path: '/predictions/:predictionId', page: 'Diagnosis & Explanation', scope: 'MVP' },
  { path: '/parts', page: 'Spare Parts & Readiness', scope: 'MVP' },
  { path: '/work-orders', page: 'Preventive Work Orders', scope: 'MVP' },
  { path: '/impact', page: 'Production Impact', scope: 'MVP' },
  { path: '/demo', page: 'Run of Show', scope: 'MVP' },
  { path: '/copilot', page: 'Ask Factora', scope: 'Stretch' },
  { path: '/system', page: 'Data & Trust', scope: 'Stretch' },
] as const

const SCOPE_CLASSES: Record<string, string> = {
  MVP: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
  Stretch: 'border-violet-500/40 bg-violet-500/10 text-violet-300',
}

export default function PlannedPages() {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Product pages</h2>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">
            planned routes · nothing routed yet
          </p>
        </div>
        <span className="rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-300">
          0 / 10 built
        </span>
      </div>

      <ul className="mt-3 divide-y divide-slate-800/80">
        {PLANNED_ROUTES.map((route) => (
          <li key={route.path} className="flex items-center justify-between gap-3 py-1.5">
            <span className="flex min-w-0 items-baseline gap-2">
              <code className="shrink-0 font-mono text-[11px] text-slate-400">{route.path}</code>
              <span className="truncate text-xs text-slate-300">{route.page}</span>
            </span>
            <span
              className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                SCOPE_CLASSES[route.scope]
              }`}
            >
              {route.scope}
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-3 text-[11px] text-slate-500">
        Demo spine (PROJECT_SPEC.md §9): Factory Twin → CNC-03 critical → prediction → AI explanation → part
        check → work order.
      </p>
    </section>
  )
}
