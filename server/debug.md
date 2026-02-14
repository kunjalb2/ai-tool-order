# Reverse Engineering Guide - Learn by Breaking It Down 🔍

## For Absolute Beginners: How to Learn This Agent

This guide will teach you how to **reverse engineer** this AI agent code to truly understand it, not just copy it.

---

## 🎯 Learning Philosophy

> "The best way to learn is to **take it apart, see how it works, and build it back up.**"

Instead of reading top-to-bottom, we'll:

1. **Start simple** - Understand one piece at a time
2. **Run experiments** - Change things and see what happens
3. **Build incrementally** - Start from scratch and add features
4. **Ask questions** - Why does this work? What if I change this?

---

## 📚 Week 1: Foundation (Days 1-3)

### Day 1: Understand the Basics

**Goal:** Run the code and see what happens

**Tasks:**

1. Run `python interactive_agent.py`
2. Try these conversations:
   - "Check order ORD-001"
   - "What is 2+2?" (test guardrails)
   - "Cancel order ORD-002" (test verification)

**Questions to Ask Yourself:**

- What did the agent do differently in each case?
- When did it call tools? When didn't it?
- What happens when I give a wrong verification code?

**🔬 Experiment 1: Break Something**

```python
# Change this line in GUARDRAILS:
"I apologize, but I can only assist with order-related queries..."

# To:
"BEEP BOOP! Not my job!"

# Run it and see the difference!
```

**What You'll Learn:** How guardrails control agent behavior

---

### Day 2: Understand Data Flow

**Goal:** Follow one complete interaction from start to finish

**Pick ONE scenario and trace it:**

```
Scenario: "Check order ORD-001"
```

**Trace the Flow:**

```
1. User types: "Check order ORD-001"
   ↓
2. run_agent() is called
   ↓
3. Message added to conversation_history
   ↓
4. Sent to OpenRouter API with:
   - System prompt (instructions + guardrails)
   - Conversation history
   - Available tools
   ↓
5. AI decides: "I need to use get_order_status tool"
   ↓
6. Tool is called: get_order_status("ORD-001")
   ↓
7. Function looks up ORDERS_DB["ORD-001"]
   ↓
8. Returns: {"success": True, "order": {...}}
   ↓
9. Result sent back to AI
   ↓
10. AI generates response based on tool result
   ↓
11. Response shown to user
```

**🔬 Experiment 2: Add Print Statements**

```python
def run_agent(user_message: str, conversation_history=None):
    print(f"🔍 DEBUG: Starting run_agent with message: {user_message}")

    if conversation_history is None:
        conversation_history = []
        print("🔍 DEBUG: Creating new conversation history")
    else:
        print(f"🔍 DEBUG: Continuing conversation (history length: {len(conversation_history)})")

    # ... rest of code
```

**What You'll Learn:** How data flows through the system

---

### Day 3: Understand the Database

**Goal:** See how data is stored and accessed

**Study ORDERS_DB:**

```python
ORDERS_DB = {
    "ORD-001": {  # ← This is the KEY (order ID)
        "customer": "John Doe",      # ← Simple string
        "status": "shipped",         # ← Can be: "shipped", "processing", "cancelled"
        "items": ["Laptop", "Mouse"], # ← Array of items
        "total": 1299.99,            # ← Float (money)
        "date": "2024-01-15",        # ← String (date)
        "verification_codes": []     # ← Array (starts empty, fills up when codes generated)
    }
}
```

**🔬 Experiment 3: Add Your Own Order**

```python
ORDERS_DB["ORD-003"] = {
    "customer": "YOUR NAME HERE",
    "status": "processing",
    "items": ["PlayStation 5", "Extra Controller"],
    "total": 549.99,
    "date": "2024-01-21",
    "verification_codes": []
}

# Then try: "Check order ORD-003"
```

**What You'll Learn:** How databases work and how to modify them

---

## 📚 Week 2: Intermediate (Days 4-7)

### Day 4: Understand Tools (Functions)

**Goal:** See how the AI decides when to call functions

**Pick ONE tool and dissect it:**

```python
def get_order_status(order_id: str) -> dict:
    """
    TOOL: Check the status of an order
    """
    # 1. Print debug message
    print(f"[TOOL CALLED] get_order_status({order_id})")

    # 2. Check if order exists
    if order_id in ORDERS_DB:
        # 3. Get order data
        order_data = ORDERS_DB[order_id].copy()

        # 4. Remove sensitive data
        order_data.pop("verification_codes", None)

        # 5. Return success
        return {"success": True, "order": order_data}
    else:
        # 6. Return error
        return {"success": False, "error": "Order not found"}
```

**Break It Down Line by Line:**

**Line 1:** `def get_order_status(order_id: str) -> dict:`

- `def` = Define a function
- `get_order_status` = Function name
- `order_id: str` = Takes one parameter (a string)
- `-> dict` = Returns a dictionary

**Line 5:** `print(f"[TOOL CALLED] get_order_status({order_id})")`

