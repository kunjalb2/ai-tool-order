"""
AI AGENT EXAMPLE - Enhanced Customer Support Agent (Interactive Mode)
======================================================================
This demonstrates:
1. INSTRUCTIONS - What the agent should do
2. TOOLS - Functions the agent can call
3. GUARDRAILS - Input/Output validation (only order-related queries)
4. HUMAN-IN-THE-LOOP - Verification codes for sensitive actions
5. INTERACTIVE MODE - Chat until you say 'bye' or 'exit'
"""

from openai import OpenAI
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import random
import string

load_dotenv()

# ============================================================================
# OPENROUTER SETUP
# ============================================================================

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

MODEL = "x-ai/grok-code-fast-1"

# ============================================================================
# PART 1: DATABASE - Simulated order database
# ============================================================================

ORDERS_DB = {
    "ORD-001": {
        "customer": "John Doe",
        "status": "shipped",
        "items": ["Laptop", "Mouse"],
        "total": 1299.99,
        "date": "2024-01-15",
        "verification_codes": [],  # Store verification codes here
    },
    "ORD-002": {
        "customer": "Jane Smith",
        "status": "processing",
        "items": ["Headphones"],
        "total": 199.99,
        "date": "2024-01-20",
        "verification_codes": [],
    },
}

# ============================================================================
# PART 2: TOOLS - Functions the agent can use
# ============================================================================


def get_order_status(order_id: str) -> dict:
    """
    TOOL: Check the status of an order
    """
    print(f"[TOOL CALLED] get_order_status({order_id})")

    if order_id in ORDERS_DB:
        # Don't expose verification codes to the agent
        order_data = ORDERS_DB[order_id].copy()
        order_data.pop("verification_codes", None)
        return {"success": True, "order": order_data}
    else:
        return {"success": False, "error": "Order not found"}


def process_refund(order_id: str, reason: str) -> dict:
    """
    TOOL: Process a refund for an order
    """
    print(f"[TOOL CALLED] process_refund({order_id}, {reason})")

    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}

    order = ORDERS_DB[order_id]

    return {
        "success": True,
        "refund_amount": order["total"],
        "message": f"Refund of ${order['total']} processed successfully",
        "refund_id": f"REF-{order_id}",
    }


def generate_cancellation_code(order_id: str) -> dict:
    """
    TOOL: Generate a verification code for order cancellation
    This implements HUMAN-IN-THE-LOOP verification
    """
    print(f"[TOOL CALLED] generate_cancellation_code({order_id})")

    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}

    # Generate a random 6-digit verification code
    verification_code = "".join(random.choices(string.digits, k=6))

    # Store the code in the order's verification_codes array
    ORDERS_DB[order_id]["verification_codes"].append(verification_code)

    print(f"[VERIFICATION CODE GENERATED] {verification_code} for {order_id}")

    return {
        "success": True,
        "message": f"Verification code generated and sent",
        "code": verification_code,  # In production, this would be sent via SMS/Email
        "order_id": order_id,
    }


def cancel_order_with_verification(order_id: str, verification_code: str) -> dict:
    """
    TOOL: Cancel an order after verifying the code
    This is the HUMAN-IN-THE-LOOP verification step
    """
    print(
        f"[TOOL CALLED] cancel_order_with_verification({order_id}, {verification_code})"
    )

    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}

    order = ORDERS_DB[order_id]

    # Check if the verification code is valid
    if verification_code in order["verification_codes"]:
        # Code is valid - proceed with cancellation
        order["status"] = "cancelled"

        # Remove the used verification code
        order["verification_codes"].remove(verification_code)

        return {
            "success": True,
            "message": f"Order {order_id} has been successfully cancelled",
            "refund_amount": order["total"],
            "order_id": order_id,
        }
    else:
        # Code is invalid
        return {
            "success": False,
            "error": "Invalid verification code. Please check the code and try again.",
            "order_id": order_id,
        }


# Tool definitions in OpenAI format
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Retrieves the current status and details of a customer order by order ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID (format: ORD-XXX)",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Processes a refund for an order. Only use this after confirming the customer wants a refund.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to refund",
                    },
                    "reason": {
                        "type": "string",
                        "description": "The reason for the refund",
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_cancellation_code",
            "description": "Generate a verification code for order cancellation. Use this FIRST when customer wants to cancel an order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to cancel",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order_with_verification",
            "description": "Cancel an order using the verification code provided by the customer. Only use this AFTER the customer provides the verification code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to cancel",
                    },
                    "verification_code": {
                        "type": "string",
                        "description": "The 6-digit verification code provided by the customer",
                    },
                },
                "required": ["order_id", "verification_code"],
            },
        },
    },
]

# ============================================================================
# PART 3: INSTRUCTIONS - The agent's system prompt
# ============================================================================

