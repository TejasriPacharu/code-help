'use client';

import { Agent } from '@/lib/types';
import { cn, getAgentColor, getAgentIcon, getAgentTextColor } from '@/lib/utils';

interface AgentPanelProps {
  agents: Agent[];
  currentAgent: string;
}

export function AgentPanel({ agents, currentAgent }: AgentPanelProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <span>🤖</span>
          Agents
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Specialist agents available
        </p>
      </div>

      <div className="p-3 space-y-2">
        {agents.map((agent) => {
          const isActive = agent.name === currentAgent;
          
          return (
            <div
              key={agent.name}
              className={cn(
                'p-3 rounded-lg border transition-all',
                isActive
                  ? 'border-copilot-500 bg-copilot-50 dark:bg-copilot-900/20'
                  : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50'
              )}
            >
              {/* Agent header */}
              <div className="flex items-center gap-2">
                <span className="text-lg">{getAgentIcon(agent.name)}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'text-sm font-medium truncate',
                        isActive
                          ? 'text-copilot-700 dark:text-copilot-300'
                          : 'text-slate-700 dark:text-slate-300'
                      )}
                    >
                      {agent.name}
                    </span>
                    {isActive && (
                      <span className="flex items-center gap-1 px-1.5 py-0.5 bg-copilot-500 text-white text-[10px] font-medium rounded-full">
                        <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
                        Active
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5">
                    {agent.description}
                  </p>
                </div>
              </div>

              {/* Tools */}
              {isActive && agent.tools.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 mb-1">
                    Tools
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {agent.tools.map((tool) => (
                      <span
                        key={tool}
                        className="px-1.5 py-0.5 text-[10px] font-mono bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Handoffs */}
              {isActive && agent.handoffs.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700">
                  <p className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 mb-1">
                    Can hand off to
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {agent.handoffs.map((handoff) => (
                      <span
                        key={handoff}
                        className="px-1.5 py-0.5 text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded flex items-center gap-1"
                      >
                        <span>{getAgentIcon(handoff)}</span>
                        {handoff.replace(' Agent', '')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