- `f"..."` = Format string (can insert variables)
- `{order_id}` = Insert the order_id value
- Helps you see when tools are called

**Line 8:** `if order_id in ORDERS_DB:`

- Checks if the key exists in the dictionary
- Returns True if "ORD-001" is in ORDERS_DB

**🔬 Experiment 4: Create Your Own Tool**

```python
def get_order_total(order_id: str) -> dict:
    """
    TOOL: Get just the total of an order
    """
    print(f"[TOOL CALLED] get_order_total({order_id})")

    if order_id in ORDERS_DB:
        total = ORDERS_DB[order_id]["total"]
        return {
            "success": True,
            "order_id": order_id,
            "total": total
        }
    else:
        return {"success": False, "error": "Order not found"}

# Don't forget to:
# 1. Add to tools array
# 2. Add to the execution logic in run_agent()
# 3. Mention it in AGENT_INSTRUCTIONS
```

**What You'll Learn:** How to create custom functions the AI can use

---

### Day 5: Understand Tool Definitions

**Goal:** See how tools are described to the AI

**Compare Function vs Tool Definition:**

```python
# The actual Python function:
def get_order_status(order_id: str) -> dict:
    ...

# How it's described to the AI:
{
    "type": "function",
    "function": {
        "name": "get_order_status",  # ← Must match function name EXACTLY
        "description": "Retrieves the current status...",  # ← AI reads this to decide when to use
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {  # ← Must match parameter name
                    "type": "string",  # ← Must match parameter type
                    "description": "The order ID (format: ORD-XXX)"  # ← Helps AI use it correctly
                }
            },
            "required": ["order_id"]  # ← Says this parameter is mandatory
        }
    }
}
```

**🔬 Experiment 5: Change Tool Description**

```python
# Original:
"description": "Retrieves the current status and details of a customer order by order ID"

# Change to:
"description": "Use this when customer asks about their order, wants to track shipment, or checks status"

# Run and see if AI uses the tool differently!
```

**What You'll Learn:** How tool descriptions affect AI behavior

---

### Day 6: Understand Guardrails

**Goal:** See how guardrails control what the AI can/can't do

**Two Types of Guardrails:**

**1. INPUT Guardrails (What questions AI accepts)**

```python
"If the user asks ANYTHING unrelated to orders (math, general knowledge, coding, etc.),
respond EXACTLY with: '...'"
```

