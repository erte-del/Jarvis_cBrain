// Markdown renderer shared by chat bubbles and canvas cards.
// react-markdown never renders raw HTML, so text from web pages or emails can't inject any.

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function Markdown({ text }: { text: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[[remarkGfm, { singleTilde: false }]]} // "~$5" means "about $5", not strikethrough
      components={{
        a: (props) => <a {...props} target="_blank" rel="noreferrer noopener" />,
      }}
    >
      {text}
    </ReactMarkdown>
  )
}
