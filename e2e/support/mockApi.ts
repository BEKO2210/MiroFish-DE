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
      const detail = loadFixture(`simulation_${id}_run-status_detail`)
      if (detail) return detail
      const base = loadFixture(`simulation_${id}_run-status`) as { data?: unknown } | null
      return base
        ? {
            success: true,
            data: {
              ...(base as { data: object }).data,
              recent_actions: [],
              all_actions: [
                {
                  id: 'e2e-rich-post-1',
                  timestamp: '2026-10-13T09:50:00.000000',
                  platform: 'twitter',
                  agent_id: 'agent_e2e',
                  agent_name: 'Elternbeirat',
                  action_type: 'CREATE_POST',
                  action_args: {
                    content:
                      'Wir sprechen vom \\"Gemeinwohls\\" und handeln *ganzheitlich* mit **Fakten**.',
                  },
                },
              ],
            },
          }
        : null
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
    // Fixture enthält V1-Feld methodology (Methodik und Grenzen)
    if (!rest) return loadFixture(`report_${id}`)
    if (rest === 'console-log') {
      return defaultOk({ logs: [], lines: [], content: '', from_line: 0, total_lines: 0 })
    }
    if (rest === 'agent-log') {
      // Abgeschlossenen Bericht aus Fixture als Agent-Logs spiegeln (Outline + Abschnitte)
      const fixture = loadFixture(`report_${id}`) as {
        data?: {
          outline?: {
            title?: string
            summary?: string
            sections?: { title: string; content: string }[]
          }
        }
      } | null
      const outline = fixture?.data?.outline
      if (!outline?.sections?.length) {
        return defaultOk({ logs: [], from_line: 0, total_lines: 0 })
      }
      const logs: Record<string, unknown>[] = [
        {
          action: 'planning_complete',
          timestamp: '2026-10-13T09:56:30.000000',
          details: { outline },
        },
      ]
      outline.sections.forEach((section, i) => {
        logs.push({
          action: 'section_complete',
          section_index: i + 1,
          timestamp: `2026-10-13T09:5${7 + i}:00.000000`,
          details: { content: section.content },
        })
      })
      logs.push({
        action: 'report_complete',
        timestamp: '2026-10-13T10:08:39.000000',
      })
      return defaultOk({ logs, from_line: 0, total_lines: logs.length })
    }
  }

  const pipeline = pathname.match(/^\/api\/pipeline\/([^/]+)$/)
  if (pipeline && pipeline[1] !== 'list' && pipeline[1] !== 'start') {
    const id = pipeline[1]
    if (id === 'run_e2e_mock_001') {
      return runningPipelineFixture(id, '2026-10-13T11:59:30+02:00')
    }
    if (id === 'run_e2e_stale') {
      // FIXED_NOW ist 12:00+02 → updated_at vor >2 Min → „dauert länger“
      return runningPipelineFixture(id, '2026-10-13T11:50:00+02:00')
    }
    return loadFixture(`pipeline_${id}`)
  }

  const graphData = pathname.match(/^\/api\/graph\/data\/([^/]+)$/)
  if (graphData) {
    // Format wie Backend/GraphPanel: uuid, name, labels / source_node_uuid, target_node_uuid
    const nodes = [
      { uuid: 'n1', name: 'MiroFish', labels: ['Entity', 'TechCompany'] },
      { uuid: 'n2', name: 'Öffentlichkeit', labels: ['Entity', 'Person'] },
      { uuid: 'n3', name: 'TechCrunch', labels: ['Entity', 'MediaOutlet'] },
      { uuid: 'n4', name: 'Ethik-Rat', labels: ['Entity', 'EthicsReviewer'] },
      { uuid: 'n5', name: 'Regulator', labels: ['Entity', 'GovernmentRegulator'] },
      { uuid: 'n6', name: 'Datenlabor', labels: ['Entity', 'ResearchInstitute'] },
      { uuid: 'n7', name: 'Influencerin', labels: ['Entity', 'TechInfluencer'] },
      { uuid: 'n8', name: 'Entwickler', labels: ['Entity', 'TechDeveloper'] },
      { uuid: 'n9', name: 'Analystin', labels: ['Entity', 'DataScientist'] },
      { uuid: 'n10', name: 'NGO Klarheit', labels: ['Entity', 'Organization'] },
    ]
    const edges = [
      { uuid: 'e1', source_node_uuid: 'n8', target_node_uuid: 'n1', name: 'WORKS_FOR', fact_type: 'WORKS_FOR' },
      { uuid: 'e2', source_node_uuid: 'n9', target_node_uuid: 'n6', name: 'WORKS_FOR', fact_type: 'WORKS_FOR' },
      { uuid: 'e3', source_node_uuid: 'n3', target_node_uuid: 'n1', name: 'REPORTS_ON', fact_type: 'REPORTS_ON' },
      { uuid: 'e4', source_node_uuid: 'n7', target_node_uuid: 'n8', name: 'COMMENTS_ON', fact_type: 'COMMENTS_ON' },
      { uuid: 'e5', source_node_uuid: 'n5', target_node_uuid: 'n1', name: 'REGULATES', fact_type: 'REGULATES' },
      { uuid: 'e6', source_node_uuid: 'n7', target_node_uuid: 'n1', name: 'SUPPORTS', fact_type: 'SUPPORTS' },
      { uuid: 'e7', source_node_uuid: 'n4', target_node_uuid: 'n1', name: 'OPPOSES', fact_type: 'OPPOSES' },
      { uuid: 'e8', source_node_uuid: 'n2', target_node_uuid: 'n7', name: 'COMMENTS_ON', fact_type: 'COMMENTS_ON' },
    ]
    return defaultOk({ graph_id: graphData[1], nodes, edges })
  }

  const task = pathname.match(/^\/api\/graph\/task\/([^/]+)$/)
  if (task) {
    return defaultOk({ task_id: task[1], status: 'completed', progress: 100 })
  }

  if (pathname === '/api/ensemble/list') {
    return defaultOk([ensembleListItem(ENSEMBLE_MOCK)])
  }
  const ens = pathname.match(/^\/api\/ensemble\/(ens_[^/]+)$/)
  if (ens) {
    const id = ens[1]
    return defaultOk({
      ...ENSEMBLE_MOCK,
      ensemble_id: id,
      status: id === 'ens_e2e_started' ? 'running' : ENSEMBLE_MOCK.status,
    })
  }

  return null
}