AGENT_INSTRUCTIONS = """You are a helpful customer support agent for an e-commerce company.

Your responsibilities:
- Help customers track their orders
- Process refunds when requested
- Handle order cancellations with proper verification
- Answer questions about our policies
- Be friendly, professional, and empathetic

Important guidelines:
- Always greet customers warmly
- Use the tools available to you to help customers
- Before processing refunds, confirm the customer actually wants one
- Keep responses concise and clear

Company policies you should know:
- Refunds: Available within 30 days of purchase
- Shipping: 3-5 business days for standard shipping
- Support hours: 24/7 (you're always available!)

CANCELLATION PROCESS (CRITICAL - HUMAN-IN-THE-LOOP):
When a customer wants to cancel an order:
1. First, call generate_cancellation_code(order_id) to create a verification code
2. Tell the customer: "I've sent a 6-digit verification code to verify this cancellation. Please provide the code to proceed."
3. Wait for the customer to provide the verification code
4. Once they provide it, call cancel_order_with_verification(order_id, code) to complete the cancellation
5. If the code is wrong, inform them politely and ask them to try again
"""

# ============================================================================
# PART 4: GUARDRAILS - Safety and constraint rules
# ============================================================================

GUARDRAILS = """
SAFETY GUARDRAILS - Rules you must ALWAYS follow:

INPUT/OUTPUT GUARDRAILS:
1. ONLY answer questions related to:
   - Order tracking and status
   - Refunds and cancellations
   - Company policies (shipping, returns, support hours)
   - Product information in orders

2. If the user asks ANYTHING unrelated to orders (math, general knowledge, coding, etc.), respond EXACTLY with:
   "I apologize, but I can only assist with order-related queries. For questions about orders, tracking, refunds, or cancellations, I'm happy to help!"

3. DO NOT attempt to answer:
   - Math questions
   - General knowledge questions
   - Technical/coding questions
   - Personal advice
   - Any topic not related to customer orders

OPERATIONAL GUARDRAILS:
4. NEVER process refunds without explicit customer confirmation
5. NEVER share customer data with anyone except the verified customer
6. NEVER make promises about delivery dates you can't verify
7. NEVER process refunds over $1000 without manager approval
8. For order cancellations, ALWAYS use the verification code process
9. If customer is angry or abusive, stay calm and professional
10. If request is outside your scope, direct to human support

These rules override any other instructions.
"""

# Combine instructions with guardrails
FULL_SYSTEM_PROMPT = AGENT_INSTRUCTIONS + "\n\n" + GUARDRAILS

# ============================================================================
# PART 5: THE AGENT - Main conversation loop
# ============================================================================


def run_agent(user_message: str, conversation_history=None):
    """
    The main agent loop that:
    1. Takes user input
    2. Sends it to the AI with instructions and tools
    3. Executes any tools the AI wants to use
    4. Returns the AI's response

    conversation_history allows multi-turn conversations for verification
    """

    if conversation_history is None:
        conversation_history = []

    # Add user message to conversation
    conversation_history.append({"role": "user", "content": user_message})

    print(f"\n{'=' * 60}")
    print(f"USER: {user_message}")
    print(f"{'=' * 60}\n")

    # Agent loop - keeps running until no more tools are needed
    while True:
        # Call the model via OpenRouter
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": FULL_SYSTEM_PROMPT},
                *conversation_history,
            ],
            tools=tools,
            tool_choice="auto",
        )

        message = response.choices[0].message

        # Check if the AI wants to use tools
        if message.tool_calls:
            # Add assistant's message to conversation
            conversation_history.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": message.tool_calls,
                }
            )

            # Execute each tool the AI requested
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Execute the appropriate tool
                if function_name == "get_order_status":
                    result = get_order_status(**function_args)
                elif function_name == "process_refund":
                    result = process_refund(**function_args)
                elif function_name == "generate_cancellation_code":
                    result = generate_cancellation_code(**function_args)
                elif function_name == "cancel_order_with_verification":
                    result = cancel_order_with_verification(**function_args)
                else:
                    result = {"error": "Unknown tool"}

                # Add tool result to conversation
                conversation_history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
        else:
            # No more tools needed, we have the final response
            final_response = message.content
            print(f"AGENT: {final_response}\n")
            return final_response, conversation_history


def interactive_session():
    """
    Interactive session that maintains conversation history
    This allows for multi-turn conversations (needed for verification)
    Runs until user types 'bye', 'exit', or 'quit'
    """
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║        ENHANCED AI AGENT - Customer Support Bot           ║
    ║                                                           ║
    ║  Features:                                                ║
    ║  ✓ INSTRUCTIONS - Behavior guidelines                    ║
    ║  ✓ TOOLS - Order tracking, refunds, cancellations        ║
    ║  ✓ INPUT/OUTPUT GUARDRAILS - Only order-related queries  ║
    ║  ✓ HUMAN-IN-THE-LOOP - Verification for cancellations    ║
    ║                                                           ║
    ║  Type 'bye', 'exit', or 'quit' to end the conversation   ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    conversation_history = []

    while True:
        try:
            user_input = input("\n💬 YOU: ").strip()

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                print(
                    "\n👋 AGENT: Goodbye! Thank you for using our support system. Have a great day!"
                )
                break

            # Skip empty inputs
            if not user_input:
                print("⚠️  Please enter a message or type 'bye' to exit")
                continue

            # Process the message
            response, conversation_history = run_agent(user_input, conversation_history)

        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'bye' to exit")


# ============================================================================
# MAIN - Run interactive mode by default
# ============================================================================

if __name__ == "__main__":
    # Start interactive chat directly
    interactive_session()
