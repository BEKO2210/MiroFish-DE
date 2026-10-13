import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { preparePage, settle } from '../support/helpers'
import { isLiveMode } from '../support/mockApi'

const A11Y_ROUTES = ['/', '/history', '/settings', '/report/report_6587bcd7e3fa'] as const

/** Routes mit bekannten serious/critical – siehe BEFUNDE.md */
const KNOWN_A11Y_FAIL = new Set([
  'handy:/',
  'handy:/history',
  'handy:/settings',
  'tablet:/',
  'tablet:/history',
  'tablet:/settings',
  'desktop:/',
  'desktop:/history',
  'desktop:/settings',
  'desktop:/report/report_6587bcd7e3fa',
  // iphone analog zu handy, falls WebKit aktiv
  'iphone:/',
  'iphone:/history',
  'iphone:/settings',
])

test.describe('Barrierefreiheit (axe)', () => {
  test.skip(() => isLiveMode(), 'a11y im Mock-Modus gegen stabile Fixtures')

  for (const route of A11Y_ROUTES) {
    test(`keine serious/critical auf ${route}`, async ({ page }, testInfo) => {
      const key = `${testInfo.project.name}:${route}`
      // bekannter Fehler, siehe BEFUNDE.md
      test.fail(KNOWN_A11Y_FAIL.has(key), 'bekannter Fehler, siehe BEFUNDE.md')

      await preparePage(page)
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await settle(page)

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
        .analyze()

      const bad = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
      expect(
        bad.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length })),
        JSON.stringify(
          bad.map((v) => ({ id: v.id, impact: v.impact, help: v.help })),
          null,
          2,
        ),
      ).toEqual([])
    })
  }
})
