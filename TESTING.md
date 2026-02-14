# Testing Guide - Kunjal Agents

This guide provides specific test scenarios for the Kunjal Agents application.

## Sample Orders

The system has 2 sample orders pre-loaded:

### Order ORD-001
- **Customer**: John Doe
- **Status**: shipped
- **Items**: Laptop, Mouse
- **Total**: $1299.99
- **Date**: 2024-01-15

### Order ORD-002
- **Customer**: Jane Smith
- **Status**: processing
- **Items**: Headphones
- **Total**: $199.99
- **Date**: 2024-01-20

## Test Scenarios

### 1. Basic Order Status Check

**User Input:**
```
What's the status of ORD-001?
```

**Expected Output:**
```
The order ORD-001 for John Doe is currently shipped. It contains: Laptop, Mouse. Total amount: $1299.99.
```

**What to verify:**
- AI retrieves order details correctly
- Response is displayed in chat bubble
- No approval prompt appears

---

### 2. Multiple Order Checks

**User Input:**
```
Check the status of ORD-002
```

**Expected Output:**
```
Order ORD-002 for Jane Smith is currently processing. It contains: Headphones. Total: $199.99.
```

**What to verify:**
- AI correctly retrieves different order
- Order status is accurate

---

### 3. Order Cancellation (Triggers Approval Flow)

**User Input:**
```
I want to cancel order ORD-001
```

**Expected Flow:**
1. AI generates a verification code (6-digit number)
2. **Approval Prompt appears** in the UI
3. Prompt shows: "Please verify the cancellation for order ORD-001. Your verification code is: XXXXXX. Please enter this code to confirm the cancellation."
4. User enters the code in the input field
5. User clicks "Approve"
6. AI cancels the order and confirms

**Expected Final Output:**
```
Order ORD-001 has been successfully cancelled. Refund amount: $1299.99.
```

**What to verify:**
- Verification code is generated and displayed
- Approval prompt appears with correct message
- Input field is pre-configured for code entry
- After approval, order status changes to "cancelled"
- Refund amount is mentioned

---

### 4. Order Cancellation - Rejected

**User Input:**
```
Cancel ORD-002
```

**Expected Flow:**
1. AI generates verification code
2. **Approval Prompt appears**
3. User clicks "Reject" instead of entering code
4. AI acknowledges rejection

**Expected Output:**
```
I understand you've decided not to cancel order ORD-002. The order remains in processing status. Is there anything else I can help you with?
```

**What to verify:**
- Rejection button works
- Order remains unchanged
- AI handles rejection gracefully

---

### 5. Invalid Order ID

**User Input:**
```
What's the status of ORD-999?
```

**Expected Output:**
```
I'm sorry, but I couldn't find an order with ID ORD-999. Please check the order ID and try again.
```

**What to verify:**
- AI handles non-existent orders
- User receives clear error message

---

### 6. Wrong Verification Code

**User Input:**
```
Cancel ORD-001
```

**Expected Flow:**
1. AI generates code (e.g., "123456")
2. Approval prompt appears
3. User enters wrong code (e.g., "000000")
4. User clicks "Approve"

**Expected Output:**
```
I'm sorry, but the verification code you entered is invalid. Please check the code and try again. The verification code for order ORD-001 is: 123456
```

**What to verify:**
- Invalid codes are rejected
- User is told to try again
- Original code is shown again

---

### 7. Non-Order Related Query

**User Input:**
```
What's the weather like today?
```

**Expected Output:**
```
I can only assist with order-related queries. Is there something about your orders I can help you with?
```

**What to verify:**
- Guardrail prevents answering non-order questions
- AI redirects to order-related queries

---

### 8. Multiple Cancellations

**User Input:**
```
Cancel ORD-001
```

**Flow:**
1. Generate code, cancel with correct code
2. Wait for completion

**User Input:**
```
Cancel ORD-002
```

**Flow:**
1. Generate code, cancel with correct code

