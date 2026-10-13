import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Page, Request } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const FIXTURES = path.join(__dirname, '../fixtures')

export type ApiCall = {
  method: string
  url: string
  pathname: string
  body: unknown
  postData: string | null
}

export type MockApi = {
  calls: ApiCall[]
  writes: ApiCall[]
  reset: () => void
}

function loadFixture(name: string): unknown | null {
  const file = path.join(FIXTURES, `${name}.json`)
  if (!fs.existsSync(file)) return null
  return JSON.parse(fs.readFileSync(file, 'utf8'))
}

/** /api/foo/bar → foo_bar */
function fixtureNameFromPath(pathname: string): string {
  return pathname.replace(/^\/api\//, '').replace(/\//g, '_')
}

function defaultOk(data: unknown = {}) {
  return { success: true, data }
}

function jsonBody(req: Request): unknown {
  const raw = req.postData()
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return raw
  }
}

function resolveFixture(pathname: string): unknown | null {
  const exact = loadFixture(fixtureNameFromPath(pathname))
  if (exact) return exact

  // Parameterisierte Pfade
  const sim = pathname.match(/^\/api\/simulation\/(sim_[^/]+)(?:\/(.*))?$/)
  if (sim) {
    const [, id, rest] = sim
    if (!rest) return loadFixture(`simulation_${id}`)
    if (rest === 'run-status') return loadFixture(`simulation_${id}_run-status`)
    if (rest === 'run-status/detail') {
      const base = loadFixture(`simulation_${id}_run-status`) as { data?: unknown } | null
      return base ? { success: true, data: { ...(base as { data: object }).data, recent_actions: [] } } : null
    }
    if (rest === 'config' || rest === 'config/realtime') {
      return defaultOk({
        time_config: { total_simulation_hours: 168, minutes_per_round: 60 },
        event_config: {},
        agent_config: {},
      })
    }
    if (rest === 'profiles' || rest === 'profiles/realtime') {
      return defaultOk({ profiles: [], count: 0 })
    }
    if (rest === 'posts' || rest === 'timeline' || rest === 'actions' || rest === 'agent-stats') {
      return defaultOk({ items: [], posts: [], timeline: [], actions: [], agents: [] })
    }
    if (rest === 'export') return null // binary – siehe Handler
  }

  const project = pathname.match(/^\/api\/graph\/project\/([^/]+)$/)
  if (project) return loadFixture(`graph_project_${project[1]}`)

  const report = pathname.match(/^\/api\/report\/([^/]+)(?:\/(.*))?$/)
  if (report) {
    const [, id, rest] = report
    if (!rest) return loadFixture(`report_${id}`)
    if (rest === 'agent-log' || rest === 'console-log') {
      return defaultOk({ lines: [], content: '', from_line: 0, total_lines: 0 })
    }
  }

  const pipeline = pathname.match(/^\/api\/pipeline\/([^/]+)$/)
  if (pipeline && pipeline[1] !== 'list' && pipeline[1] !== 'start') {
    return loadFixture(`pipeline_${pipeline[1]}`)
  }

  const graphData = pathname.match(/^\/api\/graph\/data\/([^/]+)$/)
  if (graphData) {
    return defaultOk({
      graph_id: graphData[1],
      nodes: [
        { id: 'n1', label: 'MiroFish', type: 'Entity' },
        { id: 'n2', label: 'Öffentlichkeit', type: 'Entity' },
      ],
      edges: [{ source: 'n1', target: 'n2', type: 'RELATED' }],
    })
  }

  const task = pathname.match(/^\/api\/graph\/task\/([^/]+)$/)
  if (task) {
    return defaultOk({ task_id: task[1], status: 'completed', progress: 100 })
  }

  return null
}

function writeDefaults(method: string, pathname: string, body: unknown): unknown {
  if (method === 'POST' && pathname === '/api/pipeline/start') {
    return defaultOk({ pipeline_id: 'run_e2e_mock_001', status: 'running' })
  }
  if (method === 'POST' && pathname === '/api/graph/system/config') {
    return defaultOk({ ...(typeof body === 'object' && body ? body : {}), saved: true })
  }
  if (method === 'POST' && pathname === '/api/graph/system/test-llm') {
    return defaultOk({ model: 'gemma4:12b-it-qat-16k', ok: true })
  }
  if (method === 'POST' && pathname === '/api/simulation/prepare') {
    return defaultOk({
      already_prepared: true,
      simulation_id: (body as { simulation_id?: string })?.simulation_id,
    })
  }
  if (method === 'POST' && pathname === '/api/simulation/prepare/status') {
    return defaultOk({ status: 'completed', already_prepared: true, progress: 100 })
  }
  if (method === 'POST' && pathname === '/api/simulation/start') {
    return defaultOk({
      runner_status: 'starting',
      process_pid: 1,
      force_restarted: !!(body as { force?: boolean })?.force,
    })
  }
  if (method === 'POST' && (pathname === '/api/simulation/stop' || pathname === '/api/simulation/close-env')) {
    return defaultOk({ stopped: true })
  }
  if (method === 'POST' && pathname === '/api/simulation/env-status') {
    return defaultOk({ env_alive: false })
  }
  if (method === 'POST' && pathname === '/api/report/generate') {
    return defaultOk({ report_id: 'report_e2e_mock', status: 'pending' })
  }
  if (method === 'POST' && pathname === '/api/report/chat') {
    return defaultOk({ reply: 'Mock-Antwort', message: 'Mock-Antwort' })
  }
  if (method === 'POST' && pathname === '/api/simulation/interview/batch') {
    return defaultOk({ results: [] })
  }
  if (method === 'DELETE' && pathname.startsWith('/api/simulation/')) {
    return defaultOk({ deleted: true })
  }
  if (method === 'DELETE' && pathname.match(/^\/api\/pipeline\/[^/]+$/)) {
    return defaultOk({ deleted: true })
  }
  return defaultOk({})
}

