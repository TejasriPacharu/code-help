'use client';

import { cn, getAgentColor, getAgentIcon } from '@/lib/utils';

interface HeaderProps {
  currentAgent: string;
  onReset: () => void;
}

export function Header({ currentAgent, onReset }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-copilot-500 to-copilot-700 flex items-center justify-center text-white font-bold text-lg shadow-lg">
            🤖
          </div>
          <div>
            <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
              AI Software Engineering Copilot
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Multi-agent system for code analysis & improvement
            </p>
          </div>
        </div>

        {/* Current Agent Indicator */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-700 rounded-full">
            <span className="text-sm">{getAgentIcon(currentAgent)}</span>
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              {currentAgent}
            </span>
            <span
              className={cn(
                'w-2 h-2 rounded-full animate-pulse',
                getAgentColor(currentAgent)
              )}
            />
          </div>

          {/* Reset Button */}
          <button
            onClick={onReset}
            className="px-3 py-1.5 text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            New Chat
          </button>
        </div>
      </div>
    </header>
  );
}