**What to verify:**
- Multiple approvals work in sequence
- Session maintains history
- Each cancellation is independent

---

### 9. Greetings and Small Talk

**User Input:**
```
Hello
```

**Expected Output:**
```
Hello! I'm here to help you with your orders. How can I assist you today?
```

**What to verify:**
- AI responds to greetings
- Redirects to order-related help

---

### 10. Complex Multi-Turn Conversation

**User Input:**
```
What orders do I have?
```

**Expected Output:**
```
I can help you check the status of your orders. Please provide your order ID (e.g., ORD-001, ORD-002).
```

**User Input:**
```
Check ORD-001
```

**Expected Output:**
```
The order ORD-001 for John Doe is currently shipped. It contains: Laptop, Mouse. Total: $1299.99.
```

**User Input:**
```
Actually, I want to cancel it
```

**Expected Flow:**
1. AI generates verification code
2. Approval prompt appears
3. User enters code
4. Order is cancelled

**What to verify:**
- Multi-turn conversations work
- AI maintains context
- Approval flow works mid-conversation

---

## API-Level Testing

### Test Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

### Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

Expected: `{"session_id":"..."}`

### Test SSE Connection

```bash
curl -N "http://localhost:8000/api/events?session_id=test-session"
```

Expected: Stream of events (might be empty initially)

---

## Performance Testing

### Rapid Message Testing

Send multiple messages quickly:
```
1. What's ORD-001 status?
2. Check ORD-002
3. Cancel ORD-001
```

**What to verify:**
- System handles rapid requests
- Messages are processed in order
- UI remains responsive

### Long Running Session

Keep the session open for 5+ minutes and send periodic messages.

**What to verify:**
- Connection remains stable
- Session persists
- No memory leaks (monitor in DevTools)

---

## Edge Cases

### Empty Message

**User Input:**
```
(Press Enter without typing)
```

**Expected:**
- Input should be ignored or prompt user to enter text

### Very Long Message

**User Input:**
```
(Paste a very long paragraph - 1000+ characters)
```

**Expected:**
- Message should be processed
- No UI errors
- Response should be relevant

### Special Characters

**User Input:**
```
What about order @#$%^&*()?
```

**Expected:**
- System handles special characters
- No crashes or errors

### Multiple Simultaneous Users

Open multiple browser tabs to http://localhost:5173

**What to verify:**
- Each tab has its own session
- Messages don't leak between sessions
- Approvals are independent

---

## UI/UX Testing

### Responsive Design

Test on different screen sizes:
- Desktop (1920x1080)
- Laptop (1366x768)
- Tablet (768x1024)
- Mobile (375x667)

**What to verify:**
- UI adapts to screen size
- All elements remain accessible
- No horizontal scrolling

### Keyboard Navigation

- **Tab**: Navigate between elements
- **Enter**: Send message
- **Escape**: Cancel current action (if implemented)

### Accessibility

- Test with screen reader (if available)
- Check color contrast
- Verify focus states

---

## Browser Compatibility

Test in different browsers:
- Chrome/Edge
- Firefox
- Safari

**What to verify:**
- All features work
- No console errors
- Consistent appearance

---

## Logging and Debugging

### Backend Logs

Monitor backend terminal for:
- API requests received
- Tool calls executed
- Errors or warnings

### Frontend Logs

Open browser DevTools (F12) and check:
- Console for errors
- Network tab for API calls
- SSE connections in Network tab

---

## Success Criteria

A successful test session should:
- ✅ All basic order queries work
- ✅ Approval flow triggers correctly
- ✅ Verifications work (both correct and incorrect codes)
- ✅ Guardrails prevent non-order queries
- ✅ UI remains responsive
- ✅ No errors in console
- ✅ SSE connection stays stable
- ✅ Multiple sessions work independently

---

## Report Issues

If you find any issues:
1. Note the exact steps to reproduce
2. Record the expected vs actual behavior
3. Check console logs for errors
4. Document browser and OS

Happy testing! 🧪
