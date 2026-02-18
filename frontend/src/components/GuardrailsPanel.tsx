'use client';

import { GuardrailCheck } from '@/lib/types';
import { cn, formatTimestamp } from '@/lib/utils';

interface GuardrailsPanelProps {
  guardrails: GuardrailCheck[];
}

export function GuardrailsPanel({ guardrails }: GuardrailsPanelProps) {
  if (guardrails.length === 0) {
    return null;
  }

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <span>🛡️</span>
          Guardrails
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Input validation checks
        </p>
      </div>

      <div className="p-3 space-y-2">
        {guardrails.map((check) => (
          <div
            key={check.id}
            className={cn(
              'p-3 rounded-lg border',
              check.passed
                ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                : 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20'
            )}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={check.passed ? 'text-green-500' : 'text-red-500'}>
                  {check.passed ? '✓' : '✕'}
                </span>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  {check.name}
                </span>
              </div>
              <span
                className={cn(
                  'px-2 py-0.5 text-[10px] font-medium rounded-full',
                  check.passed
                    ? 'bg-green-100 text-green-700 dark:bg-green-800 dark:text-green-300'
                    : 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-300'
                )}
              >
                {check.passed ? 'PASSED' : 'FAILED'}
              </span>
            </div>

            {check.reasoning && (
              <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
                {check.reasoning}
              </p>
            )}

            <div className="mt-2 text-[10px] text-slate-400 dark:text-slate-500">
              {formatTimestamp(check.timestamp)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
