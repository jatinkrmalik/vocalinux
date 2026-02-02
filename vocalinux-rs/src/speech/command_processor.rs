//! Text command processor for voice commands.

use std::collections::HashMap;

use tracing::debug;

/// Processes recognized text for special commands and formatting.
pub struct CommandProcessor {
    /// Text replacement commands (e.g., "new line" -> "\n")
    text_commands: HashMap<&'static str, &'static str>,
    /// Action commands (e.g., "delete that" -> action)
    action_commands: Vec<&'static str>,
}

impl CommandProcessor {
    pub fn new() -> Self {
        let mut text_commands = HashMap::new();

        // Punctuation
        text_commands.insert("period", ".");
        text_commands.insert("full stop", ".");
        text_commands.insert("comma", ",");
        text_commands.insert("question mark", "?");
        text_commands.insert("exclamation mark", "!");
        text_commands.insert("exclamation point", "!");
        text_commands.insert("colon", ":");
        text_commands.insert("semicolon", ";");
        text_commands.insert("apostrophe", "'");
        text_commands.insert("quote", "\"");
        text_commands.insert("open quote", "\"");
        text_commands.insert("close quote", "\"");
        text_commands.insert("open parenthesis", "(");
        text_commands.insert("close parenthesis", ")");
        text_commands.insert("open bracket", "[");
        text_commands.insert("close bracket", "]");
        text_commands.insert("hyphen", "-");
        text_commands.insert("dash", "-");
        text_commands.insert("underscore", "_");
        text_commands.insert("at sign", "@");
        text_commands.insert("hash", "#");
        text_commands.insert("hashtag", "#");
        text_commands.insert("dollar sign", "$");
        text_commands.insert("percent", "%");
        text_commands.insert("ampersand", "&");
        text_commands.insert("asterisk", "*");
        text_commands.insert("plus sign", "+");
        text_commands.insert("equals sign", "=");
        text_commands.insert("slash", "/");
        text_commands.insert("backslash", "\\");

        // Whitespace and formatting
        text_commands.insert("new line", "\n");
        text_commands.insert("newline", "\n");
        text_commands.insert("new paragraph", "\n\n");
        text_commands.insert("tab", "\t");
        text_commands.insert("space", " ");

        // Action commands that trigger special handling
        let action_commands = vec![
            "delete that",
            "scratch that",
            "undo",
            "undo that",
            "redo",
            "redo that",
            "select all",
            "copy",
            "copy that",
            "cut",
            "cut that",
            "paste",
            "paste that",
            "capitalize",
            "uppercase",
            "lowercase",
        ];

        Self {
            text_commands,
            action_commands,
        }
    }

    /// Process recognized text for commands.
    ///
    /// Returns (processed_text, list_of_actions)
    pub fn process(&self, text: &str) -> (String, Vec<String>) {
        let text_lower = text.to_lowercase();
        let mut actions = Vec::new();

        // Check for action commands first
        for &cmd in &self.action_commands {
            if text_lower.contains(cmd) {
                let action = cmd.replace(' ', "_");
                debug!("Detected action command: {}", action);
                actions.push(action);
            }
        }

        // If an action was found and it's the entire text, return empty text
        if !actions.is_empty() {
            for &cmd in &self.action_commands {
                if text_lower.trim() == cmd {
                    return (String::new(), actions);
                }
            }
        }

        // Process text commands
        let mut result = text.to_string();

        for (&command, &replacement) in &self.text_commands {
            // Case-insensitive replacement
            let pattern = regex_lite::Regex::new(&format!(r"(?i)\b{}\b", regex_lite::escape(command)))
                .unwrap_or_else(|_| regex_lite::Regex::new(command).unwrap());

            result = pattern.replace_all(&result, replacement).to_string();
        }

        // Clean up extra spaces
        let result = result
            .split_whitespace()
            .collect::<Vec<_>>()
            .join(" ");

        (result, actions)
    }

    /// Get list of available text commands
    pub fn text_commands(&self) -> Vec<&'static str> {
        self.text_commands.keys().copied().collect()
    }

    /// Get list of available action commands
    pub fn action_commands(&self) -> Vec<&'static str> {
        self.action_commands.clone()
    }
}

impl Default for CommandProcessor {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_punctuation() {
        let processor = CommandProcessor::new();
        let (text, actions) = processor.process("Hello period How are you question mark");
        assert_eq!(text, "Hello . How are you ?");
        assert!(actions.is_empty());
    }

    #[test]
    fn test_action_detection() {
        let processor = CommandProcessor::new();
        let (_, actions) = processor.process("delete that");
        assert!(actions.contains(&"delete_that".to_string()));
    }

    #[test]
    fn test_new_line() {
        let processor = CommandProcessor::new();
        let (text, _) = processor.process("First line new line Second line");
        assert!(text.contains('\n'));
    }
}
