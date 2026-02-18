'use client';

import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Message } from '@/lib/types';
import { cn, getAgentIcon, getAgentColor } from '@/lib/utils';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={cn(
        'flex gap-3 animate-fade-in',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm',
          isUser
            ? 'bg-copilot-600 text-white'
            : getAgentColor(message.agent || 'Triage Agent') + ' text-white'
        )}
      >
        {isUser ? '👤' : getAgentIcon(message.agent || 'Triage Agent')}
      </div>

      {/* Message Bubble */}
      <div
        className={cn(
          'max-w-[80%] px-4 py-3 rounded-2xl',
          isUser
            ? 'bg-copilot-600 text-white rounded-br-md'
            : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-bl-md'
        )}
      >
        {/* Agent indicator for assistant messages */}
        {!isUser && message.agent && (
          <div className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium">
            {message.agent}
          </div>
        )}

        {/* Message content */}
        <div
          className={cn(
            'prose prose-sm max-w-none',
            isUser
              ? 'prose-invert'
              : 'dark:prose-invert prose-slate'
          )}
        >
          {message.content ? (
            <ReactMarkdown
              components={{
                code({ node, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const inline = !match;
                  
                  return inline ? (
                    <code
                      className={cn(
                        'px-1.5 py-0.5 rounded text-sm font-mono',
                        isUser
                          ? 'bg-copilot-700'
                          : 'bg-slate-100 dark:bg-slate-700'
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <SyntaxHighlighter
                      style={oneDark}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-lg !mt-2 !mb-2"
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  );
                },
                // Ensure links open in new tab
                a({ children, href, ...props }) {
                  return (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-copilot-500 hover:text-copilot-600 underline"
                      {...props}
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            <div className="flex items-center gap-1">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div
          className={cn(
            'text-xs mt-1',
            isUser ? 'text-copilot-200' : 'text-slate-400 dark:text-slate-500'
          )}
        >
          {message.timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  );
}
