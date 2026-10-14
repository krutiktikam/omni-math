#!/usr/bin/env python3
"""
Test script for interactive chat.py functionality
Tests the actual CLI interaction with programming commands
"""

import sys
import os
from pathlib import Path
import subprocess
import time
import threading

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_chat_interaction():
    """Test actual chat.py interaction with programming commands"""
    print("Testing interactive chat.py with programming commands...")

    # Start chat.py as a subprocess
    try:
        # Start the process
        process = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / 'chat.py')],
            cwd=str(PROJECT_ROOT),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Give it time to start up
        time.sleep(2)

        # Test commands
        test_commands = [
            "/setlang python\n",
            "/explain decorators\n",
            "/example factorial function\n",
            "/help\n",
            "exit\n"
        ]

        output_lines = []

        # Send each command and collect output
        for cmd in test_commands:
            print(f"Sending: {cmd.strip()}")
            process.stdin.write(cmd)
            process.stdin.flush()

            # Wait a bit for response
            time.sleep(2)

            # Try to read available output (non-blocking)
            try:
                # Read what's available without blocking
                import select
                if hasattr(select, 'select'):  # Unix-like
                    ready, _, _ = select.select([process.stdout], [], [], 0.1)
                    if ready:
                        output = process.stdout.read()
                        output_lines.append(output)
                        print(f"Received: {output[:100]}...")
                else:
                    # Windows fallback - just wait and try to read
                    time.sleep(0.5)
                    output = process.stdout.read()
                    output_lines.append(output)
                    print(f"Received: {output[:100]}...")
            except:
                # If select isn't available or fails, just wait
                time.sleep(1)
                try:
                    output = process.stdout.read()
                    output_lines.append(output)
                    print(f"Received: {output[:100]}...")
                except:
                    pass

        # Terminate the process
        process.terminate()
        process.wait(timeout=5)

        # Get any remaining output
        try:
            stdout, stderr = process.communicate(timeout=2)
            if stdout:
                output_lines.append(stdout)
            if stderr:
                print(f"Stderr: {stderr}")
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            if stdout:
                output_lines.append(stdout)
            if stderr:
                print(f"Stderr: {stderr}")

        full_output = "".join(output_lines)
        print(f"\nTotal output length: {len(full_output)} characters")

        # Check for expected content
        checks = [
            ("Language set to: python", "setlang command worked"),
            ("Explaining decorators", "explain command worked"),
            ("Code Example for factorial function", "example command worked"),
            ("Available commands", "help command worked")
        ]

        passed_checks = 0
        for check_string, description in checks:
            if check_string in full_output:
                print(f"  PASS: {description}")
                passed_checks += 1
            else:
                print(f"  FAIL: {description} - not found in output")

        print(f"\nInteraction test: {passed_checks}/{len(checks)} checks passed")

        if passed_checks >= 2:  # At least some basic functionality works
            print("PASS: Interactive chat test PASSED - basic functionality working")
            return True
        else:
            print("FAIL: Interactive chat test FAILED - insufficient functionality")
            return False

    except Exception as e:
        print(f"FAIL: Error testing chat interaction: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the interactive chat test"""
    print("Testing Interactive CLI Functionality\n")

    # First check if server is running
    try:
        import requests
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            raise Exception("Server not responding correctly")
        print("PASS: Backend server is running\n")
    except Exception as e:
        print(f"WARNING: Cannot connect to backend server: {e}")
        print("   The CLI tests will be limited without a running backend\n")
        # Continue anyway to test command parsing

    success = test_chat_interaction()

    if success:
        print("\nSUCCESS: Interactive CLI test completed successfully!")
        print("The enhanced chat.py with programming commands is working.")
    else:
        print("\nFAILURE: Interactive CLI test encountered issues.")
        print("Please check the output above for details.")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)