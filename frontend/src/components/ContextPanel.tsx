'use client';

import { CopilotContext } from '@/lib/types';
import { cn, getSeverityColor } from '@/lib/utils';

interface ContextPanelProps {
  context: CopilotContext;
}

export function ContextPanel({ context }: ContextPanelProps) {
  const hasProject = context.project_name || context.language;
  const hasDiagnosis = context.error_type || context.diagnosis_report;
  const hasQuality = context.complexity_score !== undefined || context.code_smells?.length;
  const hasTesting = context.test_coverage !== undefined || context.test_framework;
  const hasSecurity = context.security_score !== undefined || context.vulnerabilities?.length;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <span>📋</span>
          Context
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
          Current analysis state
        </p>
      </div>

      <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
        {/* Project Info */}
        {hasProject && (
          <ContextSection title="Project" icon="📁">
            {context.project_name && (
              <ContextItem label="Name" value={context.project_name} />
            )}
            {context.language && (
              <ContextItem label="Language" value={context.language} />
            )}
            {context.framework && (
              <ContextItem label="Framework" value={context.framework} />
            )}
            {context.repo_path && (
              <ContextItem label="Path" value={context.repo_path} mono />
            )}
          </ContextSection>
        )}

        {/* Diagnosis Info */}
        {hasDiagnosis && (
          <ContextSection title="Diagnosis" icon="🔍">
            {context.error_type && (
              <ContextItem 
                label="Error Type" 
                value={context.error_type}
                badge
                badgeColor="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
              />
            )}
            {context.affected_endpoint && (
              <ContextItem label="Endpoint" value={context.affected_endpoint} mono />
            )}
          </ContextSection>
        )}

        {/* Code Quality */}
        {hasQuality && (
          <ContextSection title="Code Quality" icon="📊">
            {context.complexity_score !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Complexity Score
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        context.complexity_score <= 3
                          ? 'bg-green-500'
                          : context.complexity_score <= 6
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      )}
                      style={{ width: `${(context.complexity_score / 10) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    {context.complexity_score}/10
                  </span>
                </div>
              </div>
            )}
            {context.code_smells && context.code_smells.length > 0 && (
              <div className="mt-2">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Code Smells ({context.code_smells.length})
                </span>
                <div className="mt-1 space-y-1">
                  {context.code_smells.slice(0, 3).map((smell, i) => (
                    <div
                      key={i}
                      className="text-[10px] text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded truncate"
                    >
                      {smell}
                    </div>
                  ))}
                  {context.code_smells.length > 3 && (
                    <span className="text-[10px] text-slate-400">
                      +{context.code_smells.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </ContextSection>
        )}

        {/* Testing */}
        {hasTesting && (
          <ContextSection title="Testing" icon="🧪">
            {context.test_framework && (
              <ContextItem label="Framework" value={context.test_framework} />
            )}
            {context.test_coverage !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Coverage
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        context.test_coverage >= 80
                          ? 'bg-green-500'
                          : context.test_coverage >= 50
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      )}
                      style={{ width: `${context.test_coverage}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    {context.test_coverage}%
                  </span>
                </div>
              </div>
            )}
          </ContextSection>
        )}

        {/* Security */}
        {hasSecurity && (
          <ContextSection title="Security" icon="🛡️">
            {context.security_score !== undefined && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Security Score
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full',
                        context.security_score >= 80
                          ? 'bg-green-500'
                          : context.security_score >= 50
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      )}
                      style={{ width: `${context.security_score}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    {context.security_score}/100
                  </span>
                </div>
              </div>
            )}
            {context.vulnerabilities && context.vulnerabilities.length > 0 && (
              <div className="mt-2">
                <span className="text-xs text-slate-500 dark:text-slate-400">
                  Vulnerabilities ({context.vulnerabilities.length})
                </span>
                <div className="mt-1 space-y-1">
                  {context.vulnerabilities.slice(0, 3).map((vuln) => (
                    <div
                      key={vuln.id}
                      className="flex items-center gap-2 text-[10px]"
                    >
                      <span
                        className={cn(
                          'px-1.5 py-0.5 rounded font-medium',
                          getSeverityColor(vuln.severity)
                        )}
                      >
                        {vuln.severity}
                      </span>
                      <span className="text-slate-600 dark:text-slate-400 truncate">
                        {vuln.type}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </ContextSection>
        )}

        {/* Empty state */}
        {!hasProject && !hasDiagnosis && !hasQuality && !hasTesting && !hasSecurity && (
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
            Context will populate as analysis progresses...
          </p>
        )}
      </div>
    </div>
  );
}

function ContextSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 uppercase">
        <span>{icon}</span>
        {title}
      </h4>
      <div className="space-y-1.5 pl-5">{children}</div>
    </div>
  );
}

function ContextItem({
  label,
  value,
  mono,
  badge,
  badgeColor,
}: {
  label: string;
  value: string;
  mono?: boolean;
  badge?: boolean;
  badgeColor?: string;
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      {badge ? (
        <span className={cn('px-2 py-0.5 rounded-full font-medium', badgeColor)}>
          {value}
        </span>
      ) : (
        <span
          className={cn(
            'text-slate-700 dark:text-slate-300 font-medium truncate max-w-[60%]',
            mono && 'font-mono text-[10px]'
          )}
        >
          {value}
        </span>
      )}
    </div>
  );
}
