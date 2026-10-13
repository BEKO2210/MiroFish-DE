import { test, expect } from '@playwright/test'
import {
  expectMinTouchTargets,
  expectMobileNavDoesNotCoverContent,
  expectNoHorizontalScroll,
  preparePage,
  settle,
} from '../support/helpers'
import { ROUTES, isLiveMode } from '../support/mockApi'

/** Handy: Fußmenü verdeckt Inhalt – bekannter Fehler, siehe BEFUNDE.md (Schrittseiten: anderer Agent) */
const MOBILE_NAV_COVER = new Set([
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

/** Handy: ganze Seite scrollt; kein innerer Haupt-Scroll mit fester Höhe. */
const PAGE_SCROLL_ROUTES = [
  '/report/report_6587bcd7e3fa',
  '/interaction/report_6587bcd7e3fa',
] as const

test.describe('Handy Seiten-Scroll (Report/Interaction)', () => {
  for (const route of PAGE_SCROLL_ROUTES) {
    test(`${route}: Seite scrollt, Inhalt über StickyBar`, async ({ page }, testInfo) => {
      test.skip(testInfo.project.name !== 'handy', 'nur Galaxy-S23-Viewport')

      await preparePage(page)
      await page.goto(route, { waitUntil: 'domcontentloaded' })
      await settle(page)
      await page.waitForSelector('.generated-content, .main-title', { timeout: 10000 })

      const pageScrolls = await page.evaluate(() => {
        const el = document.scrollingElement || document.documentElement
        return el.scrollHeight > window.innerHeight
      })
      expect(pageScrolls, 'document.scrollingElement.scrollHeight > innerHeight').toBe(true)

      const innerFixedScroll = await page.evaluate(() => {
        const main =
          document.querySelector('.report-panel, .interaction-panel, .content-area') ||
          document.querySelector('main')
        if (!main) return { ok: true }
        const chain: HTMLElement[] = []
        let n: HTMLElement | null = main as HTMLElement
        while (n && n !== document.body) {
          chain.push(n)
          n = n.parentElement
        }
        for (const el of chain) {
          const st = getComputedStyle(el)
          const oy = st.overflowY
          if (oy !== 'auto' && oy !== 'scroll') continue
          if (el.clientHeight > 0 && el.scrollHeight > el.clientHeight + 2) {
            return {
              ok: false,
              tag: el.tagName,
              className: String(el.className).slice(0, 80),
              height: st.height,
              clientHeight: el.clientHeight,
              scrollHeight: el.scrollHeight,
            }
          }
        }
        return { ok: true }
      })
      expect(
        innerFixedScroll.ok,
        `kein innerer Overflow-Scroll mit fester Höhe: ${JSON.stringify(innerFixedScroll)}`,
      ).toBe(true)

      await page.evaluate(() => {
        const el = document.scrollingElement || document.documentElement
        el.scrollTop = el.scrollHeight
      })
      await page.waitForTimeout(200)

      const lastParaClear = await page.evaluate(() => {
        const sticky = document.querySelector('.mobile-sticky-bar') as HTMLElement | null
        const composer = document.querySelector('.mobile-chat-composer') as HTMLElement | null
        const stickyTop =
          sticky && getComputedStyle(sticky).display !== 'none'
            ? sticky.getBoundingClientRect().top
            : composer && getComputedStyle(composer).display !== 'none'
              ? composer.getBoundingClientRect().top
              : (document.querySelector('.mobile-nav') as HTMLElement | null)?.getBoundingClientRect()
                  .top ?? window.innerHeight
        // Nur Fließtext im Berichtskörper – keine fixierten Chat-/UI-Zeilen
        const paras = Array.from(
          document.querySelectorAll(
            '.generated-content p, .generated-content .md-p, .report-content-wrapper .sub-title, .sections-list p',
          ),
        ) as HTMLElement[]
        let last: HTMLElement | null = null
        let lastBottom = -Infinity
        for (const p of paras) {
          const st = getComputedStyle(p)
          if (st.display === 'none' || st.visibility === 'hidden') continue
          if (st.position === 'fixed' || st.position === 'sticky') continue
          const r = p.getBoundingClientRect()
          if (r.width < 2 || r.height < 2) continue
          if (r.bottom > lastBottom) {
            lastBottom = r.bottom
            last = p
          }
        }
        if (!last) return { ok: true, reason: 'no-paragraph' }
        return {
          ok: lastBottom <= stickyTop + 1,
          lastBottom,
          stickyTop,
          text: (last.textContent || '').trim().slice(0, 60),
        }
      })
      expect(
        lastParaClear.ok,
        `letzter Absatz oberhalb StickyBar: ${JSON.stringify(lastParaClear)}`,
      ).toBe(true)
    })
  }
})

/** Graph-Ansicht: Zeichenfläche braucht echte Höhe; Knoten dürfen nicht in einem Streifen kleben. */
test.describe('Graph-Ansicht mobil/tablet', () => {
  test('view=graph: Canvas ≥400px, Knoten über >30% der Höhe', async ({ page }, testInfo) => {
    const project = testInfo.project.name
    test.skip(project !== 'handy' && project !== 'tablet', 'nur handy und tablet')

    await preparePage(page)
    await page.goto('/process/proj_6fde53d0e82a?view=graph', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.graph-svg circle', { timeout: 15000 })
    // Force-Layout + Fit-to-View abwarten
    await page.waitForTimeout(800)

    const metrics = await page.evaluate(() => {
      const container = document.querySelector('.graph-container') as HTMLElement | null
      const svg = document.querySelector('.graph-svg') as SVGSVGElement | null
      const canvasH = Math.max(
        container?.clientHeight ?? 0,
        svg?.clientHeight ?? 0,
        Number(svg?.getAttribute('height')) || 0,
      )
      const circles = Array.from(document.querySelectorAll('.graph-svg g.nodes circle')) as SVGCircleElement[]
      // Bildschirmhöhe der Knoten (nach Zoom/Fit), nicht D3-cy
      const tops = circles.map((c) => c.getBoundingClientRect().top)
      const bottoms = circles.map((c) => c.getBoundingClientRect().bottom)
      const spread =
        tops.length && bottoms.length ? Math.max(...bottoms) - Math.min(...tops) : 0
      return {
        canvasH,
        circleCount: circles.length,
        spread,
        spreadRatio: canvasH > 0 ? spread / canvasH : 0,
      }
    })

    expect(metrics.circleCount, `Knoten erwartet: ${JSON.stringify(metrics)}`).toBeGreaterThanOrEqual(8)
    expect(metrics.canvasH, `Canvas-Höhe ≥400: ${JSON.stringify(metrics)}`).toBeGreaterThanOrEqual(400)
    expect(
      metrics.spreadRatio,
      `Knoten-Spread >30% der Canvas-Höhe: ${JSON.stringify(metrics)}`,
    ).toBeGreaterThan(0.3)
  })
})

/** Schritt 5 mobil: volle Breite, Graph-Höhe, eine Composer-Leiste. */
test.describe('Interaction mobil (Schritt 5)', () => {
  test('/interaction: Breite ≥95%, Graph ≥400px, ein Eingabefeld', async ({ page }, testInfo) => {
    const project = testInfo.project.name
    test.skip(project !== 'handy' && project !== 'iphone', 'nur handy und iphone')

    await preparePage(page)
    await page.goto('/interaction/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.main-title, .generated-content', { timeout: 15000 })

    const widthOk = await page.evaluate(() => {
      const main =
        (document.querySelector('.interaction-panel .left-panel, .report-content-wrapper, .interaction-panel') as HTMLElement) ||
        null
      if (!main) return { ok: false, reason: 'no-main' }
      const r = main.getBoundingClientRect()
      const ratio = r.width / window.innerWidth
      return { ok: ratio >= 0.95, ratio, width: r.width, vw: window.innerWidth }
    })
    expect(widthOk.ok, `Hauptinhalt ≥95% Viewportbreite: ${JSON.stringify(widthOk)}`).toBe(true)

    // Graph-Ansicht
    await page.locator('.view-switcher .switch-btn[data-mode="graph"]').click()
    await settle(page)
    await page.waitForSelector('.graph-svg circle', { timeout: 15000 })
    await page.waitForTimeout(900)

    const graphMetrics = await page.evaluate(() => {
      const container = document.querySelector('.graph-container') as HTMLElement | null
      const svg = document.querySelector('.graph-svg') as SVGSVGElement | null
      const canvasH = Math.max(
        container?.clientHeight ?? 0,
        svg?.clientHeight ?? 0,
        Number(svg?.getAttribute('height')) || 0,
      )
      const circles = Array.from(document.querySelectorAll('.graph-svg g.nodes circle')) as SVGCircleElement[]
      const tops = circles.map((c) => c.getBoundingClientRect().top)
      const bottoms = circles.map((c) => c.getBoundingClientRect().bottom)
      const spread =
        tops.length && bottoms.length ? Math.max(...bottoms) - Math.min(...tops) : 0
      const sticky = document.querySelector('.mobile-sticky-bar') as HTMLElement | null
      const stickyVisible = !!(sticky && getComputedStyle(sticky).display !== 'none')
      const composer = document.querySelector('.mobile-chat-composer') as HTMLElement | null
      const composerVisible = !!(composer && getComputedStyle(composer).display !== 'none')
      return {
        canvasH,
        circleCount: circles.length,
        spreadRatio: canvasH > 0 ? spread / canvasH : 0,
        stickyVisible,
        composerVisible,
      }
    })
    expect(graphMetrics.canvasH, `Graph ≥400px: ${JSON.stringify(graphMetrics)}`).toBeGreaterThanOrEqual(400)
    expect(
      graphMetrics.spreadRatio,
      `Knoten >30% Höhe: ${JSON.stringify(graphMetrics)}`,
    ).toBeGreaterThan(0.3)
    expect(graphMetrics.stickyVisible || graphMetrics.composerVisible, 'keine Frage-Leiste in Graph-Ansicht').toBe(
      false,
    )

    // Zurück Arbeitsbereich: genau ein Eingabefeld über Fußmenü
    await page.locator('.view-switcher .switch-btn[data-mode="workbench"]').click()
    await settle(page)

    const inputCheck = await page.evaluate(() => {
      const nav = document.querySelector('.mobile-nav') as HTMLElement | null
      const navTop = nav?.getBoundingClientRect().top ?? window.innerHeight
      const inputs = Array.from(
        document.querySelectorAll('textarea.mobile-chat-composer__input, textarea.chat-input'),
      ) as HTMLTextAreaElement[]
      const visible = inputs.filter((el) => {
        const st = getComputedStyle(el)
        if (st.display === 'none' || st.visibility === 'hidden') return false
        const r = el.getBoundingClientRect()
        return r.width > 2 && r.height > 2
      })
      const aboveNav = visible.filter((el) => el.getBoundingClientRect().bottom <= navTop + 2)
      return { visible: visible.length, aboveNav: aboveNav.length }
    })
    expect(inputCheck.visible, `genau ein Eingabefeld: ${JSON.stringify(inputCheck)}`).toBe(1)
    expect(inputCheck.aboveNav, `Eingabefeld über Fußmenü: ${JSON.stringify(inputCheck)}`).toBe(1)
  })
})

test.beforeAll(() => {
  if (isLiveMode()) {
    // LIVE_BASE_URL gesetzt: Mocks aus, nur Smoke gegen echte Instanz
  }
})
