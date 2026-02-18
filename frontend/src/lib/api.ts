import { BootstrapResponse, ServerState } from './types';

const API_BASE = '/api/chatkit';

export async function bootstrapChat(): Promise<BootstrapResponse> {
  const response = await fetch(`${API_BASE}/bootstrap`);
  if (!response.ok) {
    throw new Error('Failed to bootstrap chat');
  }
  return response.json();
}

export async function getThreadState(threadId: string): Promise<ServerState> {
  const response = await fetch(`${API_BASE}/state?thread_id=${threadId}`);
  if (!response.ok) {
    throw new Error('Failed to get thread state');
  }
  return response.json();
}

export async function sendMessage(
  threadId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError: (error: Error) => void
): Promise<void> {
  try {
    const response = await fetch(API_BASE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        type: 'send_message',
        thread_id: threadId,
        content: [{ type: 'text', text: message }],
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            onDone();
            return;
          }
          try {
            onChunk(data);
          } catch (e) {
            console.error('Error parsing chunk:', e);
          }
        }
      }
    }

    onDone();
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Unknown error'));
  }
}

export function subscribeToStateUpdates(
  threadId: string,
  onUpdate: (state: ServerState) => void,
  onError: (error: Error) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/state/stream?thread_id=${threadId}`);

  eventSource.onmessage = (event) => {
    try {
      const state = JSON.parse(event.data);
      onUpdate(state);
    } catch (e) {
      console.error('Error parsing state update:', e);
    }
  };

  eventSource.onerror = () => {
    onError(new Error('EventSource connection failed'));
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch('/api/health');
    return response.ok;
  } catch {
    return false;
  }
}
