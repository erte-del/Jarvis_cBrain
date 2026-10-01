// The terminal tab: a real shell on this Mac (backend/terminal.py), for you to type in.
// It stays mounted while you switch tabs, so whatever runs in it (Claude Code) keeps going;
// closing the tab or reloading the page ends the shell.

import { FitAddon } from '@xterm/addon-fit'
import { Terminal as XTerm } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { useEffect, useRef } from 'react'
import { API_BASE } from '../ws'

interface TerminalProps {
  visible: boolean
  claude: boolean // type `claude` once the shell is up
}

export default function Terminal({ visible, claude }: TerminalProps) {
  const box = useRef<HTMLDivElement>(null)
  const term = useRef<XTerm | null>(null)
  const startClaude = useRef(claude) // only matters when the shell starts

  useEffect(() => {
    // The HUD colours from index.css (xterm needs real colours, not CSS variables).
    const t = new XTerm({
      cursorBlink: true,
      fontFamily: "'JetBrains Mono', 'SF Mono', ui-monospace, Menlo, monospace",
      fontSize: 13,
      macOptionIsMeta: true,
      theme: { background: '#02080c', foreground: '#cdeef7', cursor: '#22d3ee', selectionBackground: '#13506a' },
    })
    const fit = new FitAddon()
    t.loadAddon(fit)
    t.open(box.current!)
    term.current = t

    const ws = new WebSocket(API_BASE.replace(/^http/, 'ws') + '/ws/terminal')
    ws.binaryType = 'arraybuffer'
    const send = (msg: object) => ws.readyState === WebSocket.OPEN && ws.send(JSON.stringify(msg))
    const resize = () => {
      if (!box.current?.clientWidth) return // hidden behind another tab
      fit.fit()
      send({ type: 'resize', cols: t.cols, rows: t.rows })
    }
    ws.onopen = () => {
      resize()
      if (startClaude.current) send({ type: 'input', data: 'claude\r' })
    }
    ws.onmessage = (e) => t.write(new Uint8Array(e.data as ArrayBuffer))
    ws.onclose = (e) =>
      t.write(e.code === 1008 ? '\r\n[The terminal only works on the Mac itself.]\r\n' : '\r\n[Shell closed]\r\n')
    const typing = t.onData((data) => send({ type: 'input', data }))
    const observer = new ResizeObserver(resize) // also fires when the tab is shown again
    observer.observe(box.current!)

    return () => {
      observer.disconnect()
      typing.dispose()
      ws.close()
      t.dispose()
    }
  }, [])

  useEffect(() => {
    if (visible) term.current?.focus()
  }, [visible])

  return <div className="term-tab" ref={box} hidden={!visible} />
}
