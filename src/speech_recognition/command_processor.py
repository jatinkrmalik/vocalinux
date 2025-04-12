"""
Command processor for Vocalinux.

This module processes text commands from speech recognition, such as
"new line", "period", etc.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommandProcessor:
    """
    Processes text commands in speech recognition results.
    
    This class handles special commands like "new line", "period",
    "delete that", etc.
    """
    
    def __init__(self):
        """Initialize the command processor."""
        # Map of command phrases to their actions
        self.text_commands = {
            # Line commands
            "new line": "\n",
            "new paragraph": "\n\n",
            
            # Punctuation
            "period": ".",
            "full stop": ".",
            "comma": ",",
            "question mark": "?",
            "exclamation mark": "!",
            "exclamation point": "!",
            "semicolon": ";",
            "colon": ":",
            "dash": "-",
            "hyphen": "-",
            "underscore": "_",
            "quote": "\"",
            "single quote": "'",
            "open parenthesis": "(",
            "close parenthesis": ")",
            "open bracket": "[",
            "close bracket": "]",
            "open brace": "{",
            "close brace": "}",
        }
        
        # Special action commands that don't directly map to text
        self.action_commands = {
            "delete that": "delete_last",
            "scratch that": "delete_last",
            "undo": "undo",
            "redo": "redo",
            "select all": "select_all",
            "select line": "select_line",
            "select word": "select_word",
            "select paragraph": "select_paragraph",
            "cut": "cut",
            "copy": "copy",
            "paste": "paste",
        }
        
        # Formatting commands that modify the next word
        self.format_commands = {
            "capitalize": "capitalize_next",
            "uppercase": "capitalize_next",
            "all caps": "uppercase_next",
            "lowercase": "lowercase_next",
            "no spaces": "no_spaces_next",
        }
        
        # Active format modifiers
        self.active_formats = set()
        
        # Compile regex patterns for faster matching
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for command matching."""
        # Create regex pattern for text commands
        text_cmd_pattern = r'\b(' + '|'.join(re.escape(cmd) for cmd in self.text_commands.keys()) + r')\b'
        self.text_cmd_regex = re.compile(text_cmd_pattern, re.IGNORECASE)
        
        # Create regex pattern for action commands
        action_cmd_pattern = r'\b(' + '|'.join(re.escape(cmd) for cmd in self.action_commands.keys()) + r')\b'
        self.action_cmd_regex = re.compile(action_cmd_pattern, re.IGNORECASE)
        
        # Create regex pattern for format commands
        format_cmd_pattern = r'\b(' + '|'.join(re.escape(cmd) for cmd in self.format_commands.keys()) + r')\b'
        self.format_cmd_regex = re.compile(format_cmd_pattern, re.IGNORECASE)
    
    def process_text(self, text: str) -> Tuple[str, List[str]]:
        """
        Process text commands in the recognized text.
        
        Args:
            text: The recognized text to process
            
        Returns:
            Tuple of (processed_text, actions)
            - processed_text: The text with commands replaced
            - actions: List of special actions to perform
        """
        if not text:
            return "", []
        
        logger.debug(f"Processing commands in text: {text}")
        
        # Convert to lowercase for easier matching
        lower_text = text.lower()
        processed_text = text
        actions = []
        
        # Process action commands first (delete that, undo, etc.)
        action_matches = self.action_cmd_regex.findall(lower_text)
        for match in action_matches:
            action = self.action_commands[match]
            actions.append(action)
            # Remove the command from the text
            processed_text = re.sub(r'\b' + re.escape(match) + r'\b', '', processed_text, flags=re.IGNORECASE)
        
        # Process format commands
        format_matches = self.format_cmd_regex.findall(lower_text)
        for match in format_matches:
            action = self.format_commands[match]
            self.active_formats.add(action)
            # Remove the command from the text
            processed_text = re.sub(r'\b' + re.escape(match) + r'\b', '', processed_text, flags=re.IGNORECASE)
        
        # Apply active format modifiers to the next word
        if self.active_formats:
            # Find the next word
            word_match = re.search(r'\b(\w+)\b', processed_text)
            if word_match:
                word = word_match.group(1)
                start, end = word_match.span(1)
                
                # Apply formatting
                formatted_word = word
                for format_type in self.active_formats:
                    if format_type == "capitalize_next":
                        formatted_word = formatted_word.capitalize()
                    elif format_type == "uppercase_next":
                        formatted_word = formatted_word.upper()
                    elif format_type == "lowercase_next":
                        formatted_word = formatted_word.lower()
                    elif format_type == "no_spaces_next":
                        # This will be applied when combining with the next word
                        pass
                
                # Replace the word in the text
                processed_text = processed_text[:start] + formatted_word + processed_text[end:]
            
            # Clear active formats
            self.active_formats.clear()
        
        # Finally, process text commands (period, comma, etc.)
        def replace_command(match):
            cmd = match.group(0).lower()
            replacement = self.text_commands.get(cmd, "")
            return replacement
        
        processed_text = self.text_cmd_regex.sub(replace_command, processed_text)
        
        # Clean up multiple spaces
        processed_text = re.sub(r'\s+', ' ', processed_text).strip()
        
        return processed_text, actions