const ENSEMBLE_TEST_ID = 'ens_test'
const ENSEMBLE_ROUND_MINUTES = [60, 120, 240] as const
const ENSEMBLE_MOCK = {
  ensemble_id: ENSEMBLE_TEST_ID,
  simulation_id: 'sim_2c3b36b2e33f',
  question: 'Wie entwickelt sich die öffentliche Diskussion über MiroFish?',
  status: 'completed',
  created_at: '2026-10-13T08:00:00.000000',
  finished_at: '2026-10-13T11:00:00.000000',
  runs: 10,
  hours: 24,
  minutes_per_round: 60,
  primary_outcome_id: 'o1',
  variants: [
    { key: 'baseline', label_de: 'Basis', label_en: 'Baseline', status: 'completed', done: 10, total: 10 },
    { key: 'isolated', label_de: 'Ohne Vernetzung', label_en: 'No networking', status: 'completed', done: 10, total: 10 },
    { key: 'blind_feed', label_de: 'Blinder Feed', label_en: 'Blind feed', status: 'completed', done: 10, total: 10 },
    { key: 'null_document', label_de: 'Nullmodell Dokument', label_en: 'Null model (document)', status: 'completed', done: 10, total: 10 },
    { key: 'null_personas', label_de: 'Nullmodell Personas', label_en: 'Null model (personas)', status: 'completed', done: 10, total: 10 },
  ],
  checklist: [
    { id: 'o1', text_de: 'Dominanz-Narrativ', text_en: 'Dominance narrative', definition: '', kind: 'event', in_material: true, material_snippet: 'technologische Dominanz von MiroFish', source: 'auto' },
    { id: 'o2', text_de: 'Polarisierung', text_en: 'Polarisation', definition: '', kind: 'event', in_material: false, material_snippet: null, source: 'auto' },
    { id: 'o3', text_de: 'Sicherheitsdebatte zwischen Medien und Politik', text_en: 'Safety debate between media and politicians', definition: '', kind: 'interaction', in_material: false, material_snippet: null, source: 'auto' },
    { id: 'o4', text_de: 'Echokammern', text_en: 'Echo chambers', definition: '', in_material: false, material_snippet: null, source: 'auto' },
    { id: 'o5', text_de: 'Regulierungsdruck', text_en: 'Regulatory pressure', definition: '', in_material: false, material_snippet: null, source: 'auto' },
    { id: 'o6', text_de: 'Abhängigkeit', text_en: 'Dependence', definition: '', in_material: false, material_snippet: null, source: 'auto' },
    { id: 'o_user1', text_de: 'Es wird zu einer Unterschriftensammlung aufgerufen', text_en: 'A signature campaign is called for', definition: '', in_material: false, material_snippet: null, source: 'user' },
  ],
  results: {
    baseline: {
      o1: { yes: 7, n: 10, rate: 0.7, ci_low: 0.4, ci_high: 0.89, disputed: 0, evidence: [{ run: 1, platform: 'twitter', post_id: 'p1', agent: 'MediaOutlet', text: 'MiroFish dominiert die Debatte.' }] },
      o2: { yes: 6, n: 10, rate: 0.6, ci_low: 0.31, ci_high: 0.83, disputed: 2, evidence: [] },
      o3: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76, disputed: 0, evidence: [] },
      o4: { yes: 4, n: 10, rate: 0.4, ci_low: 0.17, ci_high: 0.69, disputed: 0, evidence: [] },
      o5: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
      o6: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76, disputed: 0, evidence: [] },
      o_user1: { yes: 4, n: 10, rate: 0.4, ci_low: 0.17, ci_high: 0.69, disputed: 0, evidence: [] },
    },
    isolated: {
      o1: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76, disputed: 0, evidence: [] },
      o2: { yes: 4, n: 10, rate: 0.4, ci_low: 0.17, ci_high: 0.69, disputed: 0, evidence: [] },
      o3: { yes: 4, n: 10, rate: 0.4, ci_low: 0.17, ci_high: 0.69, disputed: 0, evidence: [] },
      o4: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o5: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o6: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
      o_user1: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
    },
    blind_feed: {
      o1: { yes: 6, n: 10, rate: 0.6, ci_low: 0.31, ci_high: 0.83, disputed: 0, evidence: [] },
      o2: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76, disputed: 0, evidence: [] },
      o3: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76, disputed: 0, evidence: [] },
      o4: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
      o5: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
      o6: { yes: 4, n: 10, rate: 0.4, ci_low: 0.17, ci_high: 0.69, disputed: 0, evidence: [] },
      o_user1: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
    },
    null_document: {
      o1: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o2: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o3: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o4: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o5: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o6: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o_user1: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
    },
    null_personas: {
      o1: { yes: 3, n: 10, rate: 0.3, ci_low: 0.11, ci_high: 0.6, disputed: 0, evidence: [] },
      o2: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o3: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o4: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o5: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
      o6: { yes: 2, n: 10, rate: 0.2, ci_low: 0.06, ci_high: 0.51, disputed: 0, evidence: [] },
      o_user1: { yes: 1, n: 10, rate: 0.1, ci_low: 0.02, ci_high: 0.4, disputed: 0, evidence: [] },
    },
  },
  run_stats: {
    baseline: [
      { run: 1, post_count: 42, character_count: 8200, batch_count: 3 },
      { run: 2, post_count: 38, character_count: 7600, batch_count: 3 },
    ],
    isolated: [
      { run: 1, post_count: 30, character_count: 5100, batch_count: 2 },
    ],
    blind_feed: [
      { run: 1, post_count: 40, character_count: 7900, batch_count: 3 },
    ],
    null_document: [
      { run: 1, post_count: 0, character_count: 4500, batch_count: 1 },
    ],
    null_personas: [
      { run: 1, post_count: 0, character_count: 6200, batch_count: 1 },
    ],
  },
  reliability: {
    o1: { agreement: 0.85, kappa: 0.72, n_pairs: 30, label: 'messbar' },
    o2: { agreement: 0.55, kappa: 0.21, n_pairs: 30, label: 'unsicher' },
    o3: { agreement: 0.9, kappa: 0.8, n_pairs: 30, label: 'messbar' },
    o4: { agreement: 0.4, kappa: 0.05, n_pairs: 30, label: 'nicht messbar' },
    o5: { agreement: 0.78, kappa: 0.61, n_pairs: 30, label: 'messbar' },
    o6: { agreement: 0.7, kappa: 0.48, n_pairs: 30, label: 'unsicher' },
    o_user1: { agreement: 0.82, kappa: 0.66, n_pairs: 30, label: 'messbar' },
  },
  comparisons: [
    { variant: 'isolated', outcome_id: 'o1', diff: -0.2, ci_low: -0.5, ci_high: 0.1, unreliable: true, role: 'confirmatory', mcnemar_p: 0.125, holm_p: 0.25 },
    { variant: 'null_document', outcome_id: 'o2', diff: -0.4, ci_low: -0.7, ci_high: -0.08, unreliable: false, role: 'exploratory', mcnemar_p: 0.03125, holm_p: 0.375 },
    { variant: 'isolated', outcome_id: 'o3', diff: -0.1, ci_low: -0.4, ci_high: 0.2, unreliable: false, role: 'exploratory', mcnemar_p: 1, holm_p: 1 },
    { variant: 'null_document', outcome_id: 'o3', diff: -0.4, ci_low: -0.68, ci_high: -0.05, unreliable: false, role: 'exploratory', mcnemar_p: 0.0625, holm_p: 0.75 },
  ],
  current: null,
  eta_seconds: 90,
  error: null,
}

function ensembleListItem(full: typeof ENSEMBLE_MOCK) {
  const { results: _r, ...rest } = full
  // Kurzform ohne results/evidence
  return {
    ...rest,
    checklist: full.checklist.map(({ material_snippet: _s, ...c }) => c),
  }
}

function writeDefaults(method: string, pathname: string, body: unknown): unknown {
  if (method === 'POST' && pathname === '/api/ensemble/start') {
    const b = (body || {}) as {
      runs?: number
      hours?: number
      variants?: string[]
      minutes_per_round?: number
    }
    const minutes = (ENSEMBLE_ROUND_MINUTES as readonly number[]).includes(b.minutes_per_round ?? -1)
      ? (b.minutes_per_round as number)
      : 60
    const rounds = Math.max(1, Math.floor(((b.hours || 24) * 60) / minutes))
    const variantCount = b.variants?.length || 1
    return defaultOk({
      ensemble_id: 'ens_e2e_started',
      estimate_seconds: Math.max(60, rounds * (b.runs || 10) * variantCount * 12),
      minutes_per_round: minutes,
    })
  }
  if (method === 'POST' && pathname.match(/^\/api\/ensemble\/[^/]+\/cancel$/)) {
    return defaultOk({})
  }
  if (method === 'DELETE' && pathname.match(/^\/api\/ensemble\/[^/]+$/)) {
    return defaultOk({})
  }
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

/** Laufender Pipeline-Zustand für Lebenszeichen / Stale-Hinweis (Uhr: FIXED_NOW). */
function runningPipelineFixture(pipelineId: string, updatedAt: string) {
  return defaultOk({
    pipeline_id: pipelineId,
    status: 'running',
    created_at: '2026-10-13T11:30:00+02:00',
    updated_at: updatedAt,
    current_step: 'prepare',
    requirement: 'Wie entwickelt sich die Diskussion über MiroFish?',
    files: ['test_data.txt'],
    project_id: 'proj_e2e_running',
    simulation_id: null,
    report_id: null,
    error: null,
    steps: {
      ontology: {
        label: 'Dokumente lesen',
        status: 'done',
        detail: '10 Entitätstypen',
        progress: 100,
      },
      graph: {
        label: 'Wissensgraph aufbauen',
        status: 'done',
        detail: '12 Knoten',
        progress: 100,
      },
      create: {
        label: 'Simulation anlegen',
        status: 'done',
        detail: 'sim_pending',
        progress: 100,
      },
      prepare: {
        label: 'Agenten vorbereiten',
        status: 'running',
        detail: 'Agent 3 von 12 bekommt eine Persönlichkeit',
        progress: 25,
      },
      simulate: {
        label: 'Simulation läuft',
        status: 'pending',
        detail: '',
        progress: 0,
      },
      report: {
        label: 'Bericht schreiben',
        status: 'pending',
        detail: '',
        progress: 0,
      },
    },
  })
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
        let payload: unknown = fixture
        if (pathname.includes('/agent-log')) {
          const from = Number(url.searchParams.get('from_line') || 0)
          const data = (fixture as { data?: { logs?: unknown[] } }).data
          const all = data?.logs || []
          payload = {
            success: true,
            data: {
              logs: all.slice(from),
              from_line: from,
              total_lines: all.length,
            },
          }
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(payload),
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
  '/ensemble/ens_test',
] as const

export const FIXED_NOW = '2026-10-13T12:00:00+02:00'

export async function freezeClock(page: Page) {
  // Playwright Clock API (1.45+)
  await page.clock.install({ time: new Date(FIXED_NOW) })
}

export function isLiveMode() {
  return !!process.env.LIVE_BASE_URL
}
