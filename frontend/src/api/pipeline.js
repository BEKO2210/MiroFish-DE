import service from './index'

export const STEP_ORDER = ['ontology', 'graph', 'create', 'prepare', 'simulate', 'report']

export const STEP_LABELS = {
  ontology: 'Dokumente lesen',
  graph: 'Wissensgraph aufbauen',
  create: 'Simulation anlegen',
  prepare: 'Agenten vorbereiten',
  simulate: 'Simulation läuft',
  report: 'Bericht schreiben'
}

/**
 * Automatischen Durchlauf starten.
 * @param {File[]} files
 * @param {string} requirement
 * @param {string} [projectName]
 */
export const startPipeline = (files, requirement, projectName) => {
  const fd = new FormData()
  files.forEach(f => fd.append('files', f))
  fd.append('simulation_requirement', requirement)
  if (projectName) fd.append('project_name', projectName)
  return service.post('/api/pipeline/start', fd, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 600000 })
}

export const getPipeline = (pipelineId) => service.get(`/api/pipeline/${pipelineId}`)

export const listPipelines = () => service.get('/api/pipeline/list')
