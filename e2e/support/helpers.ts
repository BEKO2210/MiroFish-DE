import { expect, type Page, type Locator } from '@playwright/test'
import { freezeClock, installMockApi, isLiveMode, type MockApi } from './mockApi'

export type ConsoleBag = { type: string; text: string }

/** Seite vorbereiten: Mocks (außer LIVE), Uhr einfrieren, Konsolenfehler sammeln. */
export async function preparePage(page: Page): Promise<{ api: MockApi | null; errors: ConsoleBag[] }> {
  const errors: ConsoleBag[] = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push({ type: 'console', text: msg.text() })
  })
  page.on('pageerror', (err) => {
    errors.push({ type: 'pageerror', text: err.message })
  })

  let api: MockApi | null = null
  if (!isLiveMode()) {
    api = await installMockApi(page)
  }
  await freezeClock(page)
  return { api, errors }
}

export async function expectNoHorizontalScroll(page: Page) {
  const ok = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)
  expect(ok, 'keine horizontale Scrollleiste').toBe(true)
}

/** Am Handy: letztes interaktives Element darf nicht unter dem Fußmenü liegen. */
export async function expectMobileNavDoesNotCoverContent(page: Page) {
  const nav = page.locator('.mobile-nav')
  if (!(await nav.isVisible())) return

  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  await page.waitForTimeout(200)

  const overlap = await page.evaluate(() => {
    const navEl = document.querySelector('.mobile-nav') as HTMLElement | null
    if (!navEl) return null
    const navTop = navEl.getBoundingClientRect().top
    const selectors = 'a, button, input, textarea, select, [role="button"], [tabindex]:not([tabindex="-1"])'
    const nodes = Array.from(document.querySelectorAll(selectors)) as HTMLElement[]
    let last: HTMLElement | null = null
    let lastBottom = -Infinity
    for (const el of nodes) {
      if (navEl.contains(el)) continue
      const st = getComputedStyle(el)
      if (st.display === 'none' || st.visibility === 'hidden' || Number(st.opacity) === 0) continue
      const r = el.getBoundingClientRect()
      if (r.width < 2 || r.height < 2) continue
      if (r.bottom > lastBottom) {
        lastBottom = r.bottom
        last = el
      }
    }
    if (!last) return { ok: true }
    return {
      ok: lastBottom <= navTop + 1,
      lastTag: last.tagName,
      lastBottom,
      navTop,
      lastText: (last.textContent || '').trim().slice(0, 80),
    }
  })

  if (overlap && overlap.ok === false) {
    expect(
      overlap.ok,
      `Fußmenü verdeckt Element (${overlap.lastTag}: „${overlap.lastText}“, bottom=${overlap.lastBottom}, navTop=${overlap.navTop})`,
    ).toBe(true)
  }
}

const ACTION_BAR = '.mobile-nav, .row__actions, .actions, .sheet__actions, .control-bar'

/** Sichtbare Buttons/Links in Fußmenü und Aktionsleisten ≥ 44×44. */
export async function expectMinTouchTargets(page: Page) {
  const bad = await page.evaluate((rootSel) => {
    const roots = Array.from(document.querySelectorAll(rootSel))
    const out: { text: string; w: number; h: number }[] = []
    for (const root of roots) {
      const st = getComputedStyle(root as Element)
      if (st.display === 'none' || st.visibility === 'hidden') continue
      const controls = (root as Element).querySelectorAll('a, button')
      for (const el of Array.from(controls)) {
        const r = (el as HTMLElement).getBoundingClientRect()
        const cs = getComputedStyle(el)
        if (cs.display === 'none' || cs.visibility === 'hidden') continue
        if (r.width < 1 || r.height < 1) continue
        if (r.width < 44 || r.height < 44) {
          out.push({
            text: ((el as HTMLElement).textContent || '').trim().slice(0, 60),
            w: Math.round(r.width),
            h: Math.round(r.height),
          })
        }
      }
    }
    return out
  }, ACTION_BAR)

  expect(bad, `Touch-Ziele < 44px: ${JSON.stringify(bad)}`).toEqual([])
}

export async function settle(page: Page) {
  await page.waitForLoadState('networkidle').catch(() => {})
  await page.waitForTimeout(400)
}

export function screenshotMasks(page: Page): Locator[] {
  return [
    page.locator('canvas.swarm'),
    page.locator('.live__meta'),
    page.locator('.recent__meta'),
    page.locator('.row__meta'),
    page.locator('.chip__pulse'),
    page.locator('.live__pulse'),
    page.locator('.status-indicator'),
    page.locator('.system-logs'),
    page.locator('time'),
  ]
}
