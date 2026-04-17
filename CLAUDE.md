# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

# Git Commit Review Application

A Windows desktop application that integrates with Claude Code CLI to review Git commits before they are made. The application provides a GUI for entering git commands, automatically analyzing changes with Claude, and showing feedback before execution.

## Development Commands

### Setup and Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Structure
```
git-commit-tool/
├── main.py                  # Application entry point
├── gui.py                   # PyQt5 GUI implementation
├── git_integration.py       # Git command execution and diff capture
├── claude_integration.py   # Claude Code CLI integration
├── requirements.txt         # Python dependencies
└── CLAUDE.md               # This file
```

## Architecture

### Overview
The application follows a three-layer architecture:

1. **GUI Layer (gui.py)**
   - PyQt5-based window with:
     - Repository path selector (QLineEdit + Browse button) - allows selecting any git repository directory
     - Command input field (QLineEdit) - enter git commands like "commit -m \"message\"" or "push origin main"
     - "Review Changes" button - analyzes staged changes with Claude
     - "Execute Command" button - runs the git command and displays output
     - Diff display panel (QTextEdit) - shows current staged changes
     - Feedback display panel (QTextEdit) - shows Claude's review results
     - Output terminal (QTextEdit) - shows command execution results
     - Status bar - shows repository status, current branch, and repository path

2. **Git Operations Layer (git_integration.py)**
   - GitIntegration class handles:
     - Finding git repository root (searches upward from specified directory)
     - Capturing git diffs (`git diff --cached` for staged changes)
     - Executing git commands via subprocess
     - Detecting command types (commit, push, etc.)
     - Getting current branch
     - Getting git status
     - Supports custom repository paths via constructor parameter

3. **Claude Integration Layer (claude_integration.py)**
   - ClaudeIntegration class handles:
     - Checking Claude Code CLI availability (auto-detects common installation paths)
     - Sending diff content to Claude Code with `--print` flag for non-interactive output (using stdin input)
     - Parsing JSON responses for can_commit, issues, and confidence
     - Handling timeouts (5 minutes) and errors gracefully
     - Multiple fallback strategies for extracting JSON from response
     - Comprehensive validation of diff content before sending to Claude
     - Debug logging of diff content length and content preview
     - Correct implementation: uses stdin input with --print flag (not command line argument)
     - Enhanced capability: When repository path is available, enables Claude to use Read and Grep tools to inspect file context for deeper analysis

### Key Design Patterns

- **Subprocess Pattern**: All git and claude CLI commands use Python subprocess with proper timeout handling
- **Separation of Concerns**: Each module has a single responsibility
- **Signal-based Updates**: GUI updates happen after subprocess completes (no threading complexity)
- **JSON Response Format**: Claude Code is prompted to return structured JSON for parsing

### Claude Code Integration

The application calls Claude Code CLI with a specific prompt template that:
- Asks for code review of the diff
- Looks for compilation errors, bugs, security issues
- Returns JSON with fields: `can_commit` (bool), `issues` (list), `confidence` (high/medium/low)

Example Claude prompt template:
```
Analyze for:
1. Compilation/build errors
2. Logic issues
3. Code quality concerns
4. Security risks
5. Git commit best practices

Respond with JSON format:
{
  "can_commit": true|false,
  "issues": ["issue descriptions"],
  "confidence": "high"|"medium"|"low"
}
```

**Note**: The application now includes robust JSON parsing with multiple fallback strategies to handle variations in Claude's response format, including:
- Extracting JSON from code blocks (```json ... ```)
- Searching for JSON objects containing "can_commit" field
- Parsing entire response as JSON
- Fallback to raw response preview in error messages

## Development Guidelines

### Adding New Git Commands
The current design supports any git command. To add specific command handling:
1. Add detection methods in `git_integration.py` (e.g., `is_merge_command`, `is_rebase_command`)
2. Add custom command options in `gui.py`'s `execute_command` method if needed

### Improving Claude Review
To review different aspects of changes:
1. Modify the prompt template in `claude_integration.py`'s `review_diff` method
2. Adjust expected JSON response structure
3. Update `gui.py`'s feedback display to show new data fields

### Supporting Windows Features
The application uses standard Python and PyQt5, making it Windows-compatible:
- All paths are handled via `pathlib.Path`
- Subprocess uses UTF-8 encoding for git/claude output
- Windows-specific features can use `pywin32` if needed (already in requirements.txt)

### Testing
This is a GUI application; manual testing is most effective:
1. Run `python main.py`
2. Navigate to a git repository
3. Stage some changes with `git add`
4. Click "Review Changes" to test Claude integration
5. Execute commit commands to verify output

### Known Limitations
- Claude Code CLI must be installed and in PATH
- Only staged changes are reviewed (files added with `git add`)
- Large diffs may take time to review (30 second timeout) - if this occurs, try staging smaller sets of changes or splitting large commits into multiple smaller ones
- Review is asynchronous - gui freezes during Claude call (future: add threading)

## Future Enhancements
- Add support for unstaged changes review
- Show line-by-line diff with Claude comments inline
- Add configurable review rules
- Cache Claude responses for identical diffs
- Add background review that auto-triggers on staging changes
- Support CLAUDE.md project-specific configuration in repo