'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { Message, ServerState, AgentEvent } from '@/lib/types';
import { bootstrapChat, sendMessage, subscribeToStateUpdates } from '@/lib/api';

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  threadId: string | null;
  serverState: ServerState | null;
  sendUserMessage: (content: string) => Promise<void>;
  resetChat: () => Promise<void>;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [serverState, setServerState] = useState<ServerState | null>(null);
  const unsubscribeRef = useRef<(() => void) | null>(null);
  const currentAssistantMessageRef = useRef<string>('');

  // Initialize chat
  const initializeChat = useCallback(async () => {
    try {
      setError(null);
      const response = await bootstrapChat();
      setThreadId(response.thread_id);
      setServerState(response);
      
      // Subscribe to state updates
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
      
      unsubscribeRef.current = subscribeToStateUpdates(
        response.thread_id,
        (state) => {
          setServerState(state);
        },
        (err) => {
          console.error('State subscription error:', err);
        }
      );
    } catch (err) {
      setError('Failed to initialize chat. Make sure the backend is running.');
      console.error('Bootstrap error:', err);
    }
  }, []);

  // Initialize on mount
  useEffect(() => {
    initializeChat();
    
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, [initializeChat]);

  // Send a user message
  const sendUserMessage = useCallback(async (content: string) => {
    if (!threadId || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    currentAssistantMessageRef.current = '';

    // Create placeholder for assistant message
    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        agent: serverState?.current_agent,
      },
    ]);

    await sendMessage(
      threadId,
      content,
      (chunk) => {
        try {
          const data = JSON.parse(chunk);
          
          // Handle different event types
          if (data.type === 'thread_item_delta_event') {
            const delta = data.delta;
            if (delta?.type === 'text' && delta?.text) {
              currentAssistantMessageRef.current += delta.text;
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: currentAssistantMessageRef.current }
                    : msg
                )
              );
            }
          } else if (data.type === 'thread_item_done_event') {
            // Message complete
            if (data.item?.content?.[0]?.text) {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMessageId
                    ? { 
                        ...msg, 
                        content: data.item.content[0].text,
                        agent: serverState?.current_agent,
                      }
                    : msg
                )
              );
            }
          } else if (data.type === 'client_effect_event') {
            // Handle client effects (state updates, etc.)
            if (data.name === 'runner_state_update') {
              // State will be updated via SSE subscription
            }
          }
        } catch (e) {
          // Non-JSON chunk, might be plain text
          if (chunk.trim()) {
            currentAssistantMessageRef.current += chunk;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: currentAssistantMessageRef.current }
                  : msg
              )
            );
          }
        }
      },
      () => {
        setIsLoading(false);
      },
      (err) => {
        setError(err.message);
        setIsLoading(false);
        // Remove empty assistant message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== assistantMessageId));
      }
    );
  }, [threadId, isLoading, serverState?.current_agent]);

  // Reset chat
  const resetChat = useCallback(async () => {
    setMessages([]);
    setServerState(null);
    if (unsubscribeRef.current) {
      unsubscribeRef.current();
    }
    await initializeChat();
  }, [initializeChat]);

  return {
    messages,
    isLoading,
    error,
    threadId,
    serverState,
    sendUserMessage,
    resetChat,
  };
}
