#!/usr/bin/env python3
"""
Voice-Controlled Music Player
Main entry point for the application
"""

import os
import sys
import json
import signal
import logging
import argparse
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.wakeword_detector import WakewordDetector
from src.speech_recognizer import SpeechRecognizer
from src.command_parser import CommandParser
from src.music_controller import MusicController
from src.bluetooth_manager import BluetoothManager
from src.tts_engine import TTSEngine
from src.audio_manager import AudioManager
from src.utils import setup_logging, load_config


class VoiceMusicPlayer:
    """Main application class for voice-controlled music player"""
    
    def __init__(self, config_path='config/config.json'):
        """Initialize the voice music player"""
        self.config = load_config(config_path)
        self.running = False
        
        # Setup logging
        self.logger = setup_logging(self.config)
        self.logger.info("=" * 60)
        self.logger.info("Voice Music Player Starting")
        self.logger.info("=" * 60)
        
        # Initialize components
        try:
            self.logger.info("Initializing components...")
            
            self.audio_manager = AudioManager(self.config)
            self.tts = TTSEngine(self.config)
            self.wakeword_detector = WakewordDetector(self.config, self.audio_manager)
            self.speech_recognizer = SpeechRecognizer(self.config, self.audio_manager)
            self.bluetooth_manager = BluetoothManager(self.config)
            self.music_controller = MusicController(self.config)
            self.command_parser = CommandParser(self.config)
            
            self.logger.info("All components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}", exc_info=True)
            raise
    
    def start(self):
        """Start the voice music player"""
        self.running = True
        self.logger.info("Voice Music Player started - listening for wake word...")
        
        # Initial Bluetooth check (non-blocking)
        if self.config['bluetooth']['check_on_command']:
            self.logger.info("Performing initial Bluetooth check...")
            try:
                bt_status = self.bluetooth_manager.check_connection()
                if bt_status:
                    self.logger.info("Bluetooth speaker connected")
                else:
                    self.logger.warning("Bluetooth speaker not connected - will attempt to connect when playing music")
                    # Don't try to reconnect at startup - device may be powered off
                    # Will reconnect when first command is issued
            except Exception as e:
                self.logger.warning(f"Bluetooth check failed: {e}")
        
        try:
            while self.running:
                # Wait for wake word
                if self.wakeword_detector.detect():
                    self.logger.info("Wake word detected!")
                    self.handle_voice_command()
                    
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def handle_voice_command(self):
        """Handle a voice command after wake word detection"""
        try:
            # Announce listening
            self.tts.speak("Listening")
            
            # Record audio
            self.logger.info("Recording user command...")
            audio_data = self.audio_manager.record_audio(
                timeout=self.config['audio']['recording_timeout']
            )
            
            if audio_data is None:
                self.logger.warning("No audio recorded")
                self.tts.play_error_beep()
                return
            
            # Convert to text
            self.logger.info("Processing speech...")
            text = self.speech_recognizer.recognize(audio_data)
            
            if not text:
                self.logger.warning("No speech recognized")
                self.tts.play_error_beep()
                return
            
            self.logger.info(f"Recognized: '{text}'")
            
            # Parse command
            command = self.command_parser.parse(text)
            
            if not command:
                self.logger.warning(f"Could not parse command: '{text}'")
                self.tts.speak("I didn't understand that")
                return
            
            self.logger.info(f"Parsed command: {command}")
            
            # Check Bluetooth before music commands
            if command['type'] in ['play', 'volume', 'next', 'previous', 'pause', 'resume']:
                if self.config['bluetooth']['check_on_command']:
                    if not self.bluetooth_manager.check_connection():
                        self.logger.warning("Bluetooth not connected, attempting reconnect...")
                        self.tts.speak("Reconnecting Bluetooth")
                        if not self.bluetooth_manager.reconnect():
                            self.tts.speak("Bluetooth connection failed")
                            return
            
            # Execute command
            self.execute_command(command)
            
        except Exception as e:
            self.logger.error(f"Error handling voice command: {e}", exc_info=True)
            self.tts.speak("An error occurred")
    
    def execute_command(self, command):
        """Execute a parsed command"""
        cmd_type = command['type']
        
        try:
            if cmd_type == 'play':
                self.handle_play_command(command)
            
            elif cmd_type == 'next':
                self.music_controller.next_track()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Next")
            
            elif cmd_type == 'previous':
                self.music_controller.previous_track()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Previous")
            
            elif cmd_type == 'pause':
                self.music_controller.pause()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Paused")
            
            elif cmd_type == 'resume':
                self.music_controller.resume()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Resuming")
            
            elif cmd_type == 'stop':
                self.music_controller.stop()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Stopped")
            
            elif cmd_type == 'volume_up':
                new_vol = self.music_controller.volume_up()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak(f"Volume {new_vol}")
            
            elif cmd_type == 'volume_down':
                new_vol = self.music_controller.volume_down()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak(f"Volume {new_vol}")
            
            elif cmd_type == 'set_volume':
                level = command.get('level', 50)
                self.music_controller.set_volume(level)
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak(f"Volume {level}")
            
            elif cmd_type == 'mute':
                self.music_controller.mute()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Muted")
            
            elif cmd_type == 'unmute':
                self.music_controller.unmute()
                if self.config['commands']['confirmation_enabled']:
                    self.tts.speak("Unmuted")
            
            elif cmd_type == 'current_track':
                track_info = self.music_controller.get_current_track()
                if track_info:
                    self.tts.speak(f"Playing {track_info}")
                else:
                    self.tts.speak("Nothing is playing")
            
            elif cmd_type == 'check_bluetooth':
                if self.bluetooth_manager.check_connection():
                    self.tts.speak("Bluetooth connected")
                else:
                    self.tts.speak("Bluetooth disconnected")
            
            else:
                self.logger.warning(f"Unknown command type: {cmd_type}")
                self.tts.speak("Unknown command")
                
        except Exception as e:
            self.logger.error(f"Error executing command {cmd_type}: {e}", exc_info=True)
            self.tts.speak("Command failed")
    
    def handle_play_command(self, command):
        """Handle play commands with search or playlist"""
        query = command.get('query', '')
        play_type = command.get('play_type', 'random')  # 'random' or 'playlist'
        playlist_num = command.get('playlist_num', 1)
        
        if play_type == 'playlist':
            self.logger.info(f"Playing playlist {playlist_num} for query: {query}")
            result = self.music_controller.play_playlist(query, playlist_num)
        else:
            self.logger.info(f"Playing random track for query: {query}")
            result = self.music_controller.play_random(query)
        
        if result:
            if self.config['commands']['confirmation_enabled']:
                self.tts.speak("Playing")
        else:
            self.tts.speak("No results found")
    
    def stop(self):
        """Stop the voice music player"""
        self.logger.info("Stopping Voice Music Player...")
        self.running = False
        
        try:
            # Cleanup components
            if hasattr(self, 'wakeword_detector'):
                self.wakeword_detector.cleanup()
            if hasattr(self, 'speech_recognizer'):
                self.speech_recognizer.cleanup()
            if hasattr(self, 'audio_manager'):
                self.audio_manager.cleanup()
            
            self.logger.info("Voice Music Player stopped")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    def signal_handler(self, signum, frame):
        """Handle system signals"""
        self.logger.info(f"Received signal {signum}")
        self.stop()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Voice-Controlled Music Player')
    parser.add_argument(
        '--config',
        default='config/config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    # Change to script directory
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    
    try:
        # Initialize and start the player
        player = VoiceMusicPlayer(config_path=args.config)
        
        # Set debug mode if requested
        if args.debug:
            player.config['system']['debug_mode'] = True
            player.logger.setLevel(logging.DEBUG)
            player.logger.info("Debug mode enabled")
        
        # Register signal handlers
        signal.signal(signal.SIGINT, player.signal_handler)
        signal.signal(signal.SIGTERM, player.signal_handler)
        
        # Start the player
        player.start()
        
    except Exception as e:
        logging.error(f"Failed to start Voice Music Player: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
