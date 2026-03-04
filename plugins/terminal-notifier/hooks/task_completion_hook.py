#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# dependencies = ["pync"]
# ///
"""
Claude Code hook for sending Mac notifications when Claude finishes responding.

This hook is designed to be used with the Stop event in Claude Code hooks configuration.
It triggers when Claude completes processing and is waiting for user input.

Uses pync for native macOS notifications that appear in the notification center.
Clicking the notification will bring your terminal to focus.

Exit codes:
- 0: Success
- 2: Blocking error (prevents Claude Code from continuing)
- Other: Non-blocking error
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from pync import Notifier
except ImportError:
    print("Error: pync not available. The script should be run with uvx.", file=sys.stderr)
    sys.exit(1)

CONFIG_FILE = Path.home() / ".claude_code_notification_config.json"
DEFAULT_CONFIG = {
    "enabled": True,
    "sound": "default",
    "title": "Claude Code",
    "subtitle": "Task Complete",
    "activate": "auto"  # "auto", "com.googlecode.iterm2", "com.mitchellh.ghostty", "com.apple.Terminal"
}

TERMINAL_APPS = {
    "iterm2": "com.googlecode.iterm2",
    "ghostty": "com.mitchellh.ghostty",
    "terminal": "com.apple.Terminal"
}

def load_config():
    """Load configuration from file or create default."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def detect_terminal():
    """Detect which terminal application launched us by walking up the process tree."""
    import os

    try:
        # Start with our own PID
        current_pid = os.getpid()

        # Walk up the process tree looking for a terminal
        max_depth = 10  # Prevent infinite loops
        for _ in range(max_depth):
            # Get parent process info using ps
            result = subprocess.run(
                ["ps", "-p", str(current_pid), "-o", "ppid=,comm="],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                break

            output = result.stdout.strip()
            if not output:
                break

            parts = output.split(None, 1)
            if len(parts) < 2:
                break

            parent_pid = parts[0].strip()
            process_name = parts[1].strip() if len(parts) > 1 else ""

            # Check if this is a terminal we recognize
            if "ghostty" in process_name.lower():
                return TERMINAL_APPS["ghostty"]
            elif "iterm" in process_name.lower() or "iTerm" in process_name:
                return TERMINAL_APPS["iterm2"]
            elif "Terminal" in process_name:
                return TERMINAL_APPS["terminal"]

            # Move up to parent
            current_pid = parent_pid

            # Stop if we hit init (PID 1)
            if current_pid == "1":
                break

    except Exception as e:
        print(f"Error detecting terminal from process tree: {e}", file=sys.stderr)

    # Default to Terminal if we couldn't detect
    return TERMINAL_APPS["terminal"]

def send_notification(title, message, subtitle=None, sound=None, activate=None):
    """Send a macOS notification using pync with Claude icon."""
    kwargs = {
        "title": title,
        "message": message,
        "appIcon": "https://claude.ai/favicon.ico"
    }

    if subtitle:
        kwargs["subtitle"] = subtitle

    if sound and sound != "none":
        kwargs["sound"] = sound

    if activate:
        if activate == "auto":
            activate = detect_terminal()
        kwargs["activate"] = activate

    try:
        Notifier.notify(**kwargs)
        return True
    except Exception as e:
        print(f"Error sending notification: {e}", file=sys.stderr)
        return False

def extract_task_info(hook_data):
    """Extract relevant task information from the hook data."""
    if isinstance(hook_data, dict):
        # Try to get message from data
        data = hook_data.get("data", {})
        if isinstance(data, dict):
            message = data.get("message", "")
            if message:
                # Truncate if too long
                if len(message) > 100:
                    return message[:100] + "..."
                return message

    return "Ready for input"

def main():
    config = load_config()

    # If notifications are disabled, exit successfully
    if not config.get("enabled", True):
        sys.exit(0)

    # Read JSON input from stdin
    hook_data = {}
    if not sys.stdin.isatty():
        try:
            input_text = sys.stdin.read()
            if input_text:
                hook_data = json.loads(input_text)
        except json.JSONDecodeError:
            # If it's not JSON, treat it as plain text for backwards compatibility
            hook_data = {"data": {"message": input_text}}
        except Exception as e:
            print(f"Error reading input: {e}", file=sys.stderr)
            # Non-blocking error
            sys.exit(1)

    # Extract task information from the hook data
    task_info = extract_task_info(hook_data)

    # Format the notification message
    timestamp = datetime.now().strftime("%I:%M %p")
    message = f"Task completed at {timestamp}"

    if task_info and task_info != "Ready for input":
        message = f"{timestamp}: {task_info}"

    # Send the notification
    success = send_notification(
        title=config.get("title", "Claude Code"),
        message=message,
        subtitle=config.get("subtitle", "Waiting for input..."),
        sound=config.get("sound", "default"),
        activate=config.get("activate", "auto")
    )

    # Exit with appropriate code
    # 0 = success, anything else = non-blocking error
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
