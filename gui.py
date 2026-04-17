"""
GUI implementation for the Git Commit Review Application using PyQt5.
"""

import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton,
                            QVBoxLayout, QHBoxLayout, QWidget, QLineEdit,
                            QMessageBox, QLabel, QGroupBox, QFileDialog, QProgressDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QIcon
import git_integration
import claude_integration

class GitCommitReviewGUI(QMainWindow):
    """
    Main GUI application for Git commit review.
    """

    def __init__(self):
        super().__init__()

        # Initialize settings for persistent storage
        self.settings = QSettings("GitCommitReviewApp", "GitCommitReviewTool")

        # Initialize components
        try:
            self.git_integration = git_integration.GitIntegration()
            self.current_repo_path = self.git_integration.repo_path
        except RuntimeError:
            # If current directory is not a git repo, use empty path
            self.git_integration = git_integration.GitIntegration(None)
            self.current_repo_path = None

        # Initialize Claude integration with default path
        self.claude_integration = claude_integration.ClaudeIntegration()
        self.claude_path = None

        self.init_ui()
        self.load_settings()
        self.update_status()

    def init_ui(self):
        """
        Initialize the user interface.
        """
        self.setWindowTitle("Git Commit Review Tool")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Status bar
        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)

        # Repository selection group
        repo_group = QGroupBox("Git Repository")
        repo_layout = QHBoxLayout()

        self.repo_path_input = QLineEdit()
        self.repo_path_input.setPlaceholderText("Repository path (auto-detected if current directory is a git repo)")
        self.repo_path_input.textChanged.connect(self.on_repo_path_changed)
        repo_layout.addWidget(self.repo_path_input)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_repository)
        self.browse_button.setMaximumWidth(100)
        repo_layout.addWidget(self.browse_button)

        repo_group.setLayout(repo_layout)
        main_layout.addWidget(repo_group)

        # Claude CLI path group
        claude_group = QGroupBox("Claude Code CLI Path")
        claude_layout = QHBoxLayout()

        self.claude_path_input = QLineEdit()
        self.claude_path_input.setPlaceholderText("Path to claude executable (auto-detected)")
        self.claude_path_input.textChanged.connect(self.on_claude_path_changed)
        claude_layout.addWidget(self.claude_path_input)

        self.claude_browse_button = QPushButton("Browse")
        self.claude_browse_button.clicked.connect(self.browse_claude)
        self.claude_browse_button.setMaximumWidth(100)
        claude_layout.addWidget(self.claude_browse_button)

        claude_group.setLayout(claude_layout)
        main_layout.addWidget(claude_group)

        # Command input group
        command_group = QGroupBox("Git Command")
        command_layout = QVBoxLayout()

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter git command (e.g., 'commit -m \"message\"' or 'push origin main')")
        self.command_input.returnPressed.connect(self.execute_command)
        command_layout.addWidget(self.command_input)

        # Review and Execute buttons
        button_layout = QHBoxLayout()

        self.review_button = QPushButton("Review Changes")
        self.review_button.clicked.connect(self.review_changes)
        self.review_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.review_button)

        self.execute_button = QPushButton("Execute Command")
        self.execute_button.clicked.connect(self.execute_command)
        self.execute_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        button_layout.addWidget(self.execute_button)

        command_layout.addLayout(button_layout)
        command_group.setLayout(command_layout)
        main_layout.addWidget(command_group)

        # Diff preview group
        diff_group = QGroupBox("Changes to be Reviewed")
        diff_layout = QVBoxLayout()

        self.diff_display = QTextEdit()
        self.diff_display.setReadOnly(True)
        self.diff_display.setFontFamily("Courier New")
        self.diff_display.setFontPointSize(10)
        self.diff_display.setMinimumHeight(150)
        diff_layout.addWidget(self.diff_display)

        diff_group.setLayout(diff_layout)
        main_layout.addWidget(diff_group)

        # Feedback group
        feedback_group = QGroupBox("Review Feedback")
        feedback_layout = QVBoxLayout()

        self.feedback_display = QTextEdit()
        self.feedback_display.setReadOnly(True)
        self.feedback_display.setFontFamily("Courier New")
        self.feedback_display.setFontPointSize(10)
        self.feedback_display.setMinimumHeight(100)
        feedback_layout.addWidget(self.feedback_display)

        feedback_group.setLayout(feedback_layout)
        main_layout.addWidget(feedback_group)

        # Output terminal group
        output_group = QGroupBox("Command Output")
        output_layout = QVBoxLayout()

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFontFamily("Courier New")
        self.output_display.setFontPointSize(10)
        output_layout.addWidget(self.output_display)

        output_group.setLayout(output_layout)
        main_layout.addWidget(output_group)

        # Set default font for all text widgets
        font = QFont("Consolas", 10)
        self.diff_display.setFont(font)
        self.feedback_display.setFont(font)
        self.output_display.setFont(font)

        # Set minimum window size
        self.setMinimumSize(700, 600)

    def load_settings(self):
        """
        Load saved settings from QSettings
        """
        # Block signals during load
        self.repo_path_input.blockSignals(True)
        self.claude_path_input.blockSignals(True)
        self.command_input.blockSignals(True)

        try:
            # Load repo path
            repo_path = self.settings.value("repo_path", "")
            if repo_path:
                try:
                    self.git_integration = git_integration.GitIntegration(repo_path)
                    self.repo_path_input.setText(repo_path)
                except RuntimeError:
                    pass

            # Load Claude CLI path
            claude_path = self.settings.value("claude_path", "")
            if claude_path:
                self.claude_path_input.setText(claude_path)
                self.claude_integration = claude_integration.ClaudeIntegration(claude_path)

            # Load command input
            command = self.settings.value("command_input", "")
            self.command_input.setText(command)
        finally:
            self.repo_path_input.blockSignals(False)
            self.claude_path_input.blockSignals(False)
            self.command_input.blockSignals(False)

    def save_settings(self):
        """
        Save current settings to QSettings
        """
        # Save repo path
        self.settings.setValue("repo_path", self.repo_path_input.text())

        # Save Claude CLI path
        self.settings.setValue("claude_path", self.claude_path_input.text())

        # Save command input
        self.settings.setValue("command_input", self.command_input.text())

    def update_status(self):
        """
        Update the status label based on git repository state.
        """
        # Block signals to prevent infinite recursion
        self.repo_path_input.blockSignals(True)
        self.claude_path_input.blockSignals(True)

        try:
            # Check Claude CLI availability first
            claude_available = self.claude_integration.is_claude_available()
            if claude_available:
                claude_status = "Claude CLI: OK"
                claude_style = "color: #4CAF50;"
                # Update Claude path input with detected path
                if hasattr(self.claude_integration, 'claude_path'):
                    self.claude_path_input.setText(self.claude_integration.claude_path)
            else:
                claude_status = "Claude CLI: Not found"
                claude_style = "color: #f44336;"

            # Check git repository status
            if self.git_integration.repo_path is not None and self.git_integration.is_git_repo():
                branch = self.git_integration.get_current_branch()
                if branch:
                    self.status_label.setText(f"Git: {branch} | {claude_status}")
                    self.status_label.setStyleSheet(f"{claude_style} font-weight: bold;")
                    self.repo_path_input.setText(self.git_integration.repo_path)
                    self.current_repo_path = self.git_integration.repo_path
                else:
                    self.status_label.setText(f"Git: Repository | {claude_status}")
                    self.status_label.setStyleSheet(f"{claude_style} font-weight: bold;")
                    self.repo_path_input.setText(self.git_integration.repo_path)
                    self.current_repo_path = self.git_integration.repo_path
            else:
                self.status_label.setText(f"Git: Not a repository | {claude_status}")
                self.status_label.setStyleSheet(f"{claude_style} font-weight: bold;")
                self.repo_path_input.setText("")
                self.current_repo_path = None
        finally:
            # Re-enable signals
            self.repo_path_input.blockSignals(False)
            self.claude_path_input.blockSignals(False)

    def on_repo_path_changed(self, text):
        """
        Handle changes to the repository path input.
        """
        # Block signals to prevent recursion when updating status
        self.repo_path_input.blockSignals(True)

        try:
            if not text.strip():
                # Reset to current directory
                try:
                    self.git_integration = git_integration.GitIntegration(None)
                except:
                    pass
                self.update_status()
                return

            # Try to initialize with new path
            try:
                self.git_integration = git_integration.GitIntegration(text)
                self.update_status()
            except RuntimeError:
                self.status_label.setText("Status: Invalid repository path")
                self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
                self.current_repo_path = None
        finally:
            self.repo_path_input.blockSignals(False)

    def browse_repository(self):
        """
        Open file dialog to select repository directory.
        """
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Git Repository Directory",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            self.repo_path_input.setText(folder)
            self.on_repo_path_changed(folder)
            self.save_settings()

    def on_claude_path_changed(self, text):
        """
        Handle changes to the Claude CLI path input.
        """
        if not text.strip():
            # Reset to auto-detection
            self.claude_integration = claude_integration.ClaudeIntegration(None)
            self.claude_path = None
            self.save_settings()
            return

        # Try to initialize with new path
        try:
            self.claude_integration = claude_integration.ClaudeIntegration(text)
            self.claude_path = text
            # Test if available
            if not self.claude_integration.is_claude_available():
                self.status_label.setText(f"Status: Claude CLI not found at {text}")
                self.status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        except:
            self.status_label.setText("Status: Invalid Claude CLI path")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold;")
        self.save_settings()

    def browse_claude(self):
        """
        Open file dialog to select Claude CLI executable.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Claude CLI Executable",
            "",
            "Executable Files (*.exe *.cmd);;All Files (*.*)"
        )

        if file_path:
            self.claude_path_input.setText(file_path)
            self.on_claude_path_changed(file_path)

    def review_changes(self):
        """
        Review the current git changes using Claude Code.
        """
        if not self.git_integration.is_git_repo():
            QMessageBox.warning(self, "Error", "Not in a git repository")
            return

        # Check if Claude CLI is available
        if not self.claude_integration.is_claude_available():
            QMessageBox.warning(self, "Error", "Claude Code CLI not found. Please set the correct path in the Claude Code CLI Path field.")
            self.feedback_display.setText("Error: Claude Code CLI not found. Please configure the path.")
            return

        # Get staged changes for review
        diff_content = self.git_integration.get_git_diff(staged=True)

        if diff_content is None:
            self.diff_display.setText("Unable to get git diff")
            self.feedback_display.setText("Error: Could not retrieve git diff")
            return

        # Display the diff
        if not diff_content.strip():
            self.diff_display.setText("No staged changes to review")
            self.feedback_display.setText("No staged changes to review")
            return

        # Verify we have actual diff content
        if len(diff_content.strip()) < 10:
            self.diff_display.setText(diff_content)
            self.feedback_display.setText("Error: Git diff content appears to be too short or empty")
            return

        # Block signals to prevent recursion during text updates
        self.diff_display.blockSignals(True)
        self.feedback_display.blockSignals(True)

        try:
            self.diff_display.setText(diff_content)

            # Show loading dialog
            progress = QProgressDialog("Reviewing changes with Claude Code... This may take several minutes.", "Cancel", 0, 0, self)
            progress.setModal(True)
            progress.setWindowTitle("Processing...")
            progress.setCancelButton(None)  # Disable cancel button to prevent interference
            progress.setMinimumDuration(0)  # Show immediately
            progress.show()
            QApplication.processEvents()  # Ensure dialog is displayed

            # Review with Claude Code
            repo_path = self.git_integration.repo_path if self.git_integration.repo_path else None
            review_result = self.claude_integration.review_diff(diff_content, repo_path)

            # Close loading dialog
            progress.close()

            # Display results
            if review_result["error"]:
                # Show detailed error info
                error_msg = f"Error: {review_result['error']}"
                if len(review_result["issues"]) > 1 and isinstance(review_result["issues"][1], str):
                    error_msg += f"\n\nRaw response preview: {review_result['issues'][1]}"
                self.feedback_display.setText(error_msg)
            else:
                feedback_text = ""

                if review_result["can_commit"]:
                    feedback_text += "✅ <b>Can commit</b>\n\n"
                else:
                    feedback_text += "❌ <b>Cannot commit</b>\n\n"

                feedback_text += "<b>Issues found:</b>\n"

                if review_result["issues"]:
                    for issue in review_result["issues"]:
                        feedback_text += f"- {issue}\n"
                else:
                    feedback_text += "- No issues found\n"

                feedback_text += f"\n<b>Confidence:</b> {review_result['confidence'].upper()}"

                self.feedback_display.setText(feedback_text)
        finally:
            # Re-enable signals
            self.diff_display.blockSignals(False)
            self.feedback_display.blockSignals(False)

    def execute_command(self):
        """
        Execute the entered git command.
        """
        if not self.git_integration.is_git_repo():
            QMessageBox.warning(self, "Error", "Not in a git repository")
            return

        command = self.command_input.text().strip()

        if not command:
            QMessageBox.warning(self, "Error", "Please enter a git command")
            return

        # Check if it's a commit command and we have changes
        if self.git_integration.is_commit_command(command):
            diff_content = self.git_integration.get_git_diff(staged=True)
            if not diff_content or not diff_content.strip():
                reply = QMessageBox.question(self, "Confirm",
                    "No changes staged for commit. Are you sure you want to continue?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

        # Block signals to prevent recursion
        self.output_display.blockSignals(True)
        try:
            # Execute command
            self.output_display.setText(f"> {command}\n\n")

            result = self.git_integration.execute_command(command)

            # Display output
            if result["output"]:
                self.output_display.append(result["output"])

            if result["error"]:
                self.output_display.append(f"<span style='color: red;'>{result['error']}</span>")
        finally:
            self.output_display.blockSignals(False)

        # Update status
        self.update_status()

        # If it was a commit, clear the command input
        if self.git_integration.is_commit_command(command):
            self.command_input.clear()

        # Save the current command input for persistence
        self.save_settings()

        # Refresh diff display after commit
        if result["success"] and self.git_integration.is_commit_command(command):
            # Wait a moment for git to process
            import time
            time.sleep(0.5)
            self.review_changes()

    def showEvent(self, event):
        """
        Handle window show event to update status.
        """
        super().showEvent(event)
        self.update_status()

    def closeEvent(self, event):
        """
        Handle window close event.
        """
        # Save settings before closing
        self.save_settings()
        event.accept()

# Create and show the application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GitCommitReviewGUI()
    window.show()
    sys.exit(app.exec_())