import { useRef, type TouchEvent } from 'react'
import { flushSync } from 'react-dom'

const GAP = 16 // px between two sections while they slide: twice the inset in App.css
const SETTLE_MS = 250 // the transition in App.css

/**
 * Phones show one section at a time (App.css). Drag sideways and the section follows your
 * finger, with its neighbour coming in beside it; let go past a quarter of the screen, or
 * flick, to switch. The drag is written straight to CSS variables on `ref`, not React
 * state, so the page doesn't re-render on every finger movement.
 */
export function useSwipePanes<T extends string>(panes: readonly T[], pane: T, setPane: (pane: T) => void) {
  const ref = useRef<HTMLElement>(null)
  const drag = useRef<{ x: number; y: number; t: number; dx: number; sideways?: boolean } | null>(null)
  const settling = useRef(false)

  const width = () => (ref.current?.clientWidth ?? 0) - GAP
  const neighbour = (side: number): T | undefined => panes[panes.indexOf(pane) + side]

  // Shift the current section by dx, with `peek` beside it on `side` (1 = right, -1 = left).
  const place = (dx: number, peek?: T, side = 0) => {
    const el = ref.current
    if (!el) return
    el.style.setProperty('--drag', `${dx}px`)
    el.style.setProperty('--peek-side', String(side))
    if (peek) el.dataset.peek = peek
    else delete el.dataset.peek
  }

  // Slide to dx, then run `done` and put everything back at rest.
  const settle = (dx: number, done?: () => void) => {
    const el = ref.current
    if (!el) return
    settling.current = true
    el.getBoundingClientRect() // lay out a just-shown section first, so it slides instead of jumping
    el.dataset.settling = ''
    el.style.setProperty('--drag', `${dx}px`)
    window.setTimeout(() => {
      if (done) flushSync(done) // the new section is current before the offsets are cleared
      place(0)
      delete el.dataset.settling
      settling.current = false
    }, SETTLE_MS)
  }

  // Switch with the same slide, from the bar at the bottom.
  const go = (target: T) => {
    if (target === pane || settling.current) return
    const side = panes.indexOf(target) > panes.indexOf(pane) ? 1 : -1
    place(0, target, side)
    settle(-side * (width() + GAP), () => setPane(target))
  }

  const onTouchStart = (e: TouchEvent<HTMLElement>) => {
    drag.current = null
    if (settling.current) return
    // Not where a sideways drag already means something: a wide table or row of tabs
    // that scrolls, the 3D viewer (drag to turn the model), a text box.
    for (let el = e.target as HTMLElement | null; el && el !== e.currentTarget; el = el.parentElement) {
      const scrolls = el.scrollWidth > el.clientWidth + 1 && /auto|scroll/.test(getComputedStyle(el).overflowX)
      if (scrolls || el.matches('.model-stage, input, textarea')) return
    }
    drag.current = { x: e.touches[0].clientX, y: e.touches[0].clientY, t: e.timeStamp, dx: 0 }
  }

  const onTouchMove = (e: TouchEvent<HTMLElement>) => {
    const d = drag.current
    if (!d) return
    const dx = e.touches[0].clientX - d.x
    const dy = e.touches[0].clientY - d.y
    if (!d.sideways) {
      if (Math.hypot(dx, dy) < 10) return
      // Mostly up or down is a scroll, and selecting text isn't a swipe either.
      if (Math.abs(dx) < 1.5 * Math.abs(dy) || window.getSelection()?.toString()) {
        drag.current = null
        return
      }
      d.sideways = true
    }
    const side = dx < 0 ? 1 : -1
    const peek = neighbour(side)
    d.dx = peek ? dx : dx / 4 // at either end: give a little, with nothing beside it
    place(d.dx, peek, side)
  }

  const onTouchEnd = (e: TouchEvent<HTMLElement>) => {
    const d = drag.current
    drag.current = null
    if (!d?.sideways) return
    const side = d.dx < 0 ? 1 : -1
    const peek = neighbour(side)
    const flick = Math.abs(d.dx) > 30 && Math.abs(d.dx) / (e.timeStamp - d.t) > 0.5 // px per ms
    if (peek && (Math.abs(d.dx) > width() / 4 || flick)) settle(-side * (width() + GAP), () => setPane(peek))
    else settle(0) // back where it was
  }

  return { ref, go, touch: { onTouchStart, onTouchMove, onTouchEnd, onTouchCancel: onTouchEnd } }
}
