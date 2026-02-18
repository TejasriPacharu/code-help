'use client';

import { useEffect, useRef, useState } from 'react';
import { useChat } from '@/hooks/useChat';
import {
  Header,
  ChatMessage,
  ChatInput,
  AgentPanel,
  EventTimeline,
  ContextPanel,
  GuardrailsPanel,
  WelcomeScreen,
} from '@/components';
import { checkHealth } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function Home() {
  const {
    messages,
    isLoading,
    error,
    threadId,
    serverState,
    sendUserMessage,
    resetChat,
  } = useChat();

  const [isBackendReady, setIsBackendReady] = useState<boolean | null>(null);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      const healthy = await checkHealth();
      setIsBackendReady(healthy);
    };
    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle example prompt click from welcome screen
  const handleExampleClick = (prompt: string) => {
    sendUserMessage(prompt);
  };

  // Backend not ready state
  if (isBackendReady === false) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center p-8 max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Backend Not Connected
          </h2>
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            The Python backend server is not running. Please start it with:
          </p>
          <code className="block bg-slate-800 text-green-400 p-4 rounded-lg text-sm text-left mb-4">
            cd python-backend<br />
            python -m uvicorn main:app --reload --port 8000
          </code>
          <button
            onClick={() => checkHealth().then(setIsBackendReady)}
            className="px-4 py-2 bg-copilot-600 text-white rounded-lg hover:bg-copilot-700 transition-colors"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (isBackendReady === null || !serverState) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-copilot-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-600 dark:text-slate-400">
            Connecting to AI Copilot...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-50 dark:bg-slate-900">
      {/* Header */}
      <Header currentAgent={serverState.current_agent} onReset={resetChat} />

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <WelcomeScreen onExampleClick={handleExampleClick} />
            ) : (
              <div className="max-w-3xl mx-auto space-y-4">
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Error display */}
          {error && (
            <div className="px-4 pb-2">
              <div className="max-w-3xl mx-auto bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-600 dark:text-red-400">
                {error}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="max-w-3xl mx-auto w-full">
            <ChatInput onSend={sendUserMessage} isLoading={isLoading} />
          </div>
        </div>

        {/* Sidebar toggle button (mobile) */}
        <button
          onClick={() => setShowSidebar(!showSidebar)}
          className="fixed bottom-20 right-4 lg:hidden z-50 w-12 h-12 bg-copilot-600 text-white rounded-full shadow-lg flex items-center justify-center"
        >
          {showSidebar ? '✕' : '📊'}
        </button>

        {/* Right sidebar */}
        <div
          className={cn(
            'w-80 border-l border-slate-200 dark:border-slate-700 bg-slate-100 dark:bg-slate-800/50 overflow-y-auto',
            'fixed lg:relative right-0 top-0 bottom-0 z-40 lg:z-0 transition-transform',
            showSidebar ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'
          )}
        >
          <div className="p-4 space-y-4">
            {/* Agents Panel */}
            <AgentPanel
              agents={serverState.agents}
              currentAgent={serverState.current_agent}
            />

            {/* Context Panel */}
            <ContextPanel context={serverState.context} />

            {/* Event Timeline */}
            <EventTimeline events={serverState.events} />

            {/* Guardrails Panel */}
            <GuardrailsPanel guardrails={serverState.guardrails} />
          </div>
        </div>
      </div>
    </div>
  );
}
