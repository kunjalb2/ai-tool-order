#!/usr/bin/env python3
"""Update SYSTEM_PROMPT in api.py to include user information"""

import sys
import os

# Read the api.py file
api_file = sys.argv[1]
if len(sys.argv) > 2:
    api_file = sys.argv[1]

with open(api_file, 'r') as f:
    content = f.read()

# Find SYSTEM_PROMPT start and end
lines = content.split('\n')
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if i >= 330 and i <= 340:
        if line.startswith("SYSTEM_PROMPT = "):
            if start_idx is None:
                start_idx = i
            end_idx = i + 1
    elif i >= 340 and i <= 345:
                end_idx = i

    # Extract user info from database.py models
    if start_idx is not None and end_idx is not None:
        # Found the SYSTEM_PROMPT block - replace it
        prompt_start = lines[start_idx]
        prompt_end = lines[end_idx]
        old_prompt = '\n'.join(lines[prompt_start:prompt_end+1])

        # Import models
        sys.path.insert(0, os.path.dirname(os.path.abspath(api_file)))
        from database import User, Order

        # Parse user information
        # Current format: Name: {current_user.get('name', 'Guest')}
        user_info = ""
        if current_user and isinstance(current_user, dict):
            user_info = f"\n- Name: {current_user.get('name', 'Guest')}\n- Email: {current_user.get('email', 'Not provided')}"
        elif current_user and isinstance(current_user, User):
            user_info = f"\n- Name: {current_user.name}\n- Email: {current_user.email}"
        # Build new prompt
        new_prompt = old_prompt.replace("{", "}", user_info)
        # Write back
        with open(api_file, 'w') as f:
            f.write(new_prompt)
            print(f"Updated api.py with user context in SYSTEM_PROMPT")
    else:
        print("No SYSTEM_PROMPT found or file structure has changed. Please check manually.")
