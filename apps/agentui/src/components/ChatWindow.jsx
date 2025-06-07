import React, { useRef, useEffect, useState } from 'react'
import { Button } from './ui/button'
import { Input } from './ui/Input'
import { Card } from './ui/Card'
import ReactMarkdown from 'react-markdown'
import 'katex/dist/katex.min.css'
import { InlineMath, BlockMath } from 'react-katex'
import { useTranslation } from 'react-i18next'
import remarkMath from 'remark-math'
import rehypeKatex from 'rehype-katex'

// Thinking section component
function ThinkingSection({ content, isComplete }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const { t } = useTranslation()

  return (
    <div className="mt-2 border border-muted-foreground/20 rounded-md overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 flex items-center justify-between bg-muted/50 hover:bg-muted/70 transition-colors"
      >
        <span className="text-sm text-muted-foreground flex items-center gap-2">
          <span className="material-icons text-base">psychology</span>
          {isComplete ? 'Thoughts' : t('thinking')}
        </span>
        <span className="material-icons text-base transition-transform" style={{ transform: isExpanded ? 'rotate(180deg)' : 'none' }}>
          expand_more
        </span>
      </button>
      {isExpanded && (
        <div className="px-3 py-2 bg-muted/30 text-sm text-muted-foreground whitespace-pre-wrap">
          {content}
        </div>
      )}
    </div>
  )
}

// Helper function to process text and extract thinking sections
const processThinkingSections = (text) => {
  if (typeof text !== 'string') return text

  // Split by both complete think tags and incomplete ones
  const parts = text.split(/(<think>[\s\S]*?(?:<\/think>|$))/g)
  if (parts.length === 1) return text

  return parts.map((part, index) => {
    if (part.startsWith('<think>')) {
      // If we have a complete think section
      if (part.endsWith('</think>')) {
        const thinkingContent = part.slice(7, -8)
        return <ThinkingSection key={index} content={thinkingContent} isComplete={true} />
      } else {
        // If we have an incomplete think section (still streaming)
        const thinkingContent = part.slice(7)
        return <ThinkingSection key={index} content={thinkingContent} isComplete={false} />
      }
    }
    return part
  }).filter(part => part !== '');
}

// Custom renderer for math expressions
const MathRenderer = ({ value, display }) => {
  try {
    return display ? <BlockMath math={value} /> : <InlineMath math={value} />
  } catch (error) {
    console.error('Error rendering math:', error)
    return <span className="text-red-500">Error rendering math: {value}</span>
  }
}

// Helper function to process text and extract math expressions
const processMathExpressions = (text) => {
  if (typeof text !== 'string') return text

  // Handle block math expressions ($$...$$)
  if (text.startsWith('$$') && text.endsWith('$$')) {
    const math = text.slice(2, -2)
    return <MathRenderer value={math} display={true} />
  }

  // Handle inline math expressions ($...$)
  const parts = text.split(/(\$\$[^$]+\$\$|\$[^$\n]+\$)/g)
  if (parts.length === 1) return text

  return parts.map((part, index) => {
    if (part.startsWith('$$') && part.endsWith('$$')) {
      const math = part.slice(2, -2)
      return <MathRenderer key={index} value={math} display={true} />
    }
    if (part.startsWith('$') && part.endsWith('$')) {
      const math = part.slice(1, -1)
      return <MathRenderer key={index} value={math} display={false} />
    }
    return part
  })
}

// Custom components for ReactMarkdown
const components = {
  // Handle inline math expressions in code blocks
  code: ({ node, inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '')
    if (inline && match?.[1] === 'math') {
      return <MathRenderer value={String(children)} display={false} />
    }
    
    if (inline) {
      return (
        <code 
          className="bg-muted/50 px-1.5 py-0.5 rounded font-mono text-sm"
          {...props}
        >
          {children}
        </code>
      )
    }

    // For block code
    const language = match ? match[1] : ''
    return (
      <div className="my-4">
        {language && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-muted/70 text-xs text-muted-foreground rounded-t-md border border-muted-foreground/20 border-b-0">
            <span className="material-icons text-sm">code</span>
            <span className="font-medium">{language}</span>
          </div>
        )}
        <div className="relative">
          <code 
            className={`block bg-muted/50 p-4 rounded-md font-mono text-sm overflow-x-auto ${language ? 'rounded-t-none' : ''}`}
            {...props}
          >
            {children}
          </code>
        </div>
      </div>
    )
  },
  // Handle block and inline math expressions in paragraphs
  p: ({ children }) => {
    if (typeof children === 'string') {
      return <p className="prose prose-sm max-w-none">{processMathExpressions(children)}</p>
    }
    if (Array.isArray(children)) {
      return <p className="prose prose-sm max-w-none">{children.map((child, index) => 
        typeof child === 'string' ? processMathExpressions(child) : child
      )}</p>
    }
    return <p className="prose prose-sm max-w-none">{children}</p>
  },
  // Handle math in other text elements
  span: ({ children }) => {
    if (typeof children === 'string') {
      return <span className="prose prose-sm max-w-none">{processMathExpressions(children)}</span>
    }
    return <span className="prose prose-sm max-w-none">{children}</span>
  }
}