/**
 * Leitet alle /api/*-Aufrufe auf Fixtures/Defaults um und protokolliert Schreibaufrufe.
 */
const FAILED_NOSIM_PIPELINE = {
  completed_at: null,
  created_at: '2026-10-12T08:15:00.000000',
  current_step: 'ontology',
  error: 'aborted before simulation',
  pipeline_id: 'run_failed_nosim_e2e',
  report_id: null,
  requirement: 'E2E Abbruch ohne Simulation',
  simulation_id: null,
  status: 'failed',
}

export async function installMockApi(page: Page): Promise<MockApi> {
  const calls: ApiCall[] = []
  const deletedPipelines = new Set<string>()
  const api: MockApi = {
    calls,
    get writes() {
      return calls.filter((c) => c.method !== 'GET' && c.method !== 'HEAD' && c.method !== 'OPTIONS')
    },
    reset() {
      calls.length = 0
    },
  }

  await page.route('**/api/**', async (route) => {
    const req = route.request()
    const url = new URL(req.url())
    const pathname = url.pathname
    const method = req.method().toUpperCase()
    const body = jsonBody(req)
    const entry: ApiCall = {
      method,
      url: req.url(),
      pathname,
      body,
      postData: req.postData(),
    }
    calls.push(entry)

    // Export / Download: leerer ZIP / Text
    if (pathname.endsWith('/export') || pathname.endsWith('/download')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/zip',
        body: Buffer.from('PK\u0003\u0004mock'),
      })
      return
    }

    if (method === 'GET' || method === 'HEAD') {
      // Verlauf: abgebrochener Durchlauf ohne simulation_id (für Löschen-via-Pipeline)
      if (pathname === '/api/pipeline/list') {
        const base = (loadFixture('pipeline_list') as { success?: boolean; data?: unknown[] } | null) || defaultOk([])
        const data = Array.isArray((base as { data?: unknown[] }).data)
          ? [...((base as { data: unknown[] }).data)]
          : []
        if (!data.some((p) => (p as { pipeline_id?: string }).pipeline_id === FAILED_NOSIM_PIPELINE.pipeline_id)) {
          data.push(FAILED_NOSIM_PIPELINE)
        }
        const filtered = data.filter(
          (p) => !deletedPipelines.has((p as { pipeline_id?: string }).pipeline_id || ''),
        )
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: filtered }),
        })
        return
      }

      const fixture = resolveFixture(pathname)
      if (fixture) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(fixture),
        })
        return
      }
      // Bekannte Listen-Endpunkte ohne Datei
      if (pathname === '/api/simulation/list') {
        const hist = loadFixture('simulation_history')
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(hist || defaultOk([])),
        })
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(defaultOk({})),
      })
      return
    }

    if (method === 'DELETE' && pathname.match(/^\/api\/pipeline\/[^/]+$/)) {
      const id = pathname.split('/').pop()
      if (id) deletedPipelines.add(id)
    }

    const response = writeDefaults(method, pathname, body)
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response),
    })
  })

  return api
}

export const ROUTES = [
  '/',
  '/history',
  '/settings',
  '/run/run_f68e3af5662f',
  '/process/proj_6fde53d0e82a',
  '/simulation/sim_2c3b36b2e33f',
  '/simulation/sim_2c3b36b2e33f/start',
  '/report/report_6587bcd7e3fa',
  '/interaction/report_6587bcd7e3fa',
] as const

export const FIXED_NOW = '2026-10-13T12:00:00+02:00'

export async function freezeClock(page: Page) {
  // Playwright Clock API (1.45+)
  await page.clock.install({ time: new Date(FIXED_NOW) })
}

export function isLiveMode() {
  return !!process.env.LIVE_BASE_URL
}
