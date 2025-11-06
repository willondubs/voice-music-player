#!/usr/bin/env python3
"""
Command Parser
Parses voice commands using regex patterns
"""

import re
import logging


class CommandParser:
    """Parses natural language commands into structured data"""
    
    def __init__(self, config):
        """Initialize command parser"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Define command patterns
        self.patterns = self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns for command matching"""
        return [
            # Play commands with "random"
            {
                'pattern': re.compile(
                    r'play\s+(.+?)\s+random',
                    re.IGNORECASE
                ),
                'type': 'play',
                'extract': lambda m: {
                    'query': m.group(1).strip(),
                    'play_type': 'random'
                }
            },
            
            # Play commands with "playlist [number]"
            {
                'pattern': re.compile(
                    r'play\s+(.+?)\s+playlist\s+(\d+)',
                    re.IGNORECASE
                ),
                'type': 'play',
                'extract': lambda m: {
                    'query': m.group(1).strip(),
                    'play_type': 'playlist',
                    'playlist_num': int(m.group(2))
                }
            },
            
            # Play commands (general)
            {
                'pattern': re.compile(
                    r'play\s+(.+)',
                    re.IGNORECASE
                ),
                'type': 'play',
                'extract': lambda m: {
                    'query': m.group(1).strip(),
                    'play_type': 'random'
                }
            },
            
            # Next/Skip
            {
                'pattern': re.compile(
                    r'\b(next|skip)\b',
                    re.IGNORECASE
                ),
                'type': 'next',
                'extract': lambda m: {}
            },
            
            # Previous
            {
                'pattern': re.compile(
                    r'\b(previous|back|last)\b',
                    re.IGNORECASE
                ),
                'type': 'previous',
                'extract': lambda m: {}
            },
            
            # Pause
            {
                'pattern': re.compile(
                    r'\b(pause|hold|wait)\b',
                    re.IGNORECASE
                ),
                'type': 'pause',
                'extract': lambda m: {}
            },
            
            # Resume
            {
                'pattern': re.compile(
                    r'\b(resume|continue|unpause)\b',
                    re.IGNORECASE
                ),
                'type': 'resume',
                'extract': lambda m: {}
            },
            
            # Stop
            {
                'pattern': re.compile(
                    r'\bstop\b',
                    re.IGNORECASE
                ),
                'type': 'stop',
                'extract': lambda m: {}
            },
            
            # Volume up
            {
                'pattern': re.compile(
                    r'volume\s+up|louder|increase\s+volume',
                    re.IGNORECASE
                ),
                'type': 'volume_up',
                'extract': lambda m: {}
            },
            
            # Volume down
            {
                'pattern': re.compile(
                    r'volume\s+down|quieter|decrease\s+volume|lower\s+volume',
                    re.IGNORECASE
                ),
                'type': 'volume_down',
                'extract': lambda m: {}
            },
            
            # Set volume to specific level
            {
                'pattern': re.compile(
                    r'(?:set\s+)?volume\s+(?:to\s+)?(\d+)',
                    re.IGNORECASE
                ),
                'type': 'set_volume',
                'extract': lambda m: {
                    'level': int(m.group(1))
                }
            },
            
            # Mute
            {
                'pattern': re.compile(
                    r'\bmute\b',
                    re.IGNORECASE
                ),
                'type': 'mute',
                'extract': lambda m: {}
            },
            
            # Unmute
            {
                'pattern': re.compile(
                    r'\bunmute\b',
                    re.IGNORECASE
                ),
                'type': 'unmute',
                'extract': lambda m: {}
            },
            
            # What's playing?
            {
                'pattern': re.compile(
                    r'what(?:\'?s|\s+is)\s+(?:playing|this)',
                    re.IGNORECASE
                ),
                'type': 'current_track',
                'extract': lambda m: {}
            },
            
            # Check Bluetooth
            {
                'pattern': re.compile(
                    r'check\s+bluetooth|bluetooth\s+status',
                    re.IGNORECASE
                ),
                'type': 'check_bluetooth',
                'extract': lambda m: {}
            },
        ]
    
    def parse(self, text):
        """
        Parse a voice command text
        
        Args:
            text: Voice command text
            
        Returns:
            dict: Parsed command with 'type' and other parameters, or None if no match
        """
        if not text:
            return None
        
        text = text.strip()
        self.logger.debug(f"Parsing: '{text}'")
        
        # Try each pattern
        for pattern_def in self.patterns:
            match = pattern_def['pattern'].search(text)
            if match:
                command = {'type': pattern_def['type']}
                command.update(pattern_def['extract'](match))
                
                self.logger.info(f"Matched pattern: {pattern_def['type']}")
                return command
        
        # No pattern matched
        self.logger.warning(f"No pattern matched for: '{text}'")
        return None
    
    def get_supported_commands(self):
        """
        Get list of supported command types
        
        Returns:
            list: List of command types
        """
        return list(set(p['type'] for p in self.patterns))
