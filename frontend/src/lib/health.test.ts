import { describe, expect, it } from 'vitest'

import type { DependencyStatus, HealthPayload } from './api'
import {
  dependencyTone,
  describeDependencyStatus,
  findDependency,
  formatUptime,
  summariseHealth,
} from './health'

function dependency(overrides: Partial<DependencyStatus> = {}): DependencyStatus {
  return {
    name: 'snowflake',
    status: 'ok',
    detail: 'connected to FACTORA_DEV.ANALYTICS',
    latency_ms: 42,
    ...overrides,
  }
}

function payload(dependencies: DependencyStatus[] = [dependency()]): HealthPayload {
  return {
    status: 'ok',
    service: 'factora-backend',
    version: '0.1.0',
    environment: 'test',
    demo_mode: 'live',
    primary_machine: 'CNC-03',
    time_utc: '2026-10-02T00:00:00Z',
    uptime_s: 12,
    dependencies,
  }
}

describe('formatUptime', () => {
  it('renders seconds below a minute', () => {
    expect(formatUptime(0)).toBe('0s')
    expect(formatUptime(59)).toBe('59s')
  })

  it('renders minutes and zero-padded seconds below an hour', () => {
    expect(formatUptime(60)).toBe('1m 00s')
    expect(formatUptime(247)).toBe('4m 07s')
  })

  it('renders hours and zero-padded minutes above an hour', () => {
    expect(formatUptime(3600)).toBe('1h 00m')
    expect(formatUptime(8040)).toBe('2h 14m')
  })

  it('refuses to invent a value for invalid input', () => {
    expect(formatUptime(-1)).toBe('—')
    expect(formatUptime(Number.NaN)).toBe('—')
    expect(formatUptime(Number.POSITIVE_INFINITY)).toBe('—')
  })
})

describe('dependency status mapping', () => {
  it('labels every known status', () => {
    expect(describeDependencyStatus('ok')).toBe('healthy')
    expect(describeDependencyStatus('not_configured')).toBe('not configured')
    expect(describeDependencyStatus('unavailable')).toBe('unavailable')
  })

  it('maps statuses to a visual tone', () => {
    expect(dependencyTone('ok')).toBe('ok')
    expect(dependencyTone('degraded')).toBe('warn')
    expect(dependencyTone('not_configured')).toBe('neutral')
    expect(dependencyTone('unavailable')).toBe('error')
  })
})

describe('findDependency', () => {
  it('finds by name and reports absence honestly', () => {
    expect(findDependency(payload(), 'snowflake')?.status).toBe('ok')
    expect(findDependency(payload(), 'warehouse')).toBeUndefined()
  })
})

describe('summariseHealth', () => {
  it('reports a healthy Snowflake dependency', () => {
    const summary = summariseHealth(payload())
    expect(summary.tone).toBe('ok')
    expect(summary.label).toContain('Snowflake reachable')
  })

  it('reports missing credentials as "not configured", never as a failure', () => {
    const summary = summariseHealth(
      payload([dependency({ status: 'not_configured', detail: null, latency_ms: null })]),
    )
    expect(summary.tone).toBe('neutral')
    expect(summary.label).toContain('not configured')
    expect(summary.detail).toContain('.env')
  })

  it('reports an unreachable Snowflake as an error, with the backend detail', () => {
    const summary = summariseHealth(
      payload([dependency({ status: 'unavailable', detail: 'OperationalError: 250001', latency_ms: null })]),
    )
    expect(summary.tone).toBe('error')
    expect(summary.detail).toBe('OperationalError: 250001')
  })

  it('still reports backend reachability when no dependencies were returned', () => {
    const summary = summariseHealth(payload([]))
    expect(summary.label).toBe('Backend reachable')
    expect(summary.tone).toBe('ok')
  })
})
