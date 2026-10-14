import { ref } from 'vue'

/** Stale when server stamp is older than 2 minutes (client clock). */
export const STALE_AFTER_MS = 120_000

export function isStale(serverUpdatedAt, now = Date.now()) {
  if (!serverUpdatedAt) return false
  const t = new Date(serverUpdatedAt).getTime()
  if (Number.isNaN(t)) return false
  return now - t > STALE_AFTER_MS
}

/**
 * Tracks last successful poll time for “Zuletzt aktualisiert vor X s”.
 * Call notePoll(updatedAt?, fingerprint?) on every successful status fetch.
 * Without updatedAt, fingerprint changes bump the “server change” clock for stale detection.
 */
export function useLiveness() {
  const lastPollAt = ref(0)
  const serverUpdatedAt = ref(null)
  let lastFingerprint = null

  const notePoll = (updatedAt, fingerprint) => {
    lastPollAt.value = Date.now()
    if (updatedAt != null && updatedAt !== '') {
      serverUpdatedAt.value = updatedAt
      return
    }
    if (fingerprint != null && fingerprint !== lastFingerprint) {
      lastFingerprint = fingerprint
      serverUpdatedAt.value = new Date().toISOString()
    }
  }

  return { lastPollAt, serverUpdatedAt, notePoll }
}
