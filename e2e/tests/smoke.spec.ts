import { test, expect } from '@playwright/test'
import {
  expectMinTouchTargets,
  expectMobileNavDoesNotCoverContent,
  expectNoHorizontalScroll,
  preparePage,
  settle,
} from '../support/helpers'
import { ROUTES, isLiveMode } from '../support/mockApi'

/** Handy: Fußmenü verdeckt Inhalt – bekannter Fehler, siehe BEFUNDE.md */
const MOBILE_NAV_COVER = new Set([
  '/',
  '/run/run_f68e3af5662f',
])

test.describe('Smoke', () => {
  for (const route of ROUTES) {
    test(`${route} lädt sauber`, async ({ page }, testInfo) => {
      const project = testInfo.project.name
      // bekannter Fehler, siehe BEFUNDE.md
      test.fail(
        (project === 'handy' || project === 'iphone') && MOBILE_NAV_COVER.has(route),
        'bekannter Fehler, siehe BEFUNDE.md',
      )

      const { errors } = await preparePage(page)
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await settle(page)

      const serious = errors.filter((e) => !e.text.includes('favicon'))
      expect(serious, `Konsolen-/Seitenfehler auf ${route}: ${JSON.stringify(serious)}`).toEqual([])

      await expectNoHorizontalScroll(page)

      if (project === 'handy' || project === 'iphone') {
        await expectMobileNavDoesNotCoverContent(page)
      }

      await expectMinTouchTargets(page)
    })
  }
})

test.beforeAll(() => {
  if (isLiveMode()) {
    // LIVE_BASE_URL gesetzt: Mocks aus, nur Smoke gegen echte Instanz
  }
})
