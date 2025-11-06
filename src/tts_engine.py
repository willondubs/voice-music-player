#!/usr/bin/env python3
"""
TTS Engine
Text-to-speech using Piper binary
"""

import logging
import subprocess
import os
import tempfile


class TTSEngine:
    """Text-to-speech engine using Piper"""
    
    def __init__(self, config):
        """Initialize TTS engine"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get Piper settings
        self.piper_binary = config['piper']['binary_path']
        self.piper_model = config['piper']['model_path']
        self.piper_config = config['piper']['config_path']
        self.output_raw = config['piper'].get('output_raw', True)
        
        # Verify Piper binary exists
        if not os.path.exists(self.piper_binary):
            self.logger.warning(f"Piper binary not found at {self.piper_binary}")
            self.enabled = False
        elif not os.path.exists(self.piper_model):
            self.logger.warning(f"Piper model not found at {self.piper_model}")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info("TTS engine initialized with Piper")
            
            # Make sure binary is executable
            try:
                os.chmod(self.piper_binary, 0o755)
            except Exception as e:
                self.logger.warning(f"Could not set execute permission on Piper: {e}")
    
    def speak(self, text):
        """
        Speak text using Piper TTS
        
        Args:
            text: Text to speak
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            self.logger.warning("TTS is not enabled")
            return False
        
        if not text:
            return False
        
        self.logger.info(f"Speaking: '{text}'")
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                output_file = tmp_file.name
            
            # Build Piper command
            cmd = [
                self.piper_binary,
                '--model', self.piper_model,
                '--config', self.piper_config,
                '--output_file', output_file
            ]
            
            # Run Piper with text as input
            result = subprocess.run(
                cmd,
                input=text.encode('utf-8'),
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                self.logger.error(f"Piper error: {result.stderr.decode()}")
                return False
            
            # Play the audio file using aplay
            play_cmd = ['aplay', '-q', '-D', 'hw:0,0', output_file]
            play_result = subprocess.run(
                play_cmd,
                capture_output=True,
                timeout=30
            )
            
            # Clean up
            try:
                os.unlink(output_file)
            except:
                pass
            
            if play_result.returncode != 0:
                self.logger.error(f"aplay error: {play_result.stderr.decode()}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error("TTS timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error in TTS: {e}", exc_info=True)
            return False
    
    def play_error_beep(self):
        """Play an error beep sound"""
        if not self.config['commands']['error_beep_enabled']:
            return
        
        try:
            # Generate a low tone beep using speaker-test
            cmd = [
                'speaker-test',
                '-t', 'sine',
                '-f', '400',  # 400 Hz
                '-l', '1',     # Play once
                '-p', '100000' # Very short duration
            ]
            
            subprocess.run(
                cmd,
                capture_output=True,
                timeout=2
            )
            
        except Exception as e:
            self.logger.debug(f"Error playing beep: {e}")
    
    def test(self):
        """
        Test TTS functionality
        
        Returns:
            bool: True if TTS is working
        """
        if not self.enabled:
            return False
        
        return self.speak("Text to speech test")
