"""
Git integration module for the Git Commit Review Application.
Handles git repository detection, diff capture, and command execution.
"""

import os
import subprocess
import re
from pathlib import Path

class GitIntegration:
    """
    Manages git operations for the application.
    """

    def __init__(self, repo_path=None):
        """
        Initialize with repository path.

        Args:
            repo_path: Path to git repository. If None, will try current directory,
                      but won't raise error if not a git repo.
        """
        self.git_cmd = ['git']

        if repo_path is None:
            # Try current directory, but don't fail if not a git repo
            try:
                self.repo_path = self.find_git_root(os.getcwd())
            except RuntimeError:
                # Not a git repo, set to None
                self.repo_path = None
        else:
            # User specified a path, validate it
            self.repo_path = self.find_git_root(repo_path)

    def find_git_root(self, start_path):
        """
        Find the root of the git repository by searching upward from start_path.

        Args:
            start_path: Starting path to search from

        Returns:
            Path to git repository root

        Raises:
            RuntimeError: If no git repository is found
        """
        path = Path(start_path).resolve()

        while path != path.parent:
            if (path / '.git').exists():
                return str(path)
            path = path.parent

        raise RuntimeError(f"Not a git repository: {start_path}")

    def is_git_repo(self):
        """
        Check if current path is a git repository.

        Returns:
            bool: True if git repository, False otherwise
        """
        if self.repo_path is None:
            return False

        try:
            # Verify the path is still valid
            return Path(self.repo_path).exists() and (Path(self.repo_path) / '.git').exists()
        except:
            return False

    def get_git_diff(self, staged=True):
        """
        Capture git diff output.

        Args:
            staged: If True, get staged changes. If False, get all changes.

        Returns:
            str: Git diff output or None if error
        """
        try:
            if staged:
                # Get staged changes only
                result = subprocess.run(
                    self.git_cmd + ['diff', '--cached'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
            else:
                # Get all changes (staged + unstaged)
                result = subprocess.run(
                    self.git_cmd + ['diff'],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception as e:
            print(f"Error getting git diff: {e}")
            return None

    def get_git_status(self):
        """
        Get git status output.

        Returns:
            str: Git status output or None if error
        """
        try:
            result = subprocess.run(
                self.git_cmd + ['status'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return None
        except Exception as e:
            print(f"Error getting git status: {e}")
            return None

    def execute_command(self, command):
        """
        Execute a git command.

        Args:
            command: Git command as string (e.g., "commit -m \"message\"", "push origin main")

        Returns:
            dict: Result with 'success', 'output', 'error', 'return_code'
        """
        try:
            # Split command into arguments while preserving quoted strings
            import shlex
            args = shlex.split(command)

            # Ensure we're using git command
            if not args[0].lower() == 'git':
                args = ['git'] + args

            result = subprocess.run(
                args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'return_code': result.returncode
            }

        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }

    def is_commit_command(self, command):
        """
        Check if command is a git commit command.

        Args:
            command: Git command as string

        Returns:
            bool: True if commit command, False otherwise
        """
        import shlex
        args = shlex.split(command)

        # Check if command starts with git commit
        if len(args) > 0 and args[0].lower() == 'git':
            args = args[1:]

        if len(args) > 0 and args[0].lower() == 'commit':
            return True

        # Also check for just "commit"
        if len(args) > 0 and args[0].lower() == 'commit':
            return True

        return False

    def is_push_command(self, command):
        """
        Check if command is a git push command.

        Args:
            command: Git command as string

        Returns:
            bool: True if push command, False otherwise
        """
        import shlex
        args = shlex.split(command)

        # Check if command starts with git push
        if len(args) > 0 and args[0].lower() == 'git':
            args = args[1:]

        if len(args) > 0 and args[0].lower() == 'push':
            return True

        # Also check for just "push"
        if len(args) > 0 and args[0].lower() == 'push':
            return True

        return False

    def get_current_branch(self):
        """
        Get current git branch name.

        Returns:
            str: Branch name or None if error
        """
        try:
            result = subprocess.run(
                self.git_cmd + ['branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return None
        except Exception as e:
            print(f"Error getting current branch: {e}")
            return None