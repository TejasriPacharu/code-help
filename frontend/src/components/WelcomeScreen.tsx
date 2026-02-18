'use client';

interface WelcomeScreenProps {
  onExampleClick: (example: string) => void;
}

const examples = [
  {
    title: 'Debug Performance Issues',
    description: 'Analyze slow API responses and find bottlenecks',
    prompt: 'My API is slow. Can you help diagnose the issue?',
    icon: '🔍',
    color: 'from-red-500 to-orange-500',
  },
  {
    title: 'Security Audit',
    description: 'Scan for vulnerabilities and security best practices',
    prompt: 'Audit my application for security vulnerabilities',
    icon: '🛡️',
    color: 'from-pink-500 to-purple-500',
  },
  {
    title: 'Generate Tests',
    description: 'Create unit tests and load tests for your code',
    prompt: 'Generate comprehensive unit tests for my project',
    icon: '🧪',
    color: 'from-green-500 to-emerald-500',
  },
  {
    title: 'Code Refactoring',
    description: 'Improve code quality and apply design patterns',
    prompt: 'Analyze my code quality and suggest refactoring improvements',
    icon: '🔧',
    color: 'from-amber-500 to-yellow-500',
  },
  {
    title: 'Generate Documentation',
    description: 'Create API docs, docstrings, and README files',
    prompt: 'Generate API documentation for my project',
    icon: '📝',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    title: 'Full Analysis',
    description: 'Comprehensive code analysis with all agents',
    prompt: 'My API is slow and I need help with performance, security, and testing',
    icon: '🚀',
    color: 'from-violet-500 to-purple-500',
  },
];

export function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      {/* Hero section */}
      <div className="text-center mb-12">
        <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-copilot-500 to-copilot-700 flex items-center justify-center text-4xl shadow-xl">
          🤖
        </div>
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
          AI Software Engineering Copilot
        </h2>
        <p className="text-slate-600 dark:text-slate-400 max-w-lg mx-auto">
          Get help with debugging, code analysis, testing, security reviews, and documentation.
          Our specialized agents work together to solve complex engineering challenges.
        </p>
      </div>

      {/* Example cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-w-4xl w-full">
        {examples.map((example) => (
          <button
            key={example.title}
            onClick={() => onExampleClick(example.prompt)}
            className="group p-5 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-copilot-300 dark:hover:border-copilot-600 hover:shadow-lg transition-all text-left"
          >
            <div
              className={`w-10 h-10 rounded-lg bg-gradient-to-br ${example.color} flex items-center justify-center text-xl mb-3 group-hover:scale-110 transition-transform`}
            >
              {example.icon}
            </div>
            <h3 className="font-semibold text-slate-900 dark:text-white mb-1">
              {example.title}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {example.description}
            </p>
          </button>
        ))}
      </div>

      {/* Agent overview */}
      <div className="mt-12 text-center">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
          Powered by specialized agents
        </p>
        <div className="flex flex-wrap justify-center gap-3">
          {[
            { name: 'Triage', icon: '🎯' },
            { name: 'Bug Diagnosis', icon: '🔍' },
            { name: 'Refactoring', icon: '🔧' },
            { name: 'Testing', icon: '🧪' },
            { name: 'Security', icon: '🛡️' },
            { name: 'Documentation', icon: '📝' },
          ].map((agent) => (
            <span
              key={agent.name}
              className="px-3 py-1.5 bg-slate-100 dark:bg-slate-700 rounded-full text-sm text-slate-600 dark:text-slate-400 flex items-center gap-1.5"
            >
              <span>{agent.icon}</span>
              {agent.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
