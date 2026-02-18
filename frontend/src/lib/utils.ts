import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function getAgentColor(agentName: string): string {
  const colors: Record<string, string> = {
    'Triage Agent': 'bg-agent-triage',
    'Bug Diagnosis Agent': 'bg-agent-diagnosis',
    'Refactoring Agent': 'bg-agent-refactoring',
    'Test Generator Agent': 'bg-agent-testing',
    'Security Review Agent': 'bg-agent-security',
    'Documentation Agent': 'bg-agent-documentation',
  };
  return colors[agentName] || 'bg-slate-500';
}

export function getAgentTextColor(agentName: string): string {
  const colors: Record<string, string> = {
    'Triage Agent': 'text-agent-triage',
    'Bug Diagnosis Agent': 'text-agent-diagnosis',
    'Refactoring Agent': 'text-agent-refactoring',
    'Test Generator Agent': 'text-agent-testing',
    'Security Review Agent': 'text-agent-security',
    'Documentation Agent': 'text-agent-documentation',
  };
  return colors[agentName] || 'text-slate-500';
}

export function getAgentIcon(agentName: string): string {
  const icons: Record<string, string> = {
    'Triage Agent': '🎯',
    'Bug Diagnosis Agent': '🔍',
    'Refactoring Agent': '🔧',
    'Test Generator Agent': '🧪',
    'Security Review Agent': '🛡️',
    'Documentation Agent': '📝',
  };
  return icons[agentName] || '🤖';
}

export function getEventTypeIcon(eventType: string): string {
  const icons: Record<string, string> = {
    message: '💬',
    handoff: '🔄',
    tool_call: '⚙️',
    tool_output: '📤',
    context_update: '📋',
  };
  return icons[eventType] || '•';
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + '...';
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    CRITICAL: 'bg-red-600 text-white',
    HIGH: 'bg-orange-500 text-white',
    MEDIUM: 'bg-yellow-500 text-black',
    LOW: 'bg-blue-500 text-white',
  };
  return colors[severity] || 'bg-slate-500 text-white';
}
