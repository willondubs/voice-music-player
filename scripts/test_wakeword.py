#!/usr/bin/env python3
"""
Test Wake Word Detection
Simple test to verify Porcupine is hearing the microphone
"""

import sys
import struct
import pyaudio
import pvporcupine

# Configuration
ACCESS_KEY = "YOUR_PICOVOICE_ACCESS_KEY_HERE"  # Replace with your key
KEYWORD = "computer"
SENSITIVITY = 0.5

def test_wakeword():
    """Test wake word detection"""
    
    print("Wake Word Detection Test")
    print("=" * 50)
    
    # Get access key from user if needed
    access_key = ACCESS_KEY
    if access_key == "YOUR_PICOVOICE_ACCESS_KEY_HERE":
        access_key = input("Enter your Picovoice access key: ").strip()
    
    print(f"\nInitializing Porcupine with keyword: '{KEYWORD}'")
    print(f"Sensitivity: {SENSITIVITY}")
    
    try:
        # Initialize Porcupine
        porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=[KEYWORD],
            sensitivities=[SENSITIVITY]
        )
        
        print(f"✓ Porcupine initialized")
        print(f"  Sample rate: {porcupine.sample_rate} Hz")
        print(f"  Frame length: {porcupine.frame_length}")
        
    except Exception as e:
        print(f"✗ Failed to initialize Porcupine: {e}")
        return
    
    # Initialize PyAudio
    pa = pyaudio.PyAudio()
    
    # List audio devices
    print("\nAvailable audio input devices:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            print(f"  [{i}] {info['name']} ({info['maxInputChannels']} channels)")
    
    # Find PS3 Eye or use default
    mic_index = None
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        name = info.get('name', '').lower()
        if 'ps3' in name or 'eye' in name:
            mic_index = i
            break
    
    if mic_index is None:
        print("\n⚠ PS3 Eye not found, using default input device")
    else:
        print(f"\n✓ Using PS3 Eye (device {mic_index})")
    
    # Open audio stream
    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=porcupine.sample_rate,
            input=True,
            input_device_index=mic_index,
            frames_per_buffer=porcupine.frame_length
        )
        
        print("✓ Audio stream opened")
        
    except Exception as e:
        print(f"✗ Failed to open audio stream: {e}")
        porcupine.delete()
        pa.terminate()
        return
    
    print("\n" + "=" * 50)
    print("Listening for wake word...")
    print(f"Say: '{KEYWORD}'")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        frame_count = 0
        while True:
            # Read audio
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            # Process with Porcupine
            result = porcupine.process(pcm)
            
            frame_count += 1
            
            # Print status every 100 frames (~3 seconds)
            if frame_count % 100 == 0:
                print(f"  Listening... ({frame_count} frames processed)")
            
            if result >= 0:
                print(f"\n🎤 WAKE WORD DETECTED! (keyword index: {result})")
                print("✓ Wake word detection is working!")
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"\n✗ Error during detection: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()
        print("\nTest complete")

if __name__ == "__main__":
    test_wakeword()
