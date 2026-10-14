import { test, expect, type Page } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { expectNoHorizontalScroll, preparePage, settle } from '../support/helpers'
import { isLiveMode, type MockApi } from '../support/mockApi'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const sampleMd = path.join(__dirname, '../fixtures/sample-upload.md')

test.describe('Flows', () => {
  test.skip(() => isLiveMode(), 'Flows brauchen API-Mocks')

  test('Startseite: Simulation starten aktiviert nach Datei+Frage und startet Pipeline', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const cta = page.getByRole('button', { name: /Simulation starten/i })
    await expect(cta).toBeDisabled()

    await page.locator('input[type="file"]').setInputFiles(sampleMd)
    await page.locator('textarea.field__input').fill('Wie entwickelt sich die Diskussion über MiroFish?')
    await expect(cta).toBeEnabled()

    await cta.click()
    await expect(page).toHaveURL(/\/run\/run_e2e_mock_001/)

    const startCalls = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/pipeline/start')
    expect(startCalls.length).toBeGreaterThanOrEqual(1)
  })

  test('Verlauf: abgebrochener Durchlauf ohne Simulation – Löschen ruft DELETE /api/pipeline', async ({
    page,
  }) => {
    const { api } = await preparePage(page)
    await page.goto('/history', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const row = page
      .locator('article.row')
      .filter({ hasText: 'E2E Abbruch ohne Simulation' })
      .filter({ has: page.locator('button.act--danger') })
      .first()
    await expect(row).toBeVisible()

    await row.locator('button.act--danger').click()
    const sheet = page.locator('[role="alertdialog"]')
    await expect(sheet).toBeVisible()

    api!.reset()
    await sheet.getByRole('button', { name: 'Löschen' }).click()
    await expect(sheet).toBeHidden()

    const dels = api!.writes.filter(
      (c) => c.method === 'DELETE' && c.pathname === '/api/pipeline/run_failed_nosim_e2e',
    )
    expect(dels.length).toBe(1)
    await expect(
      page.locator('article.row').filter({ hasText: 'E2E Abbruch ohne Simulation' }),
    ).toHaveCount(0)
  })

  test('Verlauf: Löschen – Abbrechen ruft nichts auf, Bestätigen löscht', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/history', { waitUntil: 'domcontentloaded' })
    await settle(page)

    // Eindeutige Zeile (MiroFish) – mehrere Historie-Einträge teilen sich sonst denselben Titel
    const row = page
      .locator('article.row')
      .filter({ hasText: 'MiroFish' })
      .filter({ has: page.locator('button.act--danger') })
      .first()
    await expect(row).toBeVisible()

    await row.locator('button.act--danger').click()
    const sheet = page.locator('[role="alertdialog"]')
    await expect(sheet).toBeVisible()

    api!.reset()
    await sheet.getByRole('button', { name: 'Abbrechen' }).click()
    await expect(sheet).toBeHidden()
    expect(api!.writes.filter((c) => c.method === 'DELETE')).toHaveLength(0)

    await row.locator('button.act--danger').click()
    await expect(sheet).toBeVisible()
    await sheet.getByRole('button', { name: 'Löschen' }).click()
    await expect(sheet).toBeHidden()

    const dels = api!.writes.filter((c) => c.method === 'DELETE' && c.pathname.startsWith('/api/simulation/'))
    expect(dels.length).toBe(1)
    await expect(
      page.locator('article.row').filter({ hasText: 'MiroFish' }).filter({ has: page.locator('button.act--danger') }),
    ).toHaveCount(0)
  })

  test('Datenschutz-Anzeige: lokal und Cloud', async ({ page }) => {
    test.skip(isLiveMode(), 'nur Mock')
    await preparePage(page)
    await page.goto('/settings', { waitUntil: 'domcontentloaded' })
    await settle(page)
    const badge = page.getByTestId('privacy-badge')
    await expect(badge).toHaveAttribute('title', 'Lokal – Texte bleiben auf deinen Geräten')
    await expect(page.getByTestId('privacy-card')).toContainText('Lokal – Texte bleiben auf deinen Geräten')

    const cloud = {
      success: true,
      data: {
        config: { llm_provider: 'openai', llm_base_url: 'https://api.openai.com/v1', llm_api_key: 'sk-geheim' },
        llm_provider: 'openai', llm_base_url: 'https://api.openai.com/v1', llm_model: 'gpt-4o-mini',
        loaded_models: [], memory_provider: 'obsidian', model_installed: true, reachable: true,
      },
    }
    await page.route('**/api/graph/system/status', (r) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(cloud) }))
    await page.goto('/settings', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await expect(badge).toHaveAttribute('title', 'Cloud: OpenAI – Texte werden übertragen')
    await expect(page.getByTestId('privacy-card')).toContainText('Cloud: OpenAI – Texte werden übertragen')
    await expect(page.locator('body')).not.toContainText('sk-geheim')
    await expect(page.locator('body')).not.toContainText('api.openai.com')
    const box = await badge.boundingBox()
    expect(box!.width).toBeGreaterThanOrEqual(44)
    expect(box!.height).toBeGreaterThanOrEqual(44)
  })

  test('Einstellungen: Modelle, Speichern, Sprache', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/settings', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const mainSelect = page
      .locator('select.field__input')
      .filter({ has: page.locator('option', { hasText: 'gemma4:12b-it-qat-16k' }) })
      .first()
    await expect(mainSelect).toBeVisible({ timeout: 10_000 })
    const options = await mainSelect.locator('option').allTextContents()
    expect(options.some((o) => o.includes('gemma4:12b-it-qat-16k'))).toBe(true)
    expect(options.some((o) => o.includes('gemma4:e4b-it-qat'))).toBe(true)

    await mainSelect.selectOption({ value: 'gemma4:e4b-it-qat-16k' })
    api!.reset()
    await page.getByRole('button', { name: /^Speichern$/ }).click()
    await expect(page.getByRole('status')).toContainText(/Gespeichert/i)

    const cfgPosts = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/graph/system/config')
    expect(cfgPosts.length).toBeGreaterThanOrEqual(1)
    const body = cfgPosts[0].body as Record<string, string>
    expect(body.local_llm_model_name === 'gemma4:e4b-it-qat-16k' || body.llm_model_name).toBeTruthy()

    await page.getByRole('radio', { name: 'English' }).click()
    await expect(page.locator('h1.page__title')).toHaveText('Settings')
  })

  test('Simulation-Feed: Escape-Reste und *kursiv* werden sauber gerendert', async ({ page }) => {
    await preparePage(page)
    await page.goto('/simulation/sim_2c3b36b2e33f/start', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const post = page.locator('.content-text.main-text').first()
    await expect(post).toBeVisible({ timeout: 15_000 })
    await expect(post).toContainText('"Gemeinwohls"')
    await expect(post).not.toContainText('\\"')
    await expect(post.locator('em')).toHaveText('ganzheitlich')
    await expect(post.locator('strong')).toHaveText('Fakten')
  })

  async function openMehrfachlaufSheet(page: Page) {
    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.methodology-card, .mobile-sticky-bar, .report-actions', { timeout: 15000 })
    const sticky = page.locator('.mobile-sticky-bar .sticky-btn--secondary')
    if (await sticky.isVisible()) {
      await sticky.click()
    } else {
      await page.getByRole('button', { name: /Mehrfachlauf starten/i }).first().click()
    }
    const sheet = page.locator('[role="alertdialog"]')
    await expect(sheet).toBeVisible()
    return sheet
  }

  function lastEnsembleStartBody(api: MockApi) {
    const posts = api.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/ensemble/start')
    expect(posts.length).toBe(1)
    return posts[0].body as Record<string, unknown>
  }

  test('Mehrfachlauf starten: Optionen → POST → Navigation', async ({ page }) => {
    const { api } = await preparePage(page)
    const sheet = await openMehrfachlaufSheet(page)

    await sheet.getByRole('button', { name: /^10$/ }).click()
    await sheet.locator('input[type="number"]').fill('24')
    await expect(sheet.locator('input[type="checkbox"][disabled]')).toBeChecked()

    api!.reset()
    await sheet.getByRole('button', { name: /^Starten$/i }).click()
    await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)

    const body = lastEnsembleStartBody(api!)
    expect(body.simulation_id).toBe('sim_2c3b36b2e33f')
    expect(body.runs).toBe(10)
    expect(body.hours).toBe(24)
    expect(body.minutes_per_round).toBe(60)
    expect(body.variants).toEqual(expect.arrayContaining(['baseline']))
    expect((body.variants as string[]).length).toBeGreaterThanOrEqual(2)
  })

  test('Mehrfachlauf: Rundentakt und Vergleichsarme → POST', async ({ page }) => {
    const { api } = await preparePage(page)
    const sheet = await openMehrfachlaufSheet(page)

    await sheet.getByRole('button', { name: /2 h je Runde/i }).click()
    await sheet.getByText('Feed ausgeblendet', { exact: true }).click()
    await sheet.getByText('Einzelnes Sprachmodell: mit Rollenprofilen', { exact: true }).click()

    api!.reset()
    await sheet.getByRole('button', { name: /^Starten$/i }).click()
    await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)

    const body = lastEnsembleStartBody(api!)
    expect(body.minutes_per_round).toBe(120)
    expect(body.variants).toEqual(
      expect.arrayContaining(['baseline', 'isolated', 'blind_feed', 'null_document', 'null_personas']),
    )
  })

  test('Fertiges Mehrfachlauf-Ensemble zeigt keine Restzeit', async ({ page }) => {
    await preparePage(page)
    await page.goto('/ensemble/ens_test', { waitUntil: 'domcontentloaded' })
    await settle(page)

    await expect(page.locator('.meta')).toBeVisible()
    await expect(page.getByText(/Noch ca\./)).toHaveCount(0)
  })

  test('Mehrfachlauf erklärt Laufanteile und trennt Mechanismen von Vergleichen', async ({ page }) => {
    await preparePage(page)
    await page.goto('/ensemble/ens_test', { waitUntil: 'domcontentloaded' })
    await settle(page)

    await expect(page.getByRole('heading', { name: 'So sind diese Zahlen zu lesen' })).toBeVisible()
    await expect(page.getByTestId('ensemble-summary')).toBeVisible()
    await expect(page.getByText('7 von 10 Läufen', { exact: false }).first()).toBeVisible()
    await expect(page.getByText(/Rundentakt:\s*60 Min/i)).toBeVisible()
    const arms = page.getByTestId('ensemble-summary').locator('.summary__arms')
    await expect(arms.getByText('Feed ausgeblendet', { exact: true })).toBeVisible()
    await expect(arms.getByText('Einzelnes Sprachmodell: nur Dokumente', { exact: true })).toBeVisible()
    await expect(arms.getByText('Einzelnes Sprachmodell: mit Rollenprofilen', { exact: true })).toBeVisible()

    await page.getByRole('button', { name: /Sicherheitsdebatte zwischen Medien und Politik/i }).click()
    await expect(page.locator('#outcome-o3 .mechanism-blocked__text').first()).toContainText(
      'Diese Variante kann diese Wechselwirkung technisch nicht erzeugen',
    )

    await page.getByRole('button', { name: 'Details für Fachleute' }).click()
    await expect(page.getByText('nicht als Beleg verwenden (explorativ)', { exact: false })).toBeVisible()
    await expect(page.getByText('Vorab festgelegte Hauptfrage (konfirmatorisch)', { exact: true })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Textmengen je Lauf' })).toBeVisible()
    await expect(page.locator('.run-stats--list:visible .run-stats__run, .run-stats--table:visible tbody tr').first()).toBeVisible()
  })

  test('Mehrfachlauf: Zusammenfassung und Aufklappen auf dem Handy', async ({ page }) => {
    await preparePage(page)
    await page.setViewportSize({ width: 412, height: 915 })
    await page.goto('/ensemble/ens_test', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const summary = page.getByTestId('ensemble-summary')
    await expect(summary.getByRole('heading', { name: 'Dominanz-Narrativ' })).toBeVisible()
    await expect(page.getByTestId('ensemble-summary-plain')).toContainText(/kein klarer Unterschied/i)
    await expect(summary.getByText(/7 von 10 Läufen/i).first()).toBeVisible()
    expect(await page.evaluate(() => document.body.scrollHeight)).toBeLessThan(4500)

    const expertBtn = page.getByRole('button', { name: 'Details für Fachleute' })
    await expect(expertBtn).toHaveAttribute('aria-expanded', 'false')
    await expertBtn.click()
    await expect(expertBtn).toHaveAttribute('aria-expanded', 'true')
    await expect(page.getByRole('heading', { name: 'Textmengen je Lauf' })).toBeVisible()
    await expect(page.getByText('Vorab festgelegte Hauptfrage (konfirmatorisch)', { exact: true })).toBeVisible()

    await page.getByRole('button', { name: /^Polarisierung/i }).click()
    await expect(page.locator('#outcome-o2 .stat__text').first()).toContainText(/von \d+ Läufen/i)
    expect((await expertBtn.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44)
  })

  test('eigene Frage hinzufügen und Mehrfachlauf starten', async ({ page }) => {
    const { api } = await preparePage(page)
    const sheet = await openMehrfachlaufSheet(page)

    await sheet.getByRole('button', { name: /Frage hinzufügen/i }).click()
    await sheet.locator('.ens-custom__input').first().fill('Es wird zu einer Unterschriftensammlung aufgerufen')
    await sheet.getByRole('button', { name: /^bleibt aus$/i }).click()

    api!.reset()
    await sheet.getByRole('button', { name: /^Starten$/i }).click()
    await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)

    expect(lastEnsembleStartBody(api!).custom_outcomes).toEqual([
      { text_de: 'Es wird zu einer Unterschriftensammlung aufgerufen', polarity: 'absence' },
    ])
  })

  test('Bericht: Inhaltsverzeichnis öffnen, Sprung, Abschnitt sichtbar', async ({ page }, testInfo) => {
    await preparePage(page)
    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('#report-section-0, .methodology-card', { timeout: 15000 })

    const project = testInfo.project.name
    const methodologyBtn = /Methodik und Grenzen|Methods and limits/i
    const sectionBtn = /Agentenverhalten|Adoptionsgruppen/i
    const sectionTitle = page.locator('#report-section-1 .section-title')
    const methodHeading = page.locator('#methodology-heading')

    if (project === 'desktop') {
      const toc = page.getByTestId('report-toc-desktop')
      await expect(toc).toBeVisible()
      await toc.getByRole('button', { name: sectionBtn }).click()
      await expect(sectionTitle).toBeInViewport({ ratio: 0.5 })
      await toc.getByRole('button', { name: methodologyBtn }).click()
      await expect(methodHeading).toBeInViewport({ ratio: 0.5 })
      await expect(toc.getByRole('button', { name: /Vorgabe-Abgleich|Source check/i })).toBeVisible()
    } else {
      const leading = page.locator('.mobile-sticky-bar .sticky-btn--leading')
      if (await leading.isVisible()) {
        await leading.click()
        const sheet = page.getByTestId('report-toc-sheet')
        await expect(sheet).toBeVisible()
        await sheet.getByRole('button', { name: sectionBtn }).click()
        await expect(sectionTitle).toBeInViewport({ ratio: 0.5 })
        await leading.click()
        await expect(sheet).toBeVisible()
        await sheet.getByRole('button', { name: methodologyBtn }).click()
      } else {
        const mobile = page.getByTestId('report-toc-mobile')
        await expect(mobile).toBeVisible()
        await mobile.evaluate((el: HTMLDetailsElement) => {
          el.open = true
        })
        await mobile.getByRole('button', { name: sectionBtn }).click()
        await expect(sectionTitle).toBeInViewport({ ratio: 0.5 })
        await mobile.evaluate((el: HTMLDetailsElement) => {
          el.open = true
        })
        await mobile.getByRole('button', { name: methodologyBtn }).click()
      }
      await expect(methodHeading).toBeInViewport({ ratio: 0.5 })
    }

    await expect(page.locator('#report-methodology')).toContainText(/Methodik und Grenzen|Methods and limits/i)
    await expectNoHorizontalScroll(page)
  })

  test('Verlässlichkeit: Hinweis im Bericht, Seite und Mehrfachlauf', async ({ page }) => {
    await preparePage(page)
    await page.addInitScript(() => {
      try {
        sessionStorage.clear()
      } catch {
        /* ignore */
      }
    })

    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.methodology-card, [data-testid="reliability-hint"]', { timeout: 15000 })

    const reportHint = page.getByTestId('reliability-hint')
    await expect(reportHint).toBeVisible()
    await expect(reportHint).toContainText(/denkbaren Verlauf/i)
    await expect(page.getByText(/keine neue Erkenntnis/i).first()).toBeVisible()

    await reportHint.getByRole('link', { name: /Wie verlässlich ist das/i }).click()
    await expect(page).toHaveURL(/\/verlaesslichkeit/)
    await settle(page)
    await expect(page.locator('.guide .guide-h1')).toContainText(/verlässlich/i)
    await expect(page.getByText(/keine Vorhersage/i).first()).toBeVisible()
    await expectNoHorizontalScroll(page)

    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('[data-testid="reliability-hint"]', { timeout: 15000 })
    await page.locator('[data-testid="reliability-hint"] .guide-tip__close').click()
    await expect(page.getByTestId('reliability-hint')).toHaveCount(0)

    await page.goto('/ensemble/ens_test', { waitUntil: 'domcontentloaded' })
    await settle(page)
    const ensHint = page.locator('.meaning[data-testid="reliability-hint"]')
    await expect(ensHint).toBeVisible()
    await expect(ensHint).toContainText(/keine Wahrscheinlichkeiten für die Realität/i)
    await expect(ensHint.getByRole('heading', { name: 'So sind diese Zahlen zu lesen' })).toBeVisible()
    await expect(ensHint.getByRole('link', { name: /Wie verlässlich ist das/i })).toBeVisible()
    await expect(page.getByTestId('ensemble-summary').locator('.material-in-hint').first()).toBeVisible()
    await expectNoHorizontalScroll(page)

    await page.goto('/settings', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.getByRole('link', { name: /Wie verlässlich ist MiroFish/i }).click()
    await expect(page).toHaveURL(/\/verlaesslichkeit/)
  })

  for (const vp of [
    { width: 375, height: 560 },
    { width: 1280, height: 600 },
  ]) {
    test(`Mehrfachlauf-Dialog passt in den Viewport ${vp.width}x${vp.height} und bleibt bedienbar`, async ({ page }) => {
      const { api } = await preparePage(page)
      await page.setViewportSize(vp)
      const sheet = await openMehrfachlaufSheet(page)

      // Einblend-Animation (translateY) abwarten, dann Lage prüfen
      await expect
        .poll(async () => {
          const b = await sheet.boundingBox()
          return b ? b.y + b.height : Infinity
        })
        .toBeLessThanOrEqual(vp.height + 0.5)
      const box = await sheet.boundingBox()
      expect(box).not.toBeNull()
      expect(box!.y).toBeGreaterThanOrEqual(-0.5)
      expect(box!.x).toBeGreaterThanOrEqual(-0.5)
      expect(box!.x + box!.width).toBeLessThanOrEqual(vp.width + 0.5)

      await expect(sheet.locator('.sheet__actions')).toBeInViewport({ ratio: 1 })

      const scrollable = await sheet.locator('.sheet__body').evaluate((el) => ({
        scroll: el.scrollHeight,
        client: el.clientHeight,
      }))
      expect(scrollable.scroll).toBeGreaterThan(scrollable.client)

      api!.reset()
      await sheet.getByRole('button', { name: /^Starten$/i }).click()
      await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)
      lastEnsembleStartBody(api!)
    })
  }

  test('Einstellungen: Farbwähler Voll und Reset', async ({ page }) => {

    await preparePage(page)
    await page.goto('/settings', { waitUntil: 'domcontentloaded' })
    await settle(page)

    await page.locator('main .rowbtn').click()
    const dialog = page.locator('[role="dialog"]')
    await expect(dialog).toBeVisible()

    // Eine farbige Vorgabe wählen (Standard ist Weiß – dort bleibt „Voll“ zu Recht weiß), dann „Voll“
    await dialog.locator('.grid .tile').nth(2).click()
    await dialog.getByRole('button', { name: /^Voll$/i }).click()
    await page.waitForTimeout(200)
    const afterFull = await page.evaluate(() => {
      const v = getComputedStyle(document.documentElement).getPropertyValue('--color-bg-canvas').trim()
      return (v || '#FFFFFF').toUpperCase()
    })
    expect(afterFull).not.toBe('#FFFFFF')

    await dialog.getByRole('button', { name: /Originalfarben wiederherstellen/i }).click()
    await page.waitForTimeout(200)
    const afterReset = await page.evaluate(() => {
      const v = getComputedStyle(document.documentElement).getPropertyValue('--color-bg-canvas').trim()
      return (v || '#FFFFFF').toUpperCase()
    })
    expect(afterReset).toBe('#FFFFFF')
  })

  test('Bericht rendert HTML im Abschnitt als Text, nicht als Element', async ({ page }) => {
    await preparePage(page)
    const payload = '<img src=x onerror=alert(1)>'
    const logs = [
      {
        action: 'planning_complete',
        timestamp: '2026-10-13T09:56:30.000000',
        details: {
          outline: {
            title: 'XSS-Prüfung',
            summary: 'Kurz',
            sections: [{ title: 'Abschnitt mit Markup' }],
          },
        },
      },
      {
        action: 'section_complete',
        section_index: 1,
        timestamp: '2026-10-13T09:57:00.000000',
        details: { content: `Vorher **fett** und ${payload} danach.` },
      },
      {
        action: 'report_complete',
        timestamp: '2026-10-13T09:58:00.000000',
      },
    ]
    await page.route('**/api/report/report_xss**', async (route) => {
      const url = new URL(route.request().url())
      const path = url.pathname
      if (path.endsWith('/agent-log')) {
        const from = Number(url.searchParams.get('from_line') || 0)
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            data: { logs: logs.slice(from), from_line: from, total_lines: logs.length },
          }),
        })
        return
      }
      if (path.endsWith('/console-log')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true, data: { logs: [], from_line: 0, total_lines: 0 } }),
        })
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          data: {
            report_id: 'report_xss',
            status: 'completed',
            simulation_id: null,
            error: null,
          },
        }),
      })
    })

    await page.goto('/report/report_xss', { waitUntil: 'domcontentloaded' })
    await settle(page)
    const section = page.locator('.generated-content')
    await expect(section).toBeVisible()
    await expect(section).toContainText(payload)
    await expect(section.locator('strong')).toHaveText('fett')
    await expect(section.locator('img')).toHaveCount(0)
    await expect(page.locator('img[src="x"]')).toHaveCount(0)
    const html = await section.innerHTML()
    expect(html.includes('<img')).toBe(false)
  })

  test('Mehrfachlauf: Zusammenfassung nur bei vollständigen Intervallen', async ({ page }) => {
    await preparePage(page)
    const arm = (variant: string, outcome: string, low: number | null, high: number | null, role?: string) => ({
      variant,
      outcome_id: outcome,
      diff: -0.2,
      ci_low: low,
      ci_high: high,
      unreliable: false,
      ...(role ? { role } : {}),
    })
    const cases: Record<string, Record<string, unknown>> = {
      ens_sum_unclear: {
        comparisons: [
          arm('isolated', 'o1', -0.5, 0.1, 'confirmatory'),
          arm('blind_feed', 'o1', -0.2, 0.3, 'confirmatory'),
          arm('isolated', 'o2', -0.8, -0.2, 'exploratory'),
        ],
      },
      ens_sum_differs: {
        comparisons: [
          arm('isolated', 'o1', -0.7, -0.08, 'confirmatory'),
          arm('blind_feed', 'o1', 0.12, 0.4, 'confirmatory'),
        ],
      },
      ens_sum_mixed: {
        comparisons: [
          arm('isolated', 'o1', -0.5, 0.1, 'confirmatory'),
          arm('blind_feed', 'o1', -0.7, -0.08, 'confirmatory'),
        ],
      },
      ens_sum_incomplete: {
        comparisons: [
          arm('isolated', 'o1', -0.7, -0.1, 'confirmatory'),
          arm('blind_feed', 'o1', -0.4, null, 'confirmatory'),
        ],
      },
      ens_sum_running: {
        status: 'running',
        comparisons: [],
        current: { variant: 'isolated', run: 1, round: 2 },
      },
      ens_sum_fallback: {
        primary_outcome_id: null,
        comparisons: [arm('isolated', 'o1', -0.6, -0.1)],
      },
      ens_sum_norange: {
        results: {
          baseline: { o1: { yes: 7, n: 10, rate: 0.7, ci_low: 0.4, ci_high: 0.89 } },
          isolated: { o1: { yes: 4, n: 10, rate: 0.4 } },
          blind_feed: { o1: { yes: 5, n: 10, rate: 0.5, ci_low: 0.2, ci_high: 0.8 } },
        },
        comparisons: [
          arm('isolated', 'o1', -0.3, 0.2, 'confirmatory'),
          arm('blind_feed', 'o1', -0.1, 0.4, 'confirmatory'),
        ],
      },
    }

    await page.route('**/api/ensemble/ens_sum_*', async (route) => {
      const id = new URL(route.request().url()).pathname.split('/').pop() || ''
      const extra = cases[id]
      if (!extra) {
        await route.fallback()
        return
      }
      const data = {
        ensemble_id: id,
        simulation_id: 'sim_2c3b36b2e33f',
        question: 'Testfrage zur Zusammenfassung',
        status: 'completed',
        runs: 10,
        hours: 24,
        minutes_per_round: 60,
        primary_outcome_id: 'o1',
        variants: [
          { key: 'baseline', label_de: 'Basis', label_en: 'Baseline', status: 'completed', done: 10, total: 10 },
          { key: 'isolated', label_de: 'Ohne Vernetzung', label_en: 'No networking', status: 'completed', done: 10, total: 10 },
          { key: 'blind_feed', label_de: 'Feed ausgeblendet', label_en: 'Blind feed', status: 'completed', done: 10, total: 10 },
        ],
        checklist: [
          { id: 'o1', text_de: 'Hauptfrage', text_en: 'Main question', kind: 'event', source: 'auto' },
          { id: 'o2', text_de: 'Nebenfrage', text_en: 'Side question', kind: 'event', source: 'auto' },
        ],
        results: {
          baseline: { o1: { yes: 7, n: 10, rate: 0.7, ci_low: 0.4, ci_high: 0.89 } },
          isolated: { o1: { yes: 5, n: 10, rate: 0.5, ci_low: 0.24, ci_high: 0.76 } },
          blind_feed: { o1: { yes: 6, n: 10, rate: 0.6, ci_low: 0.31, ci_high: 0.83 } },
        },
        reliability: {},
        current: null,
        eta_seconds: null,
        error: null,
        comparisons: [],
        ...extra,
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ success: true, data }),
      })
    })

    const openCase = async (id: string) => {
      await page.goto(`/ensemble/${id}`, { waitUntil: 'domcontentloaded' })
      await settle(page)
      await expect(page.getByTestId('ensemble-summary')).toBeVisible()
    }
    const plain = () => page.getByTestId('ensemble-summary-plain')

    await openCase('ens_sum_unclear')
    await expect(plain()).toContainText(/kein klarer Unterschied/i)

    await openCase('ens_sum_differs')
    await expect(plain()).toContainText(/unterscheiden sich/i)

    await openCase('ens_sum_mixed')
    await expect(plain()).toContainText(/fallen unterschiedlich aus/i)

    await openCase('ens_sum_incomplete')
    await expect(plain()).toHaveCount(0)

    await openCase('ens_sum_running')
    await expect(plain()).toHaveCount(0)
    await expect(page.getByTestId('ensemble-summary')).not.toContainText(/kein klarer Unterschied/i)

    await openCase('ens_sum_fallback')
    await expect(plain()).toContainText(/unterscheiden sich/i)

    await openCase('ens_sum_norange')
    const summary = page.getByTestId('ensemble-summary')
    await expect(summary.getByText('Spanne —')).toBeVisible()
    await expect(summary.getByText(/0–0\s*%/)).toHaveCount(0)
    await summary.getByRole('button', { name: /Einzelheiten zur Hauptfrage/i }).click()
    await expect(summary.locator('.stat__text').filter({ hasText: 'Schwankung: —' })).toBeVisible()
    await expect(summary.locator('.stat__text').filter({ hasText: /0–0\s*%/ })).toHaveCount(0)

    await page.addInitScript(() => localStorage.setItem('lang', 'en'))
    await page.goto('/ensemble/ens_sum_mixed', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await expect(plain()).toContainText(/do not all agree/i)
  })

  test('Inhaltsverzeichnis-Sheet: Fokus, Escape, Rückgabe, ARIA', async ({ page }) => {
    await preparePage(page)
    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('#report-section-0, .methodology-card', { timeout: 15000 })

    const sectionBtn = /Agentenverhalten|Adoptionsgruppen/i
    const desktop = page.getByTestId('report-toc-desktop')
    const mobile = page.getByTestId('report-toc-mobile')
    if (await desktop.isVisible()) {
      await desktop.getByRole('button', { name: sectionBtn }).click()
    } else if (await mobile.isVisible()) {
      await mobile.evaluate((el: HTMLDetailsElement) => {
        el.open = true
      })
      await mobile.getByRole('button', { name: sectionBtn }).click()
    }
    await expect(page.locator('.toc-link[aria-current="location"]').first()).toBeAttached()

    const leading = page.locator('.mobile-sticky-bar .sticky-btn--leading')
    if (!(await leading.isVisible())) return

    await expect(leading).toHaveAttribute('aria-haspopup', 'dialog')
    await expect(leading).toHaveAttribute('aria-expanded', 'false')
    await leading.click()

    const sheet = page.getByTestId('report-toc-sheet')
    await expect(sheet).toBeVisible()
    await expect(leading).toHaveAttribute('aria-expanded', 'true')
    await expect(sheet.getByRole('dialog')).toBeVisible()
    await expect
      .poll(() =>
        page.evaluate(() => {
          const root = document.querySelector('[data-testid="report-toc-sheet"]')
          return !!root && root.contains(document.activeElement)
        }),
      )
      .toBe(true)
    await expect(sheet.locator('.toc-link[aria-current="location"]')).not.toHaveCount(0)

    await page.keyboard.press('Escape')
    await expect(sheet).toHaveCount(0)
    await expect(leading).toBeFocused()
    await expect(leading).toHaveAttribute('aria-expanded', 'false')
  })

  test('RunView: Lebenszeichen bei laufendem Schritt', async ({ page }) => {
    await preparePage(page)
    await page.goto('/run/run_e2e_mock_001', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const activity = page.getByTestId('step-activity')
    await expect(activity).toBeVisible()
    await expect(page.getByTestId('step-activity-pulse')).toBeVisible()
    await expect(page.getByTestId('step-activity-updated')).toContainText(/Zuletzt aktualisiert vor \d+ s/)
    await expect(activity).toContainText(/Agenten vorbereiten|Persönlichkeit/)
    await expect(page.getByTestId('step-activity-stale')).toHaveCount(0)
  })

  test('RunView: Hinweis „dauert länger“ bei veraltetem Zeitstempel', async ({ page }) => {
    await preparePage(page)
    await page.goto('/run/run_e2e_stale', { waitUntil: 'domcontentloaded' })
    await settle(page)

    await expect(page.getByTestId('step-activity')).toBeVisible()
    await expect(page.getByTestId('step-activity-stale')).toContainText(/Das dauert gerade länger/)
    await expect(page.getByTestId('step-activity-updated')).toContainText(/Zuletzt aktualisiert vor \d+ s/)
  })
})
