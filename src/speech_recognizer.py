#!/usr/bin/env python3
"""
Speech Recognizer
Uses Vosk for offline speech-to-text recognition
"""

import json
import logging
from vosk import Model, KaldiRecognizer


class SpeechRecognizer:
    """Converts speech to text using Vosk"""
    
    def __init__(self, config, audio_manager):
        """Initialize speech recognizer"""
        self.config = config
        self.audio_manager = audio_manager
        self.logger = logging.getLogger(__name__)
        
        # Get Vosk settings
        model_path = config['vosk']['model_path']
        sample_rate = config['vosk']['sample_rate']
        
        try:
            # Load Vosk model
            self.logger.info(f"Loading Vosk model from {model_path}...")
            self.model = Model(model_path)
            self.logger.info("Vosk model loaded successfully")
            
            # Create recognizer
            self.recognizer = KaldiRecognizer(self.model, sample_rate)
            self.recognizer.SetMaxAlternatives(0)
            self.recognizer.SetWords(False)
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Vosk: {e}")
            raise
    
    def recognize(self, audio_data):
        """
        Recognize speech from audio data
        
        Args:
            audio_data: Raw audio bytes (mono, 16-bit PCM)
            
        Returns:
            str: Recognized text, or empty string if no speech
        """
        if not audio_data:
            return ""
        
        try:
            # Reset recognizer for new utterance
            self.recognizer = KaldiRecognizer(
                self.model,
                self.config['vosk']['sample_rate']
            )
            self.recognizer.SetMaxAlternatives(0)
            self.recognizer.SetWords(False)
            
            # Process audio
            if self.recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.recognizer.Result())
                text = result.get('text', '').strip()
            else:
                # Get partial result
                result = json.loads(self.recognizer.FinalResult())
                text = result.get('text', '').strip()
            
            if text:
                self.logger.info(f"Recognized: '{text}'")
            else:
                self.logger.warning("No speech recognized")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}", exc_info=True)
            return ""
    
    def cleanup(self):
        """Cleanup recognizer resources"""
        # Vosk doesn't require explicit cleanup
        self.logger.debug("Speech recognizer cleaned up")
