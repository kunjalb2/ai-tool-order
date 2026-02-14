import React, { useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';
import { useSSE } from '../hooks/useSSE';
import { ChatMessage } from './ChatMessage';
import { ApprovalPrompt } from './ApprovalPrompt';
import { TypingIndicator } from './TypingIndicator';
import { ChatInput } from './ChatInput';
import { ChatHeader } from './ChatHeader';
import { ProtectedRoute } from './ProtectedRoute';

function ChatComponent() {
  const { 
    state, 
    sessionId, 
    sendMessage, 
    sendApproval, 
    setConnected,
    handleMessage,
    handleApproval,
    handleError,
    handleDone,
  } = useChat();
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { isConnected, onEvent, disconnect } = useSSE('/api/events', sessionId || '');

  // Set up SSE event handlers
  useEffect(() => {
    if (sessionId) {
      setConnected(isConnected);
    }

    onEvent('message', handleMessage);
    onEvent('approval', handleApproval);
    onEvent('error', handleError);
    onEvent('done', handleDone);

    return () => {
      disconnect();
    };
  }, [isConnected, onEvent, setConnected, handleMessage, handleApproval, handleError, handleDone, disconnect, sessionId]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [state.messages, state.pendingApproval]);

  const handleSend = (message: string) => {
    sendMessage(message);
  };

  const handleApprove = (userInput?: string) => {
    sendApproval(true, userInput);
  };

  const handleRejection = () => {
    sendApproval(false);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <ChatHeader isConnected={isConnected} sessionId={sessionId} />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-4xl mx-auto">
          {state.messages.length === 0 && (
            <div className="flex items-center justify-center h-full min-h-[300px]">
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <h2 className="text-lg font-medium text-gray-900 mb-2">Start a conversation</h2>
                <p className="text-gray-500">Ask me about your orders (try "What's the status of ORD-001?")</p>
              </div>
            </div>
          )}

          {state.messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {state.isTyping && <TypingIndicator />}

          {state.pendingApproval && (
            <ApprovalPrompt
              approval={state.pendingApproval}
              onApprove={handleApprove}
              onReject={handleRejection}
            />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={state.isTyping || !!state.pendingApproval}
      />
    </div>
  );
}

export function Chat() {
  return (
    <ProtectedRoute>
      <ChatComponent />
    </ProtectedRoute>
  );
}
