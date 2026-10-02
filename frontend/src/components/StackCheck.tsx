import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

/**
 * Toolchain check ONLY. This sample series exists to prove Recharts renders in this build — it is
 * explicitly not plant data. Real sensor trends come from Snowflake through the API (M3+), and
 * hardcoding plant values into a component is forbidden (PROJECT_SPEC.md §6).
 */
const TOOLCHAIN_SAMPLE = Array.from({ length: 24 }, (_, day) => ({
  day,
  baseline: 40,
  sample: Number((40 + Math.max(0, day - 10) ** 1.8 * 0.35).toFixed(2)),
}))

export default function StackCheck() {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">Chart toolchain</h2>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">Recharts · LineChart</p>
        </div>
        <span className="rounded-full border border-slate-600/60 bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-300">
          illustrative, not plant data
        </span>
      </div>

      <div className="mt-3 h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={TOOLCHAIN_SAMPLE} margin={{ top: 8, right: 8, bottom: 0, left: -18 }}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="day" stroke="#475569" tick={{ fontSize: 10 }} />
            <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
            <Tooltip
              contentStyle={{
                background: '#020617',
                border: '1px solid #1e293b',
                borderRadius: 8,
                fontSize: 11,
              }}
              labelFormatter={(day) => `sample day ${day}`}
            />
            <Line type="monotone" dataKey="baseline" stroke="#475569" strokeDasharray="4 4" dot={false} />
            <Line type="monotone" dataKey="sample" stroke="#38bdf8" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-2 text-[11px] text-slate-500">
        Sanity shape only — a flat baseline with a late ramp. The real degradation series for the demo comes
        from seeded telemetry in Snowflake.
      </p>
    </section>
  )
}
