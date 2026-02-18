'use client';

import { AgentEvent } from '@/lib/types';
import { cn, formatTimestamp, getAgentColor, getEventTypeIcon } from '@/lib/utils';

interface EventTimelineProps {
  events: AgentEvent[];
}

export function EventTimeline({ events }: EventTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-4">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-3">
          <span>📊</span>
          Event Timeline
        </h3>
        <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
          Events will appear here as agents work...
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <span>📊</span>
          Event Timeline
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          {events.length} events recorded
        </p>
      </div>

      <div className="max-h-96 overflow-y-auto">
        <div className="relative p-4">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-700" />

          <div className="space-y-3">
            {events.map((event, index) => (
              <EventItem key={event.id} event={event} isLast={index === events.length - 1} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function EventItem({ event, isLast }: { event: AgentEvent; isLast: boolean }) {
  const getEventColor = (type: string) => {
    switch (type) {
      case 'handoff':
        return 'bg-purple-500';
      case 'tool_call':
        return 'bg-amber-500';
      case 'tool_output':
        return 'bg-emerald-500';
      case 'message':
        return 'bg-blue-500';
      case 'context_update':
        return 'bg-slate-500';
      default:
        return 'bg-slate-400';
    }
  };

  return (
    <div className="relative pl-8 animate-slide-in">
      {/* Timeline dot */}
      <div
        className={cn(
          'absolute left-4 w-4 h-4 rounded-full border-2 border-white dark:border-slate-800 -translate-x-1/2',
          getEventColor(event.type)
        )}
      />

      {/* Event content */}
      <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-sm">{getEventTypeIcon(event.type)}</span>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">
              {event.type.replace('_', ' ')}
            </span>
          </div>
          {event.timestamp && (
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
              {formatTimestamp(event.timestamp)}
            </span>
          )}
        </div>

        <div className="mt-1">
          <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
            {event.agent}
          </span>
          {event.content && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 break-words">
              {event.content}
            </p>
          )}
        </div>

        {/* Metadata */}
        {event.metadata && Object.keys(event.metadata).length > 0 && (
          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-600">
            {event.type === 'handoff' && event.metadata.target_agent && (
              <div className="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400">
                <span>→</span>
                <span>{event.metadata.target_agent}</span>
              </div>
            )}
            {event.type === 'tool_call' && event.metadata.tool_args && (
              <div className="text-[10px] font-mono text-slate-500 dark:text-slate-400 truncate">
                args: {typeof event.metadata.tool_args === 'string' 
                  ? event.metadata.tool_args 
                  : JSON.stringify(event.metadata.tool_args)}
              </div>
            )}
            {event.type === 'context_update' && event.metadata.changes && (
              <div className="text-[10px] text-slate-500 dark:text-slate-400">
                Updated: {Object.keys(event.metadata.changes).join(', ')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
