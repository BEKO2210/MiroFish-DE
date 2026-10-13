import { test, expect } from '@playwright/test'
import { preparePage, settle } from '../support/helpers'
import { isLiveMode } from '../support/mockApi'

test.describe('Safety / Datenverlust', () => {
  test.skip(() => isLiveMode(), 'Safety-Regressionen brauchen Mocks')

  test('REGRESSION: abgeschlossene Simulation auf /start löst kein POST /api/simulation/start aus', async ({
    page,
  }) => {
    const { api } = await preparePage(page)
    await page.goto('/simulation/sim_2c3b36b2e33f/start', { waitUntil: 'domcontentloaded' })
    await settle(page)
    // Polling-Fenster abwarten
    await page.waitForTimeout(1500)

    const starts = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/simulation/start')
    expect(starts, `unerwartete start-Aufrufe: ${JSON.stringify(starts)}`).toHaveLength(0)
  })

  test('vorbereitete Simulation: kein prepare mit force_regenerate', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/simulation/sim_2c3b36b2e33f', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForTimeout(1500)

    const prepares = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/simulation/prepare')
    const forced = prepares.filter((c) => {
      const b = c.body as { force_regenerate?: boolean } | null
      return !!b?.force_regenerate
    })
    expect(forced, `prepare mit force_regenerate: ${JSON.stringify(forced)}`).toHaveLength(0)
  })
})
