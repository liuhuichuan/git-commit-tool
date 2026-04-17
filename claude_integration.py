"""
Claude Code integration module for the Git Commit Review Application.
Handles communication with Claude Code CLI for code review.
"""

import subprocess
import json
import re
import time
from typing import Dict, List, Optional

class ClaudeIntegration:
    """
    Manages communication with Claude Code CLI for code review.
    """

    def __init__(self, claude_path=None):
        """
        Initialize with path to Claude Code CLI.

        Args:
            claude_path: Path to claude executable. If None, tries to find it in common locations.
        """
        # Common locations where Claude Code CLI might be installed
        common_paths = [
            "claude",  # Default in PATH
            "D:\\Program Files\\nodejs\\node_global\\claude",
            "D:\\Program Files\\nodejs\\node_global\\claude.cmd",
            "C:\\Users\\*\\AppData\\Roaming\\npm\\claude",
            "C:\\Program Files\\nodejs\\node_global\\claude",
        ]

        if claude_path is None:
            # Try to find claude in common locations
            import os
            for path in common_paths:
                # Handle wildcard in path
                if '*' in path:
                    import glob
                    matches = glob.glob(path)
                    if matches:
                        claude_path = matches[0]
                        break
                else:
                    if os.path.exists(path):
                        claude_path = path
                        break

            # If still not found, use default
            if claude_path is None:
                claude_path = "claude"

        self.claude_path = claude_path
        self.timeout = 300  # 5 minutes (300 seconds)

    def is_claude_available(self):
        """
        Check if Claude Code CLI is available in the system.

        Returns:
            bool: True if available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.claude_path, "--version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def review_diff(self, diff_content: str, repo_path: str = None) -> Dict:
        """
        Send diff content to Claude Code CLI for review.

        Args:
            diff_content: Git diff output to review
            repo_path: Path to git repository (enables Claude to read files for context)

        Returns:
            dict: Review results with structure:
            {
                "can_commit": bool,
                "issues": List[str],
                "confidence": "high"|"medium"|"low",
                "error": str (if any)
            }
        """
        if not self.is_claude_available():
            return {
                "can_commit": True,
                "issues": ["Claude Code CLI not available"],
                "confidence": "low",
                "error": "Claude Code CLI not found in PATH"
            }

        # Create a prompt for Claude Code CLI
        # Debug: Verify diff_content is not None or empty
        if diff_content is None:
            print("DEBUG: diff_content is None")
            return {
                "can_commit": True,
                "issues": ["diff_content is None"],
                "confidence": "low",
                "error": "No diff content provided to Claude"
            }

        if not isinstance(diff_content, str):
            print(f"DEBUG: diff_content is not a string: {type(diff_content)}")
            return {
                "can_commit": True,
                "issues": [f"diff_content is not a string: {type(diff_content)}"],
                "confidence": "low",
                "error": "diff_content must be a string"
            }

        if len(diff_content.strip()) == 0:
            print("DEBUG: diff_content is empty string")
            return {
                "can_commit": True,
                "issues": ["diff_content is empty string"],
                "confidence": "low",
                "error": "No diff content provided to Claude"
            }

        # Print debug info about the diff content
        print(f"DEBUG: diff_content length: {len(diff_content)}")
        print(f"DEBUG: diff_content first 100 chars: {diff_content[:100]}")
        print(f"DEBUG: diff_content last 100 chars: {diff_content[-100:] if len(diff_content) > 100 else diff_content}")

        # Claude Code CLI requires the prompt as stdin for --print mode, not as command line argument
        # This is the correct way to use --print according to the help documentation

        # Store repo_path for file access
        self.repo_path = repo_path

        if repo_path:
            prompt = """You are a code review assistant with file system access. Please analyze the following git diff and provide feedback.

You have Read and Grep tools available, and access to the repository directory. Please use these tools to:
- Read the full files mentioned in the diff to understand context
- Search for related code patterns or dependencies
- Verify if the changes align with existing codebase patterns

Analyze for:
1. Compilation/build errors (syntax errors, missing imports, type errors)
2. Logic issues (bugs, incorrect behavior)
3. Code quality concerns (naming, complexity, duplication)
4. Security risks (hardcoded secrets, injection vulnerabilities)
5. Git commit best practices (commit message format, unnecessary changes)
6. Contextual issues (breaking changes, API compatibility, missing tests)

