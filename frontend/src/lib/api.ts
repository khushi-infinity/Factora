/**
 * The single HTTP boundary between the SPA and the FastAPI BFF (PROJECT_SPEC.md §3.5).
 *
 * Rules that hold for every function added here:
 *  - no Snowflake credentials, no SQL, no scoring logic — those live in the backend,
 *  - every call is typed, time-boxed and fails with a readable message,
 *  - nothing here fabricates data: an error surfaces as an error.
 */

export type DependencyStatusValue = 'ok' | 'degraded' | 'not_configured' | 'unavailable'

export interface DependencyStatus {
  name: string
  status: DependencyStatusValue
  detail: string | null
  latency_ms: number | null
}

export interface HealthPayload {
  status: 'ok' | 'degraded'
  service: string
  version: string
  environment: string
  demo_mode: string
  primary_machine: string
  time_utc: string
  uptime_s: number
  dependencies: DependencyStatus[]
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status?: number

  constructor(message: string, status?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function getJson<T>(path: string, timeoutMs = 5000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })

    if (!response.ok) {
      throw new ApiError(`Request failed: ${response.status} ${response.statusText}`, response.status)
    }

    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiError) throw error
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError(`Request to ${path} timed out after ${timeoutMs} ms`)
    }
    throw new ApiError(error instanceof Error ? error.message : `Unknown error calling ${path}`)
  } finally {
    clearTimeout(timer)
  }
}

export function fetchHealth(): Promise<HealthPayload> {
  return getJson<HealthPayload>('/api/health')
}
