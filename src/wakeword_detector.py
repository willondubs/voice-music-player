#!/usr/bin/env python3
"""
Wakeword Detector
Uses Picovoice Porcupine for offline wake word detection
"""

import logging
import struct
import pvporcupine


class WakewordDetector:
    """Detects wake word using Picovoice Porcupine"""
    
    def __init__(self, config, audio_manager):
        """Initialize wake word detector"""
        self.config = config
        self.audio_manager = audio_manager
        self.logger = logging.getLogger(__name__)
        
        # Get Porcupine settings
        access_key = config['picovoice']['access_key']
        keyword_path = config['picovoice']['keyword_path']
        sensitivity = config['picovoice']['sensitivity']
        
        if access_key == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
            raise ValueError(
                "Picovoice access key not configured. "
                "Get your free key from https://console.picovoice.ai/ "
                "and add it to config/config.json"
            )
        
        try:
            # Initialize Porcupine
            # Using built-in keyword "computer"
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=[keyword_path],
                sensitivities=[sensitivity]
            )
            
            self.logger.info(
                f"Porcupine initialized with keyword '{keyword_path}' "
                f"(sensitivity: {sensitivity})"
            )
            self.logger.info(f"Expected sample rate: {self.porcupine.sample_rate} Hz")
            self.logger.info(f"Expected frame length: {self.porcupine.frame_length}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Porcupine: {e}")
            raise
    
    def detect(self):
        """
        Listen for wake word detection
        
        Returns:
            bool: True if wake word detected, False otherwise
        """
        try:
            # Read audio chunk
            audio_chunk = self.audio_manager.read_audio_chunk()
            
            if audio_chunk is None:
                return False
            
            # Convert bytes to 16-bit integers
            pcm = struct.unpack_from(
                "h" * self.porcupine.frame_length,
                audio_chunk
            )
            
            # Process with Porcupine
            keyword_index = self.porcupine.process(pcm)
            
            if keyword_index >= 0:
                self.logger.info(f"Wake word detected (keyword index: {keyword_index})")
                return True
            
            return False
            
        except struct.error as e:
            # Audio chunk size mismatch - this can happen occasionally
            self.logger.debug(f"Audio chunk size mismatch: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error in wake word detection: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """Cleanup Porcupine resources"""
        try:
            if hasattr(self, 'porcupine') and self.porcupine is not None:
                self.porcupine.delete()
                self.logger.debug("Porcupine cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up Porcupine: {e}")
