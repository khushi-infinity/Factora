/**
 * Pure presentation helpers for the health payload. Deliberately free of React and
 * of any network access so they can be unit-tested with Vitest (AGENTS verification
 * protocol: frontend logic ships with a test).
 */

import type { DependencyStatus, DependencyStatusValue, HealthPayload } from './api'

export type Tone = 'ok' | 'warn' | 'error' | 'neutral'

const DEPENDENCY_LABELS: Record<DependencyStatusValue, string> = {
  ok: 'healthy',
  degraded: 'degraded',
  not_configured: 'not configured',
  unavailable: 'unavailable',
}

const DEPENDENCY_TONES: Record<DependencyStatusValue, Tone> = {
  ok: 'ok',
  degraded: 'warn',
  not_configured: 'neutral',
  unavailable: 'error',
}

export function describeDependencyStatus(status: DependencyStatusValue): string {
  return DEPENDENCY_LABELS[status] ?? `unknown (${String(status)})`
}

export function dependencyTone(status: DependencyStatusValue): Tone {
  return DEPENDENCY_TONES[status] ?? 'neutral'
}

/** Human-readable uptime: `42s`, `4m 07s`, `2h 13m`. */
export function formatUptime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '—'

  const total = Math.floor(seconds)
  if (total < 60) return `${total}s`

  const minutes = Math.floor(total / 60)
  if (minutes < 60) return `${minutes}m ${String(total % 60).padStart(2, '0')}s`

  const hours = Math.floor(minutes / 60)
  return `${hours}h ${String(minutes % 60).padStart(2, '0')}m`
}

export function findDependency(payload: HealthPayload, name: string): DependencyStatus | undefined {
  return payload.dependencies.find((dependency) => dependency.name === name)
}

export interface HealthSummary {
  label: string
  tone: Tone
  detail: string
}

/**
 * One sentence the operator can act on. Never claims more than the backend reported:
 * "not configured" is shown as exactly that, not as "down".
 */
export function summariseHealth(payload: HealthPayload): HealthSummary {
  const snowflake = findDependency(payload, 'snowflake')

  if (!snowflake) {
    return {
      label: 'Backend reachable',
      tone: 'ok',
      detail: 'The API answered but reported no dependencies yet.',
    }
  }

  const detail = snowflake.detail ?? ''

  switch (snowflake.status) {
    case 'ok':
      return { label: 'Backend and Snowflake reachable', tone: 'ok', detail }
    case 'not_configured':
      return {
        label: 'Backend reachable · Snowflake not configured',
        tone: 'neutral',
        detail: detail || 'Add Snowflake credentials to the repo-root .env once they are issued.',
      }
    case 'degraded':
      return { label: 'Backend reachable · Snowflake degraded', tone: 'warn', detail }
    case 'unavailable':
      return { label: 'Backend reachable · Snowflake unavailable', tone: 'error', detail }
    default:
      return { label: 'Backend reachable', tone: 'neutral', detail }
  }
}
