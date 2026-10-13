import { test, expect } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { preparePage, settle } from '../support/helpers'
import { isLiveMode } from '../support/mockApi'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const sampleMd = path.join(__dirname, '../fixtures/sample-upload.md')

test.describe('Flows', () => {
  test.skip(() => isLiveMode(), 'Flows brauchen API-Mocks')

  test('Startseite: Vorhersage starten aktiviert nach Datei+Frage und startet Pipeline', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/', { waitUntil: 'domcontentloaded' })
    await settle(page)

    const cta = page.getByRole('button', { name: /Vorhersage starten/i })
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

  test('Mehrfachlauf starten: Optionen → POST → Navigation', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.methodology-card, .report-actions', { timeout: 15000 })

    await page.getByRole('button', { name: /Mehrfachlauf starten/i }).first().click()
    const sheet = page.locator('[role="alertdialog"]')
    await expect(sheet).toBeVisible()

    await sheet.getByRole('button', { name: /^10$/ }).click()
    await sheet.locator('input[type="number"]').fill('24')
    await expect(sheet.locator('input[type="checkbox"][disabled]')).toBeChecked()

    api!.reset()
    await sheet.getByRole('button', { name: /^Starten$/i }).click()
    await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)

    const posts = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/ensemble/start')
    expect(posts.length).toBe(1)
    const body = posts[0].body as { simulation_id: string; runs: number; hours: number; variants: string[] }
    expect(body.simulation_id).toBe('sim_2c3b36b2e33f')
    expect(body.runs).toBe(10)
    expect(body.hours).toBe(24)
    expect(body.variants).toContain('baseline')
    expect(body.variants.length).toBeGreaterThanOrEqual(2)
  })

  test('Mehrfachlauf erklärt Laufanteile und trennt Mechanismen von Vergleichen', async ({ page }) => {
    await preparePage(page)
    await page.goto('/ensemble/ens_test', { waitUntil: 'domcontentloaded' })
    await settle(page)

    await expect(page.getByRole('heading', { name: 'So sind diese Zahlen zu lesen' })).toBeVisible()
    await expect(page.getByText('7 von 10 Läufen dieser Simulation', { exact: false }).first()).toBeVisible()
    await expect(page.getByText('explorativ – nicht als Beleg verwenden', { exact: false })).toBeVisible()
    await expect(page.getByText('konfirmatorisch', { exact: true })).toBeVisible()
    await expect(page.locator('.results:visible .mechanism-blocked__text').first()).toContainText('Dieser Arm kann diese Wechselwirkung technisch nicht erzeugen')
  })

  test('eigene Frage hinzufügen und Mehrfachlauf starten', async ({ page }) => {
    const { api } = await preparePage(page)
    await page.goto('/report/report_6587bcd7e3fa', { waitUntil: 'domcontentloaded' })
    await settle(page)
    await page.waitForSelector('.methodology-card, .report-actions', { timeout: 15000 })

    await page.getByRole('button', { name: /Mehrfachlauf starten/i }).first().click()
    const sheet = page.locator('[role="alertdialog"]')
    await expect(sheet).toBeVisible()

    await sheet.getByRole('button', { name: /Frage hinzufügen/i }).click()
    const q = sheet.locator('.ens-custom__input').first()
    await q.fill('Es wird zu einer Unterschriftensammlung aufgerufen')
    await sheet.getByRole('button', { name: /^bleibt aus$/i }).click()

    api!.reset()
    await sheet.getByRole('button', { name: /^Starten$/i }).click()
    await expect(page).toHaveURL(/\/ensemble\/ens_e2e_started/)

    const posts = api!.writes.filter((c) => c.method === 'POST' && c.pathname === '/api/ensemble/start')
    expect(posts.length).toBe(1)
    const body = posts[0].body as {
      custom_outcomes?: { text_de: string; polarity?: string }[]
    }
    expect(body.custom_outcomes).toEqual([
      { text_de: 'Es wird zu einer Unterschriftensammlung aufgerufen', polarity: 'absence' },
    ])
  })

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
