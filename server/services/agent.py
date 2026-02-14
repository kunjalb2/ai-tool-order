"""
Agent processing logic for chat and approval handling
"""
import asyncio
import json
import uuid
from typing import Optional, Dict, AsyncGenerator
from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import client, MODEL, SYSTEM_PROMPT, tools
from services.session_manager import session_manager
from services.tools import get_order_status, generate_cancellation_code, cancel_order_with_verification


async def process_agent_message(message: str, session_id: str, db: Session = None, current_user: Optional[Dict[str, str]] = None):
    """Process a message through the agent and emit events"""
    session = session_manager.get_session(session_id)
    if not session:
        await session_manager.emit_event(
            session_id, "error", {"message": "Session not found"}
        )
        return

    history = session["history"]

    # Add user message to history
    if message:
        history.append({"role": "user", "content": message})

    # Get current user info from session if not provided
    if not current_user and session.get("user_id"):
        current_user = {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        }

    # Add user context to system prompt if user info available
    system_prompt = SYSTEM_PROMPT
    if current_user:
        system_prompt += f"\n\nCURRENT USER CONTEXT:\n"
        system_prompt += f"- User ID: {current_user.get('id')}\n"
        system_prompt += f"- Name: {current_user.get('name')}\n"
        system_prompt += f"- Email: {current_user.get('email')}\n"

    try:
        while True:
            # Call the model
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *history,
                ],
                tools=tools,
                tool_choice="auto",
                stream=False,
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                # Add assistant message with tool calls to history
                history.append(
                    {
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in msg.tool_calls
                        ],
                    }
                )

                # Process each tool call
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    print(f"DEBUG: Calling tool {func_name} with args {func_args}")

                    if func_name == "get_order_status":
                        result = get_order_status(db, **func_args, current_user=current_user)
                        print(f"DEBUG: get_order_status result: {result}")

                    elif func_name == "generate_cancellation_code":
                        result = generate_cancellation_code(db, **func_args, current_user=current_user)
                        print(f"DEBUG: generate_cancellation_code result: {result}")

                        # If approval required, emit approval event
                        if result.get("requires_approval"):
                            order_id = result["order_id"]

                            # Store pending approval
                            session["pending_approval"] = {
                                "order_id": order_id,
                                "code": result["code"],
                                "tool_call_id": tool_call.id,
                                "user_email": result.get("user_email"),
                                "user_name": result.get("user_name"),
                            }

                            # Emit approval event
                            await session_manager.emit_event(
                                session_id,
                                "approval",
                                {
                                    "id": session_id,
                                    "message": f"A verification code has been sent to your email address for order {order_id}. Please check your email (including spam/junk folder) and enter the 6-digit code below to confirm the cancellation.",
                                    "type": "input",
                                    "placeholder": "Enter verification code from email",
                                },
                            )
                            return  # Wait for approval

                    elif func_name == "cancel_order_with_verification":
                        result = cancel_order_with_verification(db, **func_args, current_user=current_user)

                    else:
                        result = {"error": "Unknown tool"}

                    # Add tool result to history
                    history.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )

            else:
                # No tool calls, emit message
                response_text = msg.content or ""

                print(f"DEBUG: Sending message event to session {session_id}: {response_text[:50]}...")
                await session_manager.emit_event(
                    session_id,
                    "message",
                    {
                        "id": str(uuid.uuid4()),
                        "role": "assistant",
                        "content": response_text,
                        "timestamp": None,
                    },
                )

                # Add to history
                history.append({"role": "assistant", "content": response_text})

                # Emit done event
                print(f"DEBUG: Sending done event to session {session_id}")
                await session_manager.emit_event(session_id, "done", {})
                break

    except Exception as e:
        print(f"DEBUG: Exception in process_agent_message: {e}")
        import traceback
        traceback.print_exc()
        await session_manager.emit_event(session_id, "error", {"message": str(e)})


async def handle_approval(
    session_id: str, approved: bool, user_input: Optional[str] = None, db: Session = None, current_user: Optional[Dict[str, str]] = None
):
    """Handle approval response from user"""
    print(f"DEBUG: handle_approval called - session_id: {session_id}, approved: {approved}, user_input: {user_input}")

    session = session_manager.get_session(session_id)
    if not session:
        print(f"DEBUG: Session not found - {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")

    pending = session.get("pending_approval")
    if not pending:
        print(f"DEBUG: No pending approval for session {session_id}")
        await session_manager.emit_event(
            session_id, "error", {"message": "No pending approval"}
        )
        return

    history = session["history"]

    # Get current user info from session if not provided
    if not current_user and session.get("user_id"):
        current_user = {
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        }

    if approved and user_input:
        # User approved - cancel the order
        result = {
            "success": True,
            "message": "User approved cancellation",
            "verification_code": user_input,
        }

        print(f"DEBUG: Executing cancellation for order {pending['order_id']} with code {user_input}")
        # Execute the cancellation
        cancellation_result = cancel_order_with_verification(
            db, pending["order_id"], user_input, current_user=current_user
        )
        print(f"DEBUG: Cancellation result: {cancellation_result}")

        if not cancellation_result.get("success"):
            print(f"DEBUG: Cancellation failed: {cancellation_result.get('error')}")

        # Add tool result
        history.append(
            {
                "role": "tool",
                "tool_call_id": pending["tool_call_id"],
                "content": json.dumps(cancellation_result),
            }
        )

        # Clear pending approval
        session["pending_approval"] = None

        print(f"DEBUG: Continuing agent processing for session {session_id}")
        # Continue processing
        await process_agent_message("", session_id, db, current_user)

    else:
        # User rejected
        result = {
            "success": False,
            "message": "User denied cancellation",
        }

        print(f"DEBUG: User rejected cancellation")
        # Add tool result
        history.append(
            {
                "role": "tool",
                "tool_call_id": pending["tool_call_id"],
                "content": json.dumps(result),
            }
        )

        # Clear pending approval
        session["pending_approval"] = None

        # Continue processing
        await process_agent_message("", session_id, db, current_user)