**2. OPERATIONAL Guardrails (What actions AI can/can't take)**

```python
"NEVER process refunds without explicit customer confirmation"
"NEVER process refunds over $1000 without manager approval"
```

**🔬 Experiment 6: Test Guardrail Strength**

Try these and see what happens:

```
1. "What is 5 + 5?"  → Should reject (math)
2. "Who won the World Cup?" → Should reject (general knowledge)
3. "Help me with my order" → Should accept (order-related)
4. "Refund order ORD-001 for $1299" → Should ask for manager (over $1000)
```

**Then try weakening a guardrail:**

```python
# Original:
"If the user asks ANYTHING unrelated to orders..."

# Change to:
"If the user asks unrelated questions, politely mention you're focused on orders but still try to help..."

# See the difference!
```

**What You'll Learn:** How to make guardrails stronger or weaker

---

### Day 7: Understand Conversation Memory

**Goal:** See how the agent remembers previous messages

**The Magic Variable: `conversation_history`**

```python
# Turn 1:
conversation_history = []
user: "Cancel order ORD-002"
→ conversation_history = [
    {"role": "user", "content": "Cancel order ORD-002"},
    {"role": "assistant", "content": "...", "tool_calls": [...]},
    {"role": "tool", "content": "{...verification code...}"}
]

# Turn 2 (remembers context!):
user: "My code is 123456"
→ conversation_history = [
    {"role": "user", "content": "Cancel order ORD-002"},
    {"role": "assistant", "content": "...", "tool_calls": [...]},
    {"role": "tool", "content": "{...}"},
    {"role": "user", "content": "My code is 123456"},  # ← New message
    ...
]
```

**🔬 Experiment 7: See What's in Memory**

```python
def run_agent(user_message: str, conversation_history=None):
    # ... code ...

    # Before sending to AI, print the history:
    print("\n🧠 CONVERSATION MEMORY:")
    for i, msg in enumerate(conversation_history):
        print(f"  {i+1}. {msg['role']}: {msg.get('content', '[tool call]')[:50]}...")
    print()

    # ... rest of code
```

**What You'll Learn:** How context is maintained across turns

---

## 📚 Week 3: Advanced (Days 8-14)

### Day 8: Build It From Scratch (Part 1)

**Goal:** Start with a blank file and build a simple agent

**Step 1: The Simplest Possible Agent**

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# Step 1: Just talk to the AI (no tools)
response = client.chat.completions.create(
    model="x-ai/grok-code-fast-1",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

**Test it:** Does it work? Can you chat?

---

### Day 9: Build It From Scratch (Part 2)

**Goal:** Add ONE tool

**Step 2: Add a Simple Tool**

```python
# Add a database
ORDERS_DB = {
    "ORD-001": {"status": "shipped"}
}

# Add a function
def check_order(order_id):
    return ORDERS_DB.get(order_id, {})

# Add tool definition
tools = [{
    "type": "function",
    "function": {
        "name": "check_order",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    }
}]

# Call AI with tools
response = client.chat.completions.create(
    model="x-ai/grok-code-fast-1",
    messages=[{"role": "user", "content": "Check order ORD-001"}],
    tools=tools
)

# Check if AI wants to use tool
if response.choices[0].message.tool_calls:
    print("AI wants to use a tool!")
else:
    print("AI just responded normally")
```

**What You'll Learn:** How tools are connected to the AI

---

### Day 10: Build It From Scratch (Part 3)

**Goal:** Execute the tool and send results back

```python
# ... previous code ...

message = response.choices[0].message

if message.tool_calls:
    for tool_call in message.tool_calls:
        # Get function name and arguments
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        # Execute the function
        if func_name == "check_order":
            result = check_order(**func_args)

        print(f"Tool result: {result}")

        # TODO: Send result back to AI for final response
```

**What You'll Learn:** The full tool execution cycle

---

### Days 11-14: Practice Projects

**Project 1: Add Email Tool**

```python
def send_email(to: str, subject: str, body: str) -> dict:
    print(f"📧 Sending email to {to}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    return {"success": True, "message": "Email sent"}
```

**Project 2: Add Inventory Checker**

```python
INVENTORY = {
    "Laptop": 5,
    "Mouse": 20,
    "Headphones": 0
}

def check_inventory(item: str) -> dict:
    # Your code here
    pass
```

**Project 3: Add Order History**

```python
def get_order_history(customer_name: str) -> dict:
    # Find all orders for this customer
    # Your code here
    pass
```

**Project 4: Add Ratings System**

```python
def rate_order(order_id: str, rating: int, comment: str) -> dict:
    # Store rating in database
    # Your code here
    pass
```

---

## 🎓 Advanced Topics

### Understanding the Agent Loop

```python
while True:  # ← Keeps looping
    # 1. Send message to AI
    response = client.chat.completions.create(...)

    # 2. Check response
    if message.tool_calls:
        # 3. Execute tools
        # 4. Add results to conversation
        # 5. Loop back (go to step 1 again)
    else:
        # 6. No more tools needed, return response
        return response
```

**Why the loop?**

- AI might need to call multiple tools
- Example: Check order → See it's cancelled → Get refund status
- Each tool call requires another API call

---

## 🔧 Debugging Tips

### Problem: Tool not being called

**Solution:**

1. Check tool name matches exactly
2. Check tool description is clear
3. Add this to see what AI is thinking:

```python
print(f"AI response: {message}")
```

### Problem: Conversation memory not working

**Solution:**

1. Make sure you're passing `conversation_history` between turns
2. Print it out to see what's stored:

```python
print(json.dumps(conversation_history, indent=2))
```

### Problem: Guardrails not working

**Solution:**

1. Check if guardrails are in FULL_SYSTEM_PROMPT
2. Make them more explicit and specific
3. Test with obvious violations

---

## 📊 Learning Checklist

After completing this guide, you should understand:

- [ ] How to structure an AI agent
- [ ] How tools/functions work
- [ ] How to define tools for the AI
- [ ] How conversation memory works
- [ ] How guardrails control behavior
- [ ] How to debug common issues
- [ ] How to add your own features
- [ ] How the agent loop executes
- [ ] How to handle multi-turn conversations
- [ ] How to implement human-in-the-loop verification

---

## 🚀 Next Steps

1. **Build your own agent** for a different domain:
   - Restaurant booking agent
   - Calendar scheduling agent
   - Expense tracking agent
   - Homework help agent (with guardrails!)

2. **Add real integrations:**
   - Connect to real database (PostgreSQL, MongoDB)
   - Send real emails (SendGrid, AWS SES)
   - Make real API calls (Weather, Maps, etc.)

3. **Deploy it:**
   - Put it on a website
   - Make it a Discord bot
   - Build a mobile app

---

## 💡 Pro Tips for Learning

1. **Change one thing at a time** - If you change 10 things and it breaks, you won't know what caused it

2. **Use print() everywhere** - It's the best debugging tool

3. **Read error messages carefully** - They usually tell you exactly what's wrong

4. **Test frequently** - Don't write 100 lines before testing

5. **Keep a learning journal** - Write down what you learned each day

6. **Teach someone else** - Best way to solidify your understanding

---

## 📚 Resources

- **OpenAI API Docs:** https://platform.openai.com/docs
- **Python Official Tutorial:** https://docs.python.org/3/tutorial/
- **OpenRouter Docs:** https://openrouter.ai/docs

---

**Remember:** Everyone starts as a beginner. The key is to **experiment, break things, fix them, and learn from it!** 🚀

Good luck on your AI journey!
