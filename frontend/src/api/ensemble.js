import service from './index'

/** POST /api/ensemble/start */
export const startEnsemble = (data) => {
  return service.post('/api/ensemble/start', data)
}

/** GET /api/ensemble/:id */
export const getEnsemble = (ensembleId) => {
  return service.get(`/api/ensemble/${ensembleId}`)
}

/** GET /api/ensemble/list?simulation_id=… */
export const listEnsembles = (simulationId) => {
  return service.get('/api/ensemble/list', { params: { simulation_id: simulationId } })
}

/** POST /api/ensemble/:id/cancel */
export const cancelEnsemble = (ensembleId) => {
  return service.post(`/api/ensemble/${ensembleId}/cancel`)
}

/** DELETE /api/ensemble/:id */
export const deleteEnsemble = (ensembleId) => {
  return service.delete(`/api/ensemble/${ensembleId}`)
}
