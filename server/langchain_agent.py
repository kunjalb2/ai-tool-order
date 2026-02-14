"""
AI AGENT - Simple Version (Minimal LangChain Dependencies)
===========================================================
This version uses minimal LangChain to avoid version conflicts.
It's more compatible across different LangChain versions.
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from dotenv import load_dotenv
import os
import json
import random
import string

load_dotenv()

# ============================================================================
# SETUP
# ============================================================================

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

llm = ChatOpenAI(
    model="x-ai/grok-code-fast-1",
    openai_api_key=api_key,
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.7,
)

# ============================================================================
# DATABASE
# ============================================================================

ORDERS_DB = {
    "ORD-001": {
        "customer": "John Doe",
        "status": "shipped",
        "items": ["Laptop", "Mouse"],
        "total": 1299.99,
        "date": "2024-01-15",
        "verification_codes": [],
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
# TOOLS
# ============================================================================


@tool
def get_order_status(order_id: str) -> dict:
    """Retrieves order status by order ID."""
    print(f"[TOOL CALLED] get_order_status({order_id})")
    if order_id in ORDERS_DB:
        order_data = ORDERS_DB[order_id].copy()
        order_data.pop("verification_codes", None)
        return {"success": True, "order": order_data}
    return {"success": False, "error": "Order not found"}


@tool
def process_refund(order_id: str, reason: str) -> dict:
    """Processes a refund for an order."""
    print(f"[TOOL CALLED] process_refund({order_id}, {reason})")
    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}
    order = ORDERS_DB[order_id]
    return {
        "success": True,
        "refund_amount": order["total"],
        "message": f"Refund of ${order['total']} processed",
        "refund_id": f"REF-{order_id}",
    }


@tool
def generate_cancellation_code(order_id: str) -> dict:
    """Generate verification code for order cancellation."""
    print(f"[TOOL CALLED] generate_cancellation_code({order_id})")
    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}
    code = "".join(random.choices(string.digits, k=6))
    ORDERS_DB[order_id]["verification_codes"].append(code)
    print(f"[CODE GENERATED] {code} for {order_id}")
    return {
        "success": True,
        "message": "Code generated",
        "code": code,
        "order_id": order_id,
    }


@tool
def cancel_order_with_verification(order_id: str, verification_code: str) -> dict:
    """Cancel order using verification code."""
    print(
        f"[TOOL CALLED] cancel_order_with_verification({order_id}, {verification_code})"
    )
    if order_id not in ORDERS_DB:
        return {"success": False, "error": "Order not found"}
    order = ORDERS_DB[order_id]
    if verification_code in order["verification_codes"]:
        order["status"] = "cancelled"
        order["verification_codes"].remove(verification_code)
        return {
            "success": True,
            "message": f"Order {order_id} cancelled",
            "refund_amount": order["total"],
        }
    return {"success": False, "error": "Invalid verification code"}


# Convert tools to LangChain format
tools = [
    get_order_status,
    process_refund,
    generate_cancellation_code,
    cancel_order_with_verification,
]

# Bind tools to LLM (this works across all LangChain versions)
llm_with_tools = llm.bind_tools(tools)

# ============================================================================
# SYSTEM PROMPT
# ============================================================================

SYSTEM_PROMPT = """You are a customer support agent for an e-commerce company.

CANCELLATION PROCESS:
1. Call generate_cancellation_code(order_id) first
2. Ask customer for the verification code
3. Call cancel_order_with_verification(order_id, code)

GUARDRAILS:
- ONLY answer order-related questions
- For non-order questions, say: "I can only assist with order-related queries."
- NEVER process refunds over $1000 without manager approval
- ALWAYS use verification codes for cancellations
"""

# ============================================================================
# AGENT LOOP (Manual Implementation)
# ============================================================================


def run_agent(user_input: str, chat_history: list) -> tuple[str, list]:
    """
    Run the agent with manual loop implementation.
    This avoids dependency on specific LangChain versions.
    """
    # Add user message
    chat_history.append(HumanMessage(content=user_input))

    # Create messages with system prompt
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history

    # Run loop until we get a final answer
    max_iterations = 10
    for iteration in range(max_iterations):
        # Call LLM
        response = llm_with_tools.invoke(messages)

        # Check if tools were called
        if hasattr(response, "tool_calls") and response.tool_calls:
            # Add AI response to history
            chat_history.append(response)

            # Execute each tool
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                # Find and execute the tool
                tool_result = None
                for t in tools:
                    if t.name == tool_name:
                        tool_result = t.invoke(tool_args)
                        break

                # Add tool result
                tool_message = ToolMessage(
                    content=json.dumps(tool_result), tool_call_id=tool_call["id"]
                )
                chat_history.append(tool_message)

            # Update messages for next iteration
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history
        else:
            # No more tools, we have final answer
            chat_history.append(AIMessage(content=response.content))
            return response.content, chat_history

    return "Max iterations reached", chat_history


# ============================================================================
# INTERACTIVE SESSION
# ============================================================================


def interactive_session():
    """Interactive chat session."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     AI AGENT - Customer Support Bot                       ║
    ║     (Simple Version - Minimal LangChain)                  ║
    ║                                                           ║
    ║  Type 'bye', 'exit', or 'quit' to end                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    chat_history = []

    while True:
        try:
            user_input = input("\n💬 YOU: ").strip()

            if user_input.lower() in ["quit", "exit", "bye", "goodbye"]:
                print("\n👋 AGENT: Goodbye!")
                break

            if not user_input:
                print("⚠️  Please enter a message")
                continue

            # Run agent
            response, chat_history = run_agent(user_input, chat_history)
            print(f"\n🤖 AGENT: {response}")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    interactive_session()
