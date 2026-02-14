import { useState, useCallback, useEffect } from 'react';
import { Message, ApprovalRequest, ChatState } from '../types/chat';

export function useChat() {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isTyping: false,
    pendingApproval: null,
    isConnected: false,
  });

  const [sessionId, setSessionId] = useState<string | null>(null);

  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    setState((prev) => ({
      ...prev,
      messages: [
        ...prev.messages,
        {
          ...message,
          id: crypto.randomUUID(),
          timestamp: new Date(),
        },
      ],
    }));
  }, []);

  const setTyping = useCallback((isTyping: boolean) => {
    setState((prev) => ({ ...prev, isTyping }));
  }, []);

  const setApprovalRequest = useCallback((approval: ApprovalRequest | null) => {
    setState((prev) => ({ ...prev, pendingApproval: approval }));
  }, []);

  const setConnected = useCallback((isConnected: boolean) => {
    setState((prev) => ({ ...prev, isConnected }));
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    const token = localStorage.getItem('token');
    
    addMessage({ role: 'user', content });
    setTyping(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          message: content,
          session_id: sessionId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      if (data.session_id && !sessionId) {
        setSessionId(data.session_id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        role: 'assistant',
        content: 'Sorry, there was an error processing your message.',
      });
      setTyping(false);
    }
  }, [sessionId, addMessage, setTyping]);

  const sendApproval = useCallback(async (approved: boolean, userInput?: string) => {
    const token = localStorage.getItem('token');
    
    if (!state.pendingApproval || !sessionId) {
      console.error('sendApproval called but missing:', { pendingApproval: state.pendingApproval, sessionId });
      return;
    }

    try {
      console.log('Sending approval request:', { sessionId, approved, userInput });
      const response = await fetch('/api/approval', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          id: sessionId,
          approved,
          userInput,
        }),
      });

      console.log('Approval response status:', response.status, response.statusText);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Approval request failed:', response.status, errorText);
        throw new Error('Failed to send approval');
      }

      setApprovalRequest(null);
      setTyping(true);
    } catch (error) {
      console.error('Error sending approval:', error);
    }
  }, [sessionId, state.pendingApproval, setApprovalRequest, setTyping]);

  const handleMessage = useCallback((data: any) => {
    console.log('Handling message event:', data);
    addMessage({
      role: data.role || 'assistant',
      content: data.content || '',
    });
    setTyping(false);
  }, [addMessage, setTyping]);

  const handleApproval = useCallback((data: any) => {
    console.log('Handling approval event:', data);
    setTyping(false);
    setApprovalRequest(data);
  }, [setTyping, setApprovalRequest]);

  const handleError = useCallback((data: any) => {
    console.error('Handling error event:', data);
    addMessage({
      role: 'assistant',
      content: `Error: ${data.message}`,
    });
    setTyping(false);
  }, [addMessage, setTyping]);

  const handleDone = useCallback(() => {
    console.log('Handling done event');
    setTyping(false);
  }, [setTyping]);

  return {
    state,
    sessionId,
    sendMessage,
    sendApproval,
    addMessage,
    setTyping,
    setApprovalRequest,
    setConnected,
    handleMessage,
    handleApproval,
    handleError,
    handleDone,
  };
}
