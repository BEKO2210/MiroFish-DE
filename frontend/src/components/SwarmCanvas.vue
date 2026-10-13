<template>
  <canvas ref="el" class="swarm" aria-hidden="true"></canvas>
</template>

<script setup>
/**
 * Schwarm-Hintergrund: einige hundert Agenten treiben als Boids über die Fläche, bilden lose Gruppen und
 * weichen dem Finger/Mauszeiger aus. Bei reduced-motion oder ohne Canvas: ruhiges Standbild.
 */
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({ density: { type: Number, default: 1 } })
const el = ref(null)
let raf = 0, ctx, w, h, dpr, agents = [], pointer = { x: -9999, y: -9999 }, running = true, reduced = false

const accent = () => getComputedStyle(document.documentElement).getPropertyValue('--color-brand-primary').trim() || '#E8491D'
const ink = () => getComputedStyle(document.documentElement).getPropertyValue('--color-text-primary').trim() || '#0E1726'

function resize() {
  const c = el.value; if (!c) return
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  w = c.clientWidth; h = c.clientHeight
  c.width = w * dpr; c.height = h * dpr
  ctx = c.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  const n = Math.round(Math.max(90, Math.min(260, (w * h) / 2600)) * props.density)
  while (agents.length < n) agents.push({ x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - .5), vy: (Math.random() - .5), r: 1.2 + Math.random() * 1.8, k: Math.random() })
  agents.length = n
}

function step() {
  const a = accent(), i = ink()
  ctx.clearRect(0, 0, w, h)
  const grid = new Map(); const cell = 48
  for (const p of agents) { const key = ((p.x / cell) | 0) + ',' + ((p.y / cell) | 0); (grid.get(key) || grid.set(key, []).get(key)).push(p) }
  for (const p of agents) {
    let cx = 0, cy = 0, ax = 0, ay = 0, sx = 0, sy = 0, n = 0
    const gx = (p.x / cell) | 0, gy = (p.y / cell) | 0
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) {
      const list = grid.get((gx + dx) + ',' + (gy + dy)); if (!list) continue
      for (const q of list) {
        if (q === p) continue
        const ddx = q.x - p.x, ddy = q.y - p.y, d2 = ddx * ddx + ddy * ddy
        if (d2 > cell * cell) continue
        cx += q.x; cy += q.y; ax += q.vx; ay += q.vy; n++
        if (d2 < 220) { sx -= ddx; sy -= ddy }
      }
    }
    if (n) { p.vx += ((cx / n - p.x) * 0.0015) + ((ax / n - p.vx) * 0.03); p.vy += ((cy / n - p.y) * 0.0015) + ((ay / n - p.vy) * 0.03) }
    p.vx += sx * 0.004; p.vy += sy * 0.004
    // Finger/Zeiger: ausweichen
    const px = p.x - pointer.x, py = p.y - pointer.y, pd = px * px + py * py
    if (pd < 120 * 120) { const f = (1 - Math.sqrt(pd) / 120) * 0.9; p.vx += px / Math.sqrt(pd + 1) * f; p.vy += py / Math.sqrt(pd + 1) * f }
    // leichte Strömung nach rechts, wie ein Schwarm, der zieht
    p.vx += 0.004
    const sp = Math.hypot(p.vx, p.vy), max = 1.1 + p.k * 0.5
    if (sp > max) { p.vx = p.vx / sp * max; p.vy = p.vy / sp * max }
    p.x += p.vx; p.y += p.vy
    if (p.x > w + 10) p.x = -10; if (p.x < -10) p.x = w + 10
    if (p.y > h + 10) p.y = -10; if (p.y < -10) p.y = h + 10
  }
  // zeichnen: Richtung als kleiner Strich, bunte Minderheit als Akzent
  for (const p of agents) {
    const hot = p.k > 0.72
    ctx.strokeStyle = hot ? a : i
    ctx.globalAlpha = hot ? 0.85 : 0.22 + p.k * 0.2
    ctx.lineWidth = p.r
    ctx.lineCap = 'round'
    const sp = Math.hypot(p.vx, p.vy) || 1, L = 4 + p.r * 2
    ctx.beginPath(); ctx.moveTo(p.x - p.vx / sp * L, p.y - p.vy / sp * L); ctx.lineTo(p.x, p.y); ctx.stroke()
  }
  ctx.globalAlpha = 1
  if (running && !reduced) raf = requestAnimationFrame(step)
}

const onMove = (e) => { const r = el.value.getBoundingClientRect(); const t = e.touches ? e.touches[0] : e; pointer.x = t.clientX - r.left; pointer.y = t.clientY - r.top }
const onLeave = () => { pointer.x = -9999; pointer.y = -9999 }
const onVis = () => { running = !document.hidden; if (running && !reduced) { cancelAnimationFrame(raf); raf = requestAnimationFrame(step) } }

onMounted(() => {
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  resize(); step()
  window.addEventListener('resize', resize)
  document.addEventListener('visibilitychange', onVis)
  const c = el.value
  c.addEventListener('pointermove', onMove, { passive: true }); c.addEventListener('pointerleave', onLeave)
  c.addEventListener('touchmove', onMove, { passive: true }); c.addEventListener('touchend', onLeave)
})
onUnmounted(() => { running = false; cancelAnimationFrame(raf); window.removeEventListener('resize', resize); document.removeEventListener('visibilitychange', onVis) })
</script>

<style scoped>
.swarm { position: absolute; inset: 0; width: 100%; height: 100%; display: block; touch-action: pan-y; }
</style>
