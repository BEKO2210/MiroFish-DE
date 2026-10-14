import { test, expect, type Page } from '@playwright/test'
import { preparePage, settle } from '../support/helpers'
import { isLiveMode, ROUTES } from '../support/mockApi'

/** Extra-Routen + Dialoge, die Smoke-ROUTES nicht abdecken */
const EXTRA = ['/verlaesslichkeit'] as const

const VIEWPORTS = [
  { width: 360, height: 740 },
  { width: 320, height: 640 },
] as const

const THEMES = ['light', 'dark'] as const

type Measure = {
  route: string
  viewport: string
  theme: string
  hScroll: { ok: boolean; scrollWidth: number; innerWidth: number }
  truncatedButtons: { text: string; scrollW: number; clientW: number }[]
  smallTargets: { text: string; w: number; h: number; sel: string }[]
  navCover: { ok: boolean; detail?: string }
}

async function applyTheme(page: Page, theme: 'light' | 'dark') {
  await page.evaluate((t) => {
    document.documentElement.setAttribute('data-theme', t === 'dark' ? 'dark' : 'light')
    if (t === 'light') document.documentElement.removeAttribute('data-theme')
  }, theme)
}

async function measurePage(page: Page, route: string, viewport: string, theme: string): Promise<Measure> {
  const hScroll = await page.evaluate(() => {
    const scrollWidth = document.documentElement.scrollWidth
    const innerWidth = window.innerWidth
    return { ok: scrollWidth <= innerWidth, scrollWidth, innerWidth }
  })

  const truncatedButtons = await page.evaluate(() => {
    const out: { text: string; scrollW: number; clientW: number }[] = []
    const isVisuallyHidden = (el: HTMLElement) => {
      if (el.classList.contains('sr-only')) return true
      const st = getComputedStyle(el)
      if (st.display === 'none' || st.visibility === 'hidden') return true
      if (st.position === 'absolute' && (st.clipPath === 'inset(50%)' || /rect\(0/.test(st.clip))) return true
      const r = el.getBoundingClientRect()
      return r.width < 2 || r.height < 2
    }
    for (const el of Array.from(
      document.querySelectorAll(
        'button, a.sticky-btn, .mobile-sticky-bar button, .mobile-nav a, .sheet__actions button, [role="alertdialog"] button',
      ),
    )) {
      const btn = el as HTMLElement
      if (isVisuallyHidden(btn)) continue
      const st = getComputedStyle(btn)
      // Eltern mit display:none (z. B. Desktop-Kopf am Handy)
      if (btn.offsetParent === null && st.position !== 'fixed') continue
      const labels = Array.from(btn.querySelectorAll('span, .sticky-btn__label')) as HTMLElement[]
      const nodes = labels.filter((n) => !isVisuallyHidden(n))
      const check = nodes.length ? nodes : [btn]
      for (const node of check) {
        // Nur echte Abschneidung (nowrap/ellipsis), nicht umbrochenen Mehrzeilentext
        const ns = getComputedStyle(node)
        const clipped =
          (ns.whiteSpace === 'nowrap' || ns.textOverflow === 'ellipsis') &&
          node.scrollWidth > node.clientWidth + 1
        const overflowPlain =
          ns.whiteSpace !== 'normal' && node.scrollWidth > node.clientWidth + 1
        if (clipped || overflowPlain) {
          out.push({
            text: (node.textContent || '').trim().slice(0, 80),
            scrollW: node.scrollWidth,
            clientW: node.clientWidth,
          })
        }
      }
    }
    return out
  })

  const smallTargets = await page.evaluate(() => {
    const roots = Array.from(
      document.querySelectorAll(
        '.mobile-nav, .mobile-sticky-bar, .row__actions, .actions, .sheet__actions, .control-bar, [role="alertdialog"] .sheet__actions, .step-nav-bar__dots',
      ),
    )
    const out: { text: string; w: number; h: number; sel: string }[] = []
    for (const root of roots) {
      const rst = getComputedStyle(root)
      if (rst.display === 'none' || rst.visibility === 'hidden') continue
      for (const el of Array.from(root.querySelectorAll('a, button'))) {
        const r = (el as HTMLElement).getBoundingClientRect()
        const cs = getComputedStyle(el)
        if (cs.display === 'none' || cs.visibility === 'hidden') continue
        if (r.width < 1 || r.height < 1) continue
        if (r.width < 44 || r.height < 44) {
          out.push({
            text: ((el as HTMLElement).textContent || '').trim().slice(0, 60),
            w: Math.round(r.width),
            h: Math.round(r.height),
            sel: (el as HTMLElement).className?.toString().slice(0, 60) || el.tagName,
          })
        }
      }
    }
    return out
  })

  // Scroll zum Ende, dann prüfen ob Fußmenü Inhalt verdeckt
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  await page.waitForTimeout(150)

  const navCover = await page.evaluate(() => {
    // Modal/Sheet liegt über dem Fußmenü – kein Cover-Check während Dialog offen
    const modal = document.querySelector('[role="alertdialog"], [role="dialog"]') as HTMLElement | null
    if (modal && getComputedStyle(modal).display !== 'none') {
      const sheet = modal.closest('.backdrop, .sheet-backdrop') as HTMLElement | null
      const host = sheet || modal
      if (getComputedStyle(host).display !== 'none') return { ok: true, detail: 'modal-open' }
    }

    const navEl = document.querySelector('.mobile-nav') as HTMLElement | null
    if (!navEl || getComputedStyle(navEl).display === 'none') return { ok: true }
    const navTop = navEl.getBoundingClientRect().top
    const sticky = document.querySelector('.mobile-sticky-bar') as HTMLElement | null
    const stickyVisible = !!(sticky && getComputedStyle(sticky).display !== 'none')
    if (stickyVisible) {
      const sb = sticky!.getBoundingClientRect()
      if (sb.bottom > navTop + 1) {
        return {
          ok: false,
          detail: `stickyBar.bottom=${sb.bottom} > navTop=${navTop}`,
        }
      }
    }
    const selectors =
      'a, button, input, textarea, select, [role="button"], [tabindex]:not([tabindex="-1"])'
    const nodes = Array.from(document.querySelectorAll(selectors)) as HTMLElement[]
    let last: HTMLElement | null = null
    let lastBottom = -Infinity
    for (const el of nodes) {
      if (navEl.contains(el)) continue
      if (sticky && sticky.contains(el)) continue
      if (el.closest('[role="alertdialog"], [role="dialog"], .sheet-backdrop, .backdrop')) continue
      const st = getComputedStyle(el)
      if (st.display === 'none' || st.visibility === 'hidden' || Number(st.opacity) === 0) continue
      if (st.position === 'fixed' || st.position === 'sticky') continue
      const r = el.getBoundingClientRect()
      if (r.width < 2 || r.height < 2) continue
      if (r.bottom > lastBottom) {
        lastBottom = r.bottom
        last = el
      }
    }
    if (!last) return { ok: true }
    const ceiling = stickyVisible ? sticky!.getBoundingClientRect().top : navTop
    if (lastBottom > ceiling + 1) {
      return {
        ok: false,
        detail: `${last.tagName} „${(last.textContent || '').trim().slice(0, 60)}“ bottom=${lastBottom} ceiling=${ceiling}`,
      }
    }
    return { ok: true }
  })

  return { route, viewport, theme, hScroll, truncatedButtons, smallTargets, navCover }
}

async function assertMeasure(m: Measure) {
  expect(m.hScroll.ok, `hScroll ${m.route} ${m.viewport} ${m.theme}: ${JSON.stringify(m.hScroll)}`).toBe(
    true,
  )
  expect(
    m.truncatedButtons,
    `truncatedButtons ${m.route} ${m.viewport} ${m.theme}: ${JSON.stringify(m.truncatedButtons)}`,
  ).toEqual([])
  expect(
    m.smallTargets,
    `smallTargets ${m.route} ${m.viewport} ${m.theme}: ${JSON.stringify(m.smallTargets)}`,
  ).toEqual([])
  expect(m.navCover.ok, `navCover ${m.route} ${m.viewport} ${m.theme}: ${m.navCover.detail}`).toBe(
    true,
  )
}

test.describe('Schmale Handy-Viewports', () => {
  test.skip(() => isLiveMode(), 'Narrow-Messungen brauchen API-Mocks')

  for (const vp of VIEWPORTS) {
    for (const theme of THEMES) {
      test(`Routen ${vp.width}x${vp.height} ${theme}`, async ({ page }, testInfo) => {
        test.skip(testInfo.project.name !== 'handy', 'nur Projekt handy')
        test.setTimeout(180_000)

        await page.setViewportSize({ width: vp.width, height: vp.height })
        const { errors } = await preparePage(page)
        const viewport = `${vp.width}x${vp.height}`
        const routes = [...ROUTES, ...EXTRA]

        for (const route of routes) {
          await page.goto(route, { waitUntil: 'domcontentloaded' })
          await settle(page)
          await applyTheme(page, theme)
          await page.waitForTimeout(100)

          // Bericht: TOC-Leiste mit 3 Knöpfen abwarten
          if (route.startsWith('/report/')) {
            await page.waitForSelector('.methodology-card, .mobile-sticky-bar', { timeout: 15_000 }).catch(() => {})
          }
          if (route.startsWith('/ensemble/')) {
            await page.waitForSelector('[data-testid="ensemble-summary"]', { timeout: 15_000 }).catch(() => {})
          }

          const m = await measurePage(page, route, viewport, theme)
          await assertMeasure(m)
        }

        const serious = errors.filter((e) => !e.text.includes('favicon'))
        expect(serious, `Konsolenfehler: ${JSON.stringify(serious)}`).toEqual([])
      })

      test(`Einstellungen Farb-Combos ${vp.width}x${vp.height} ${theme}`, async ({ page }, testInfo) => {
        test.skip(testInfo.project.name !== 'handy', 'nur Projekt handy')

        await page.setViewportSize({ width: vp.width, height: vp.height })
        await preparePage(page)
        await page.goto('/settings', { waitUntil: 'domcontentloaded' })
        await settle(page)
        await applyTheme(page, theme)

        await page.locator('main .rowbtn').click()
        const dialog = page.locator('[role="dialog"]')
        await expect(dialog).toBeVisible()
        await page.waitForTimeout(200)

        const viewport = `${vp.width}x${vp.height}`
        let m = await measurePage(page, '/settings#theme', viewport, theme)
        await assertMeasure(m)

        // Soft + Full auf einer farbigen Vorgabe
        await dialog.locator('.grid .tile').nth(2).click()
        await page.waitForTimeout(150)
        m = await measurePage(page, '/settings#theme-preset', viewport, theme)
        await assertMeasure(m)

        await dialog.getByRole('button', { name: /^Voll$/i }).click()
        await page.waitForTimeout(150)
        m = await measurePage(page, '/settings#theme-full', viewport, theme)
        await assertMeasure(m)

        await dialog.getByRole('button', { name: /^Dezent$/i }).click()
        await page.waitForTimeout(100)
      })

      test(`Bestätigungsdialoge ${vp.width}x${vp.height} ${theme}`, async ({ page }, testInfo) => {
        test.skip(testInfo.project.name !== 'handy', 'nur Projekt handy')

        await page.setViewportSize({ width: vp.width, height: vp.height })
        await preparePage(page)
        const viewport = `${vp.width}x${vp.height}`

        // Verlauf Löschen
        await page.goto('/history', { waitUntil: 'domcontentloaded' })
        await settle(page)
        await applyTheme(page, theme)
        const row = page.locator('article.row').filter({ has: page.locator('button.act--danger') }).first()
        await row.locator('button.act--danger').click()
        await expect(page.locator('[role="alertdialog"]')).toBeVisible()
        await page.waitForTimeout(200)
        let m = await measurePage(page, '/history#confirm-delete', viewport, theme)
        await assertMeasure(m)
        await page.locator('[role="alertdialog"]').getByRole('button', { name: /Abbrechen/i }).click()

        // Mehrfachlauf-Sheet
        await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
        await settle(page)
        await applyTheme(page, theme)
        await page.waitForSelector('.methodology-card, .report-actions, .mobile-sticky-bar', {
          timeout: 15_000,
        })
        const stickyMehr = page.locator('.mobile-sticky-bar .sticky-btn--secondary')
        if (await stickyMehr.isVisible()) {
          await stickyMehr.click()
        } else {
          await page.getByRole('button', { name: /Mehrfachlauf/i }).first().click()
        }
        await expect(page.locator('[role="alertdialog"]')).toBeVisible()
        await page.waitForTimeout(250)
        m = await measurePage(page, '/report#ensemble-sheet', viewport, theme)
        await assertMeasure(m)
      })
    }
  }
})
