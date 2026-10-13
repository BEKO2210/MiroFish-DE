import { defineConfig, devices, webkit } from '@playwright/test'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const liveBase = process.env.LIVE_BASE_URL?.replace(/\/$/, '')
const reportPath = path.join(__dirname, 'webkit-status.txt')

/** Binary vorhanden und tatsächlich startbar (Host-Libs)? */
function webkitUsable(): { ok: boolean; detail: string } {
  try {
    const exe = webkit.executablePath()
    if (!exe || !fs.existsSync(exe)) {
      return { ok: false, detail: 'WebKit-Binary fehlt (npx playwright install webkit).' }
    }
  } catch (e) {
    return { ok: false, detail: `WebKit-Binary nicht auflösbar: ${(e as Error).message}` }
  }
  try {
    execFileSync(
      process.execPath,
      [
        '-e',
        `const {webkit}=require('@playwright/test');webkit.launch({timeout:8000}).then(b=>b.close()).then(()=>process.exit(0)).catch(()=>process.exit(1))`,
      ],
      { cwd: __dirname, timeout: 20_000, stdio: 'ignore' },
    )
    return { ok: true, detail: 'WebKit startet – Projekt „iphone“ aktiv.' }
  } catch {
    return {
      ok: false,
      detail:
        'WebKit heruntergeladen, aber nicht startbar (fehlende Host-Bibliotheken). Nur Chromium (handy/tablet/desktop). Tipp: npx playwright install-deps webkit',
    }
  }
}

const webkitStatus = webkitUsable()
const hasWebkit = webkitStatus.ok
fs.writeFileSync(reportPath, `WebKit: ${webkitStatus.detail}\n`, 'utf8')
console.log(`[e2e] ${webkitStatus.detail}`)

const sharedUse = {
  locale: 'de-DE',
  timezoneId: 'Europe/Berlin',
  baseURL: liveBase || 'http://127.0.0.1:4173',
  trace: 'on-first-retry' as const,
}

const ipad = devices['iPad Pro 11']

const projects = [
  {
    name: 'handy',
    use: {
      ...sharedUse,
      browserName: 'chromium' as const,
      viewport: { width: 412, height: 915 },
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: 2.625,
    },
  },
  ...(hasWebkit
    ? [
        {
          name: 'iphone',
          use: {
            ...sharedUse,
            ...devices['iPhone 15'],
            browserName: 'webkit' as const,
            locale: 'de-DE',
            timezoneId: 'Europe/Berlin',
          },
        },
      ]
    : []),
  {
    name: 'tablet',
    use: {
      ...sharedUse,
      browserName: 'chromium' as const,
      viewport: ipad?.viewport ?? { width: 834, height: 1194 },
      isMobile: ipad?.isMobile ?? true,
      hasTouch: ipad?.hasTouch ?? true,
      deviceScaleFactor: ipad?.deviceScaleFactor ?? 2,
      userAgent: ipad?.userAgent,
    },
  },
  {
    name: 'desktop',
    use: {
      ...sharedUse,
      browserName: 'chromium' as const,
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1,
      isMobile: false,
      hasTouch: false,
    },
  },
]

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]],
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: 'disabled',
    },
  },
  projects,
  webServer: liveBase
    ? undefined
    : {
        command: 'npx vite build && npx vite preview --port 4173 --strictPort',
        cwd: path.join(__dirname, '../frontend'),
        url: 'http://127.0.0.1:4173',
        reuseExistingServer: !process.env.CI,
        timeout: 300_000,
      },
})
