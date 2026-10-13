import { test, expect } from '@playwright/test'
import { preparePage, settle, screenshotMasks, stubWebFonts } from '../support/helpers'
import { ROUTES, isLiveMode } from '../support/mockApi'

test.describe('Visuell', () => {
  test.skip(() => isLiveMode(), 'Snapshots nur im Mock-Modus')

  for (const route of ROUTES) {
    test(`Screenshot ${route}`, async ({ page }, testInfo) => {
      await preparePage(page)
      await stubWebFonts(page)
      // Vor dem Laden: kein Blur/Pulse (WebKit fullPage sonst flaky an Sticky/Nav)
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await settle(page)
      if (route.startsWith('/report/')) {
        await page.waitForSelector('.methodology-card', { timeout: 15000 })
        await page.waitForSelector('.ensemble-list a, .report-action', { timeout: 10000 }).catch(() => {})
        await settle(page)
      }
      if (route.startsWith('/ensemble/')) {
        await page.waitForSelector('.page .title', { timeout: 15000 })
        // Tabelle und Karten beide im DOM — nur die sichtbare Variante abwarten
        await page
          .locator('.results--cards:visible .card__title, .results--table:visible tbody th')
          .filter({ hasText: 'Dominanz' })
          .first()
          .waitFor({ timeout: 15000 })
        await settle(page)
      }

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
    await stubWebFonts(page)
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/process/proj_6fde53d0e82a?view=graph', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.graph-svg circle', { timeout: 15000 })
    // Layout bei reduced-motion synchron; kurz auf Fit-Transform warten
    await settle(page)

    await expect(page).toHaveScreenshot('process_graph_view-handy.png', {
      fullPage: true,
      animations: 'disabled',
      maxDiffPixelRatio: 0.01,
      mask: screenshotMasks(page),
    })
  })
})
