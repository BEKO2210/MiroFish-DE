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
    await page.waitForSelector('.methodology-card, .report-actions', { timeout: 15000 })
    await page.getByRole('button', { name: /Mehrfachlauf starten/i }).first().click()
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
})
