export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface ApprovalRequest {
  id: string;
  message: string;
  type: 'confirmation' | 'cancellation' | 'input';
  placeholder?: string;
}

export type SSEEvent = 
  | { type: 'message'; data: Message }
  | { type: 'approval'; data: ApprovalRequest }
  | { type: 'error'; data: { message: string } }
  | { type: 'done' };

export interface ChatState {
  messages: Message[];
  isTyping: boolean;
  pendingApproval: ApprovalRequest | null;
  isConnected: boolean;
}
