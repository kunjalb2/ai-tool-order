import React, { useState } from 'react';
import { ApprovalRequest } from '../types/chat';

interface ApprovalPromptProps {
  approval: ApprovalRequest;
  onApprove: (userInput?: string) => void;
  onReject: () => void;
}

export function ApprovalPrompt({ approval, onApprove, onReject }: ApprovalPromptProps) {
  const [userInput, setUserInput] = useState('');

  const handleApprove = () => {
    onApprove(userInput || undefined);
    setUserInput('');
  };

  const handleReject = () => {
    onReject();
    setUserInput('');
  };

  return (
    <div className="flex justify-start mb-4">
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 max-w-md shadow-sm">
        <div className="flex items-start gap-3">
          <div className="text-amber-600 mt-0.5">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-sm text-gray-800 mb-3">{approval.message}</p>
            
            {approval.type === 'input' && approval.placeholder && (
              <input
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder={approval.placeholder}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            )}
            
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                className="btn-primary text-sm"
              >
                {approval.type === 'cancellation' ? 'Yes, Cancel' : 'Approve'}
              </button>
              <button
                onClick={handleReject}
                className="btn-secondary text-sm"
              >
                {approval.type === 'cancellation' ? 'No, Continue' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