export default function ChatWindow({
  messages = [],
  input,
  onInputChange,
  onSend,
  isLoading,
  streamingMessage = '',
  username = 'You',
  modelName = 'Assistant'
}) {
  const { t } = useTranslation()
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingMessage])

  const renderMessage = (content) => {
    // Helper to wrap string parts with ReactMarkdown
    const renderStringWithMarkdown = (str, key) => (
      <ReactMarkdown
        key={key}
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={components}
      >
        {str}
      </ReactMarkdown>
    );

    const processedContent = processThinkingSections(content);

    if (Array.isArray(processedContent)) {
      return processedContent.map((part, index) => {
        if (typeof part === 'string') {
          // Ensure unique keys for mapped elements
          return renderStringWithMarkdown(part, `md-${index}-${Math.random()}`);
        }
        // Part is already a React element (ThinkingSection)
        return part; 
      });
    }

    // If processedContent is not an array, it means it's the original string (no think tags)
    // or it's a part that processThinkingSections decided not to split
    if (typeof processedContent === 'string') {
      return renderStringWithMarkdown(processedContent, `md-single-${Math.random()}`);
    }
    
    // Fallback for any other type (should ideally not be hit if processThinkingSections is consistent)
    return processedContent; 
  };

  return (
    <div className="flex flex-col flex-1 h-full min-h-0 bg-background md:p-2 p-0">
      <div className="flex flex-col flex-1 h-full min-h-0">
        <Card className="flex-1 overflow-y-auto flex flex-col bg-card/90 px-2 py-3 min-h-0 md:rounded-lg rounded-none md:mb-0 mb-[68px]">
          {messages.length === 0 && !streamingMessage && (
            <div className="flex flex-1 flex-col items-center justify-center text-muted-foreground text-lg md:text-base py-10 select-none">
              <span className="material-icons mb-2 text-4xl text-accent">chat_bubble_outline</span>
              <div className="hidden md:block">{t('startConversation') || 'Start a conversation...'}</div>
            </div>
          )}
          {messages.map((message, index) => (
            <div key={index} className="mb-4 py-2">
              <div 
                className={`text-xs text-muted-foreground mb-1 ${
                  message.role === 'user' ? 'text-right' : 'text-left'
                }`}
              >
                {message.role === 'user' ? username : modelName}
              </div>
              <div
                className={`px-3 py-2 rounded-lg shadow-sm whitespace-pre-wrap text-left break-words
                  ${message.role === 'user'
                    ? 'bg-primary text-primary-foreground ml-auto' 
                    : message.isToolCall 
                      ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-900 dark:text-yellow-100' 
                      : message.isFinalMessage
                        ? 'bg-green-100 dark:bg-green-900 text-green-900 dark:text-green-100'
                        : 'bg-muted'}
                  ${message.content.length < 100 ? 'max-w-fit' : 'max-w-[95%] md:max-w-[80%]'} 
                  ${message.role === 'user' ? 'ml-auto' : 'mr-auto'}
                  text-base md:text-sm
                `}
              >
                {message.isToolCall && message.isCollapsed ? (
                  <div className="flex items-center gap-2">
                    <button 
                      onClick={() => {
                        const messages = document.querySelectorAll('.tool-call-message')
                        messages.forEach(msg => msg.classList.toggle('hidden'))
                      }}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      <span className="material-icons text-sm">expand_more</span>
                      Show tool calls
                    </button>
                  </div>
                ) : (
                  renderMessage(message.content)
                )}
              </div>
            </div>
          ))}
          {/* Always show the streaming assistant message at the end if present */}
          {streamingMessage && (
            <div className="mb-4">
              <div className="text-xs text-muted-foreground mb-1 text-left">{modelName}</div>
              <div className={`px-3 py-2 rounded-lg bg-muted/50 
                ${streamingMessage.length < 100 ? 'max-w-fit' : 'max-w-[95%] md:max-w-[80%]'} 
                mr-auto text-base md:text-sm whitespace-pre-wrap text-left break-words font-mono text-xs`}>
                {streamingMessage.split('\n').map((line, i) => (
                  <div key={i} className="py-0.5 flex items-center gap-2">
                    {line.includes('⏳ Waiting for result') ? (
                      <>
                        <span className="animate-pulse">⏳</span>
                        <span>Waiting for result...</span>
                      </>
                    ) : (
                      line
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          {isLoading && !streamingMessage && (
            <div className="text-center text-muted-foreground text-base md:text-sm">
              {t('thinking')}...
            </div>
          )}
          <div ref={messagesEndRef} />
        </Card>
        {/* Sticky input bar for mobile, static for desktop */}
        <form 
          onSubmit={onSend} 
          className="flex gap-2 items-center fixed md:static bottom-0 left-0 w-full bg-background md:bg-transparent p-3 md:p-0 border-t md:border-0 z-20"
          style={{ boxShadow: '0 -2px 8px rgba(0,0,0,0.03)' }}
        >
          <Input
            type="text"
            value={input}
            onChange={onInputChange}
            placeholder={t('typeMessage')}
            className="flex-1 text-lg md:text-base h-14 md:h-12 px-4 rounded-full md:rounded-md bg-white md:bg-background border border-input"
            autoComplete="off"
          />
          <Button 
            type="submit" 
            disabled={isLoading || !input.trim()} 
            className="text-lg md:text-base px-5 h-14 md:h-12 rounded-full md:rounded-md"
            aria-label="Send message"
          >
            <span className="material-icons text-2xl md:text-lg">send</span>
          </Button>
        </form>
      </div>
    </div>
  )
} 