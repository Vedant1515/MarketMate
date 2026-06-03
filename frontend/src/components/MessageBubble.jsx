import React from 'react'
import OrderCard from './OrderCard'

function TypingIndicator() {
  return (
    <span className="inline-flex items-center gap-0.5 ml-1 align-middle">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="w-1.5 h-1.5 rounded-full bg-text-secondary animate-bounce inline-block"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  )
}

function renderInlineMarkdown(text) {
  const parts = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Bold: **text**
    const boldMatch = remaining.match(/^([\s\S]*?)\*\*([\s\S]*?)\*\*/)
    // Italic: *text* (single)
    const italicMatch = remaining.match(/^([\s\S]*?)\*([\s\S]*?)\*/)
    // Code: `text`
    const codeMatch = remaining.match(/^([\s\S]*?)`([^`]+)`/)

    const candidates = [
      boldMatch && { type: 'bold', match: boldMatch, before: boldMatch[1], content: boldMatch[2], full: boldMatch[0] },
      italicMatch && { type: 'italic', match: italicMatch, before: italicMatch[1], content: italicMatch[2], full: italicMatch[0] },
      codeMatch && { type: 'code', match: codeMatch, before: codeMatch[1], content: codeMatch[2], full: codeMatch[0] },
    ].filter(Boolean)

    if (candidates.length === 0) {
      parts.push(<span key={key++}>{remaining}</span>)
      break
    }

    // Pick shortest "before" to match earliest
    const earliest = candidates.reduce((a, b) => a.before.length <= b.before.length ? a : b)

    if (earliest.before) {
      parts.push(<span key={key++}>{earliest.before}</span>)
    }

    if (earliest.type === 'bold') {
      parts.push(<strong key={key++} className="font-semibold text-text-primary">{earliest.content}</strong>)
    } else if (earliest.type === 'italic') {
      parts.push(<em key={key++} className="italic text-text-secondary">{earliest.content}</em>)
    } else if (earliest.type === 'code') {
      parts.push(
        <code key={key++} className="font-mono text-accent bg-background px-1 py-0.5 rounded text-sm">
          {earliest.content}
        </code>
      )
    }

    remaining = remaining.slice(earliest.full.length)
  }

  return parts
}

function renderMarkdown(text) {
  const lines = text.split('\n')
  const elements = []
  let i = 0
  let keyCounter = 0

  while (i < lines.length) {
    const line = lines[i]

    // Heading h3: ###
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={keyCounter++} className="text-sm font-bold text-text-primary mt-3 mb-1">
          {renderInlineMarkdown(line.slice(4))}
        </h3>
      )
      i++
      continue
    }

    // Heading h2: ##
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={keyCounter++} className="text-sm font-bold text-text-primary mt-3 mb-1">
          {renderInlineMarkdown(line.slice(3))}
        </h2>
      )
      i++
      continue
    }

    // Heading h1: #
    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={keyCounter++} className="text-base font-bold text-text-primary mt-3 mb-1">
          {renderInlineMarkdown(line.slice(2))}
        </h1>
      )
      i++
      continue
    }

    // Code block: ```
    if (line.startsWith('```')) {
      const codeLines = []
      i++
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i])
        i++
      }
      i++ // skip closing ```
      elements.push(
        <pre key={keyCounter++} className="font-mono text-xs bg-background border border-border rounded-lg p-3 my-2 overflow-x-auto whitespace-pre">
          <code>{codeLines.join('\n')}</code>
        </pre>
      )
      continue
    }

    // Bullet list: - or *
    if (line.match(/^[-*] /)) {
      const listItems = []
      while (i < lines.length && lines[i].match(/^[-*] /)) {
        listItems.push(
          <li key={i} className="flex gap-2">
            <span className="text-accent mt-0.5 flex-shrink-0">-</span>
            <span>{renderInlineMarkdown(lines[i].slice(2))}</span>
          </li>
        )
        i++
      }
      elements.push(
        <ul key={keyCounter++} className="space-y-0.5 my-1.5 text-sm">
          {listItems}
        </ul>
      )
      continue
    }

    // Numbered list: 1.
    if (line.match(/^\d+\. /)) {
      const listItems = []
      while (i < lines.length && lines[i].match(/^\d+\. /)) {
        const numMatch = lines[i].match(/^(\d+)\. (.*)/)
        if (numMatch) {
          listItems.push(
            <li key={i} className="flex gap-2">
              <span className="text-accent font-mono mt-0.5 flex-shrink-0">{numMatch[1]}.</span>
              <span>{renderInlineMarkdown(numMatch[2])}</span>
            </li>
          )
        }
        i++
      }
      elements.push(
        <ol key={keyCounter++} className="space-y-1 my-1.5 text-sm">
          {listItems}
        </ol>
      )
      continue
    }

    // Empty line = paragraph break
    if (line.trim() === '') {
      elements.push(<div key={keyCounter++} className="h-2" />)
      i++
      continue
    }

    // Paragraph
    elements.push(
      <p key={keyCounter++} className="text-sm leading-relaxed">
        {renderInlineMarkdown(line)}
      </p>
    )
    i++
  }

  return elements
}

export default function MessageBubble({ message, order }) {
  const isUser = message.role === 'user'

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[80%] px-4 py-2.5 rounded-2xl rounded-tr-sm bg-accent text-white text-sm leading-relaxed">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-4">
      <div className="max-w-[90%] w-full">
        <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-surface border border-border text-text-primary">
          {message.content ? (
            <div className="space-y-0.5">
              {renderMarkdown(message.content)}
              {message.isStreaming && <TypingIndicator />}
            </div>
          ) : (
            <TypingIndicator />
          )}
        </div>
        {order && !message.isStreaming && (
          <OrderCard order={order} />
        )}
      </div>
    </div>
  )
}
