import React from 'react'

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.8em]">
          {part.slice(1, -1)}
        </code>
      )
    }
    return <React.Fragment key={i}>{part}</React.Fragment>
  })
}

export function MarkdownText({ text }: { text: string }) {
  const blocks = text.split(/\n\n+/)

  return (
    <div className="space-y-2">
      {blocks.map((block, bi) => {
        const lines = block.split('\n').filter((l) => l.trim() !== '')
        if (!lines.length) return null

        const isNumbered = lines.length > 1 && lines.every((l) => /^\d+\./.test(l.trim()))
        const isBullet = lines.length > 1 && lines.every((l) => /^[-*] /.test(l.trim()))

        if (isNumbered) {
          return (
            <ol key={bi} className="list-decimal list-outside ml-5 space-y-1">
              {lines.map((l, i) => (
                <li key={i} className="text-sm pl-0.5">
                  {renderInline(l.replace(/^\d+\.\s*/, ''))}
                </li>
              ))}
            </ol>
          )
        }

        if (isBullet) {
          return (
            <ul key={bi} className="list-disc list-outside ml-5 space-y-1">
              {lines.map((l, i) => (
                <li key={i} className="text-sm pl-0.5">
                  {renderInline(l.replace(/^[-*] /, ''))}
                </li>
              ))}
            </ul>
          )
        }

        return (
          <p key={bi} className="text-sm leading-relaxed">
            {lines.map((l, i) => (
              <React.Fragment key={i}>
                {renderInline(l)}
                {i < lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </p>
        )
      })}
    </div>
  )
}