Respond with JSON format:
{
  "can_commit": true|false,
  "issues": ["issue description 1", "issue description 2", ...],
  "confidence": "high"|"medium"|"low"
}

Git diff:
""" + diff_content
        else:
            prompt = """You are a code review assistant. Please analyze the following git diff and provide feedback.

Note: You do not have file system access in this mode, so you can only analyze the diff itself.

Analyze for:
1. Compilation/build errors (syntax errors, missing imports, type errors)
2. Logic issues (bugs, incorrect behavior)
3. Code quality concerns (naming, complexity, duplication)
4. Security risks (hardcoded secrets, injection vulnerabilities)
5. Git commit best practices (commit message format, unnecessary changes)

Respond with JSON format:
{
  "can_commit": true|false,
  "issues": ["issue description 1", "issue description 2", ...],
  "confidence": "high"|"medium"|"low"
}

Git diff:
""" + diff_content

        try:
            # Call Claude Code CLI with --print flag and enable file access if repo_path is provided
            if repo_path:
                # --add-dir: allow Claude to read files in the git repository
                # --allowedTools: enable Read and Grep tools so Claude can inspect context
                result = subprocess.run(
                    [self.claude_path, "--print", "--add-dir", repo_path, "--allowedTools", "Read,Grep"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )
            else:
                # No file access - just use --print
                result = subprocess.run(
                    [self.claude_path, "--print"],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

            if result.returncode != 0:
                return {
                    "can_commit": True,
                    "issues": [f"Claude Code CLI error: {result.stderr}"],
                    "confidence": "low",
                    "error": result.stderr
                }

            # Parse the response as JSON
            response_text = result.stdout.strip()

            # Debug: Print the raw response (can be removed later)
            print(f"DEBUG: Claude Response:\n{response_text}\n")

            # Try multiple JSON extraction strategies
            review_data = None

            # Strategy 1: Try to find JSON object in the response
            json_match = re.search(r'\{[^{}]*"can_commit"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    review_data = json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            # Strategy 2: Try to parse entire response as JSON
            if review_data is None:
                try:
                    review_data = json.loads(response_text)
                except json.JSONDecodeError:
                    pass

            # Strategy 3: Look for JSON code block
            if review_data is None:
                code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if code_block_match:
                    try:
                        review_data = json.loads(code_block_match.group(1))
                    except json.JSONDecodeError:
                        pass

            # If all strategies failed, return error with raw response
            if review_data is None:
                return {
                    "can_commit": True,
                    "issues": ["Failed to parse Claude Code response as JSON", "Raw response:", response_text[:500]],
                    "confidence": "low",
                    "error": f"Invalid JSON format in response. First 200 chars: {response_text[:200]}"
                }

            # Validate response structure
            if not isinstance(review_data, dict):
                return {
                    "can_commit": True,
                    "issues": ["Invalid response format from Claude Code"],
                    "confidence": "low",
                    "error": "Response is not a JSON object"
                }

            # Ensure required fields exist
            can_commit = review_data.get("can_commit", True)
            issues = review_data.get("issues", [])
            confidence = review_data.get("confidence", "medium")

            # Validate confidence level
            if confidence not in ["high", "medium", "low"]:
                confidence = "medium"

            return {
                "can_commit": bool(can_commit),
                "issues": list(issues) if isinstance(issues, list) else [str(issues)],
                "confidence": confidence,
                "error": None
            }

        except json.JSONDecodeError:
            return {
                "can_commit": True,
                "issues": ["Failed to parse Claude Code response as JSON"],
                "confidence": "low",
                "error": "Invalid JSON format in response"
            }
        except subprocess.TimeoutExpired:
            return {
                "can_commit": True,
                "issues": ["Claude Code review timed out after 30 seconds", "Try reducing the size of your changes or splitting into smaller commits"],
                "confidence": "low",
                "error": "Review timeout"
            }
        except Exception as e:
            return {
                "can_commit": True,
                "issues": [f"Unexpected error: {str(e)}"],
                "confidence": "low",
                "error": str(e)
            }