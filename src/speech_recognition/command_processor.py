#!/usr/bin/env python3
"""
Command processor for Vocalinux.
"""

import logging
import re
from typing import Dict, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Define command patterns
COMMAND_PATTERNS = {
    # Navigation commands
    r"new line|newline|line break": "ACTION:NEW_LINE",
    r"tab|indent": "ACTION:TAB",
    r"(go to|goto) line (\d+)": "ACTION:GOTO_LINE:\\2",
    r"(go|move) (up|down|left|right)( (\d+))?": "ACTION:MOVE_CURSOR:\\2:\\4",
    
    # Editing commands
    r"delete( that)?|remove( that)?": "ACTION:DELETE",
    r"delete (word|line|sentence|paragraph)": "ACTION:DELETE_UNIT:\\1",
    r"delete last (word|line|sentence|paragraph)": "ACTION:DELETE_LAST_UNIT:\\1",
    r"select (word|line|sentence|paragraph)": "ACTION:SELECT_UNIT:\\1",
    r"select all": "ACTION:SELECT_ALL",
    r"copy( that)?": "ACTION:COPY",
    r"cut( that)?": "ACTION:CUT",
    r"paste": "ACTION:PASTE",
    r"undo": "ACTION:UNDO",
    r"redo": "ACTION:REDO",
    
    # Formatting commands
    r"capitalize( that)?": "ACTION:CAPITALIZE",
    r"uppercase|upper case( that)?": "ACTION:UPPERCASE",
    r"lowercase|lower case( that)?": "ACTION:LOWERCASE",
    r"bold( that)?": "ACTION:BOLD",
    r"italic|italics|italicize( that)?": "ACTION:ITALIC",
    r"underline( that)?": "ACTION:UNDERLINE",
    
    # Punctuation commands (these will be directly inserted into text)
    r"^period$|^full stop$": ".",
    r"^comma$": ",",
    r"^question mark$": "?",
    r"^exclamation point$|^exclamation mark$": "!",
    r"^colon$": ":",
    r"^semicolon$": ";",
    r"^quote$|^quotation mark$": "\"",
    r"^single quote$": "'",
    r"^open parenthesis$": "(",
    r"^close parenthesis$": ")",
    r"^open bracket$": "[",
    r"^close bracket$": "]",
    
    # Application control commands
    r"save( file)?|save document": "ACTION:SAVE",
    r"(quit|exit) application": "ACTION:QUIT",
    
    # Vocalinux-specific commands
    r"stop (listening|dictation|recording)": "ACTION:STOP_RECOGNITION",
}


class CommandProcessor:
    """
    Processes speech recognition results for commands.
    
    Detects and processes commands from speech recognition results,
    separating them from regular text input.
    """

    def __init__(self):
        """Initialize the command processor."""
        # Compile all command patterns for efficiency
        self.command_patterns = []
        for pattern, action in COMMAND_PATTERNS.items():
            self.command_patterns.append((re.compile(pattern, re.IGNORECASE), action))
        
    def process_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Process text for commands and regular input.
        
        Args:
            text: The text to process
            
        Returns:
            A tuple of (processed_text, actions)
            - processed_text: Text with commands removed
            - actions: List of action strings to perform
        """
        if not text:
            return ("", [])
            
        # Clean up the text
        text = text.strip()
        
        # Check if the text is entirely a command
        for pattern, action in self.command_patterns:
            match = pattern.match(text)
            if match and match.group(0) == text:
                # The entire text is a command
                if action.startswith("ACTION:"):
                    # This is a special action, not text
                    # Extract any parameters from the match
                    action_parts = action.split(":")
                    action_type = action_parts[1]
                    
                    # Handle parametrized actions
                    if len(action_parts) > 2:
                        # Replace captured groups in the action
                        for i, group in enumerate(match.groups(), 1):
                            if group:
                                action_parts = [
                                    p.replace(f"\\{i}", group) for p in action_parts
                                ]
                        
                        action = ":".join(action_parts)
                    
                    logger.debug(f"Command: {text} -> Action: {action}")
                    return ("", [action])
                else:
                    # This is a replacement text (e.g., punctuation)
                    logger.debug(f"Command: {text} -> Text: {action}")
                    return (action, [])
        
        # Process word by word to find partial commands
        # This is a simpler approach; more sophisticated parsing could be applied
        # for now, just return the full text
        return (text, [])
        
    def get_command_help(self) -> Dict[str, List[str]]:
        """
        Get help information for available commands.
        
        Returns:
            A dictionary of command categories and their commands
        """
        return {
            "Navigation": [
                "new line - Insert a line break",
                "tab - Insert a tab character",
                "go to line [number] - Move cursor to specified line",
                "move [up/down/left/right] [number] - Move cursor in specified direction",
            ],
            "Editing": [
                "delete/remove - Delete selected text or last word/character",
                "delete [word/line/sentence/paragraph] - Delete specified unit",
                "select [word/line/sentence/paragraph] - Select specified unit",
                "select all - Select all text",
                "copy - Copy selected text",
                "cut - Cut selected text",
                "paste - Paste from clipboard",
                "undo - Undo last action",
                "redo - Redo last undone action",
            ],
            "Formatting": [
                "capitalize - Capitalize selected text or next word",
                "uppercase/upper case - Convert to UPPERCASE",
                "lowercase/lower case - Convert to lowercase",
                "bold - Apply bold formatting",
                "italic - Apply italic formatting",
                "underline - Apply underline formatting",
            ],
            "Punctuation": [
                "period/full stop - Insert a period (.)",
                "comma - Insert a comma (,)",
                "question mark - Insert a question mark (?)",
                "exclamation point/mark - Insert an exclamation mark (!)",
                "colon - Insert a colon (:)",
                "semicolon - Insert a semicolon (;)",
                "quote/quotation mark - Insert quotation marks (\"\")",
                "single quote - Insert single quotes ('')",
                "open/close parenthesis - Insert parentheses ()",
                "open/close bracket - Insert brackets []",
            ],
            "Application Control": [
                "save/save file - Save the current file",
                "quit application - Quit the application",
                "stop listening/dictation/recording - Stop voice recognition",
            ],
        }