import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { preparePage, settle } from '../support/helpers'
import { isLiveMode } from '../support/mockApi'

/** Alle Nutzer-Routen inkl. Prozess, Schritte, Bericht, Nachfragen, Mehrfachlauf, Verlässlichkeit */
const A11Y_THEME_ROUTES = [
  '/',
  '/history',
  '/settings',
  '/process/proj_6fde53d0e82a',
  '/simulation/sim_2c3b36b2e33f',
  '/simulation/sim_2c3b36b2e33f/start',
  '/report/report_6587bcd7e3fa',
  '/interaction/report_6587bcd7e3fa',
  '/ensemble/ens_test',
  '/verlaesslichkeit',
] as const

/** Wie ThemePicker/localStorage (`mirofish:theme`) – Standard + helle + kräftige Katalog-Combo */
const COMBO_THEMES = [
  {
    name: 'standard',
    theme: { id: null, a: '#FFFFFF', aName: 'Weiß', b: '#D8401A', bName: 'MiroFish-Orange', mode: 'soft' },
  },
  {
    name: 'hell-508007',
    theme: { id: 508007, a: '#E7F1F6', aName: 'Clear Vision', b: '#0B303F', bName: 'NATO Blue', mode: 'soft' },
  },
  {
    name: 'kraeftig-501771-full',
    theme: { id: 501771, a: '#1B211E', aName: 'Shadow Warrior', b: '#27FBCC', bName: 'Bright Teal', mode: 'full' },
  },
] as const

async function assertNoSeriousCritical(page: import('@playwright/test').Page, label: string) {
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
    .analyze()

  const bad = results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical')
  expect(
    bad.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length })),
    `${label}\n` +
      JSON.stringify(
        bad.map((v) => ({
          id: v.id,
          impact: v.impact,
          help: v.help,
          nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })),
        })),
        null,
        2,
      ),
  ).toEqual([])
}

test.describe('Barrierefreiheit Themes (axe)', () => {
  test.skip(() => isLiveMode(), 'a11y im Mock-Modus gegen stabile Fixtures')

  test.describe('data-theme=dark', () => {
    for (const route of A11Y_THEME_ROUTES) {
      test(`dark: keine serious/critical auf ${route}`, async ({ page, browserName }) => {
        // WebKit/iPhone: CSS-Var am html ok, computed color an Kindern oft Light-Tokens → false fails
        test.skip(browserName === 'webkit', 'data-theme=dark: WebKit color/var paint mismatch')
        await preparePage(page)
        // Transitions aus: sonst axe mittendrin (heller Text auf dunkler Fläche / umgekehrt)
        await page.emulateMedia({ reducedMotion: 'reduce' })
        await page.addInitScript(() => {
          document.documentElement.setAttribute('data-theme', 'dark')
        })
        await page.goto(route, { waitUntil: 'domcontentloaded' })
        await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'))
        await page.waitForFunction(() => {
          const cs = getComputedStyle(document.documentElement)
          return (
            cs.getPropertyValue('--color-bg-canvas').trim().toLowerCase() === '#0b0f17' &&
            cs.getPropertyValue('--color-text-primary').trim().toLowerCase() === '#f8fafc'
          )
        })
        await settle(page)
        await assertNoSeriousCritical(page, `dark ${route}`)
      })
    }
  })

  for (const { name, theme } of COMBO_THEMES) {
    test.describe(`combo ${name}`, () => {
      for (const route of A11Y_THEME_ROUTES) {
        test(`${name}: keine serious/critical auf ${route}`, async ({ page }) => {
          await preparePage(page)
          await page.emulateMedia({ reducedMotion: 'reduce' })
          await page.addInitScript((t) => {
            localStorage.setItem('mirofish:theme', JSON.stringify(t))
          }, theme)
          await page.goto(route, { waitUntil: 'domcontentloaded' })
          await settle(page)
          await assertNoSeriousCritical(page, `combo ${name} ${route}`)
        })
      }
    })
  }
})
