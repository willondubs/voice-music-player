#!/usr/bin/env python3
"""
Audio Manager
Handles all audio input/output operations including recording and playback
"""

import pyaudio
import wave
import numpy as np
import logging
import subprocess
import tempfile
from io import BytesIO


class AudioManager:
    """Manages audio input and output"""
    
    def __init__(self, config):
        """Initialize audio manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio parameters
        self.mic_card = config['audio']['mic_card']
        self.mic_device = config['audio']['mic_device']
        self.mic_channels = config['audio']['mic_channels']
        self.mic_rate = config['audio']['mic_rate']
        self.chunk_size = config['audio']['chunk_size']
        
        # Initialize PyAudio
        self.pyaudio = pyaudio.PyAudio()
        
        # Since asound.conf routes the default device to ps3eye_dsnoop,
        # we can just use the default input device
        self.mic_device_index = self._find_default_input()
        
        if self.mic_device_index is None:
            raise RuntimeError("Could not find default input device")
        
        self.logger.info(f"Using input device index: {self.mic_device_index}")
        
        # Stream for wake word detection (kept open)
        self.wakeword_stream = None
    
    def _find_default_input(self):
        """Find the default input device"""
        # First check if there's a specific device index in config
        device_index = self.config['audio'].get('mic_device_index')
        if device_index is not None:
            return device_index
        
        # Look for 'pulse' device first (better channel handling)
        for i in range(self.pyaudio.get_device_count()):
            try:
                info = self.pyaudio.get_device_info_by_index(i)
                name = info.get('name', '').lower()
                if name == 'pulse' and info.get('maxInputChannels', 0) > 0:
                    self.logger.info(f"Found pulse input device at index {i}")
                    return i
            except:
                continue
        
        # Look for 'default' device
        for i in range(self.pyaudio.get_device_count()):
            try:
                info = self.pyaudio.get_device_info_by_index(i)
                name = info.get('name', '').lower()
                if name == 'default' and info.get('maxInputChannels', 0) > 0:
                    self.logger.info(f"Found default input device at index {i}")
                    return i
            except:
                continue
        
        # If no 'default' found, use PyAudio's default
        try:
            default_info = self.pyaudio.get_default_input_device_info()
            device_index = default_info['index']
            self.logger.info(f"Using PyAudio default input: {default_info.get('name')}")
            return device_index
        except:
            pass
        
        # Last resort: find any input device
        for i in range(self.pyaudio.get_device_count()):
            try:
                info = self.pyaudio.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    self.logger.warning(f"Using fallback input device: {info.get('name')}")
                    return i
            except:
                continue
        
        return None

    
    def open_wakeword_stream(self):
        """Open a continuous stream for wake word detection"""
        if self.wakeword_stream is not None:
            return self.wakeword_stream
        
        try:
            # Porcupine requires MONO audio (1 channel)
            # The default device is routed through dsnoop via asound.conf
            # so multiple streams can be open simultaneously
            self.wakeword_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,  # Porcupine needs mono
                rate=self.mic_rate,
                input=True,
                input_device_index=self.mic_device_index,
                frames_per_buffer=self.chunk_size
            )
            self.logger.info("Wake word stream opened (using dsnoop via default device)")
            return self.wakeword_stream
        except Exception as e:
            self.logger.error(f"Failed to open wake word stream: {e}")
            raise
    
    def read_audio_chunk(self):
        """Read a chunk of audio from the wake word stream"""
        try:
            if self.wakeword_stream is None:
                self.open_wakeword_stream()
            
            audio_chunk = self.wakeword_stream.read(
                self.chunk_size,
                exception_on_overflow=False
            )
            return audio_chunk
        except Exception as e:
            self.logger.error(f"Error reading audio chunk: {e}")
            return None
    
    def record_audio(self, timeout=3.0):
        """
        Record audio for voice command recognition
        
        Args:
            timeout: Maximum recording time in seconds
            
        Returns:
            Mono audio data as bytes, or None if no audio
        """
        self.logger.info(f"Recording audio (timeout: {timeout}s)...")
        
        # With dsnoop (via default device), both streams can be open simultaneously
        # No need to close the wake word stream
        
        try:
            # Open a stream for recording (4 channels for better quality)
            # Uses the same default device which routes through dsnoop
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.mic_channels,
                rate=self.mic_rate,
                input=True,
                input_device_index=self.mic_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            num_chunks = int(self.mic_rate / self.chunk_size * timeout)
            
            # Record audio
            for i in range(num_chunks):
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    self.logger.warning(f"Error reading audio frame: {e}")
                    continue
            
            stream.stop_stream()
            stream.close()
            
            # Wake word stream stays open - no need to reopen
            
            if not frames:
                self.logger.warning("No audio frames recorded")
                return None
            
            # Convert multi-channel to mono
            audio_data = b''.join(frames)
            mono_audio = self._convert_to_mono(audio_data)
            
            self.logger.info(f"Recorded {len(mono_audio)} bytes of audio")
            return mono_audio
            
        except Exception as e:
            self.logger.error(f"Error recording audio: {e}", exc_info=True)
            return None
    
    def _convert_to_mono(self, audio_data):
        """
        Convert multi-channel audio to mono
        
        Args:
            audio_data: Raw audio bytes (16-bit, multi-channel)
            
        Returns:
            Mono audio bytes
        """
        if self.mic_channels == 1:
            return audio_data
        
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Reshape to (samples, channels)
            audio_array = audio_array.reshape(-1, self.mic_channels)
            
            # Average across channels
            mono_array = np.mean(audio_array, axis=1, dtype=np.int16)
            
            # Convert back to bytes
            return mono_array.tobytes()
            
        except Exception as e:
            self.logger.error(f"Error converting to mono: {e}")
            
            # Fallback: use ffmpeg
            return self._convert_to_mono_ffmpeg(audio_data)
    
    def _convert_to_mono_ffmpeg(self, audio_data):
        """
        Convert multi-channel audio to mono using ffmpeg
        
        Args:
            audio_data: Raw audio bytes
            
        Returns:
            Mono audio bytes
        """
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f_in:
                f_in.write(audio_data)
                input_file = f_in.name
            
            with tempfile.NamedTemporaryFile(suffix='.raw', delete=False) as f_out:
                output_file = f_out.name
            
            # Run ffmpeg
            cmd = [
                'ffmpeg',
                '-f', 's16le',
                '-ar', str(self.mic_rate),
                '-ac', str(self.mic_channels),
                '-i', input_file,
                '-f', 's16le',
                '-ar', str(self.mic_rate),
                '-ac', '1',
                '-y',
                output_file
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            
            if result.returncode != 0:
                self.logger.error(f"ffmpeg error: {result.stderr.decode()}")
                return audio_data
            
            # Read converted audio
            with open(output_file, 'rb') as f:
                mono_audio = f.read()
            
            # Cleanup
            import os
            os.unlink(input_file)
            os.unlink(output_file)
            
            return mono_audio
            
        except Exception as e:
            self.logger.error(f"Error with ffmpeg conversion: {e}")
            return audio_data
    
    def play_wav_file(self, wav_path):
        """
        Play a WAV file through the default output device
        
        Args:
            wav_path: Path to WAV file
        """
        try:
            wf = wave.open(wav_path, 'rb')
            
            stream = self.pyaudio.open(
                format=self.pyaudio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Read and play audio
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
        except Exception as e:
            self.logger.error(f"Error playing WAV file: {e}")
    
    def play_raw_audio(self, audio_data, sample_rate=22050, channels=1):
        """
        Play raw audio data
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            sample_rate: Sample rate in Hz
            channels: Number of channels
        """
        try:
            stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                output=True
            )
            
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            self.logger.error(f"Error playing raw audio: {e}")
    
    def cleanup(self):
        """Cleanup audio resources"""
        try:
            if self.wakeword_stream is not None:
                self.wakeword_stream.stop_stream()
                self.wakeword_stream.close()
                self.wakeword_stream = None
            
            self.pyaudio.terminate()
            self.logger.debug("Audio manager cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during audio cleanup: {e}")
