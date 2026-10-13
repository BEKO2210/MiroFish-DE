import { test, expect } from '@playwright/test'
import { preparePage, settle, screenshotMasks } from '../support/helpers'
import { ROUTES, isLiveMode } from '../support/mockApi'

test.describe('Visuell', () => {
  test.skip(() => isLiveMode(), 'Snapshots nur im Mock-Modus')

  for (const route of ROUTES) {
    test(`Screenshot ${route}`, async ({ page }, testInfo) => {
      await preparePage(page)
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await settle(page)
      // Animierte Canvas/Pulse abwarten bis disabled
      await page.emulateMedia({ reducedMotion: 'reduce' })

      const name = `${route.replace(/\//g, '_') || 'home'}-${testInfo.project.name}.png`
      await expect(page).toHaveScreenshot(name, {
        fullPage: true,
        animations: 'disabled',
        maxDiffPixelRatio: 0.01,
        mask: screenshotMasks(page),
      })
    })
  }

  test('Screenshot Graph-Ansicht handy', async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== 'handy', 'nur Galaxy-S23-Viewport')
    await preparePage(page)
    await page.goto('/process/proj_6fde53d0e82a?view=graph', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.graph-svg circle', { timeout: 15000 })
    await page.waitForTimeout(800)
    await page.emulateMedia({ reducedMotion: 'reduce' })

    await expect(page).toHaveScreenshot('process_graph_view-handy.png', {
      fullPage: true,
      animations: 'disabled',
      maxDiffPixelRatio: 0.01,
      mask: screenshotMasks(page),
    })
  })
})
