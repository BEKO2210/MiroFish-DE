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
})
