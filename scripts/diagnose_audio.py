#!/usr/bin/env python3
"""
Audio Device Diagnostic
Find which device actually works for wake word detection
"""

import pyaudio
import struct
import pvporcupine

ACCESS_KEY = "M3yNxgXslqTlFyd9Krh4z0AGCT7r7P70II12AuHhQfgO8Zu+ykZL6w=="

def list_all_devices():
    """List ALL PyAudio devices"""
    pa = pyaudio.PyAudio()
    print("\n" + "="*60)
    print("ALL PYAUDIO DEVICES:")
    print("="*60)
    
    for i in range(pa.get_device_count()):
        try:
            info = pa.get_device_info_by_index(i)
            print(f"\nDevice {i}:")
            print(f"  Name: {info['name']}")
            print(f"  Max Input Channels: {info['maxInputChannels']}")
            print(f"  Max Output Channels: {info['maxOutputChannels']}")
            print(f"  Default Sample Rate: {info['defaultSampleRate']}")
        except Exception as e:
            print(f"Device {i}: Error - {e}")
    
    pa.terminate()

def test_device(device_index):
    """Test if a device works for wake word detection"""
    print(f"\n{'='*60}")
    print(f"TESTING DEVICE {device_index}")
    print("="*60)
    
    pa = pyaudio.PyAudio()
    
    try:
        info = pa.get_device_info_by_index(device_index)
        print(f"Device name: {info['name']}")
        print(f"Max channels: {info['maxInputChannels']}")
    except:
        print("Could not get device info")
        pa.terminate()
        return False
    
    # Initialize Porcupine
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=["computer"],
            sensitivities=[0.5]
        )
        print(f"✓ Porcupine initialized (needs {porcupine.frame_length} samples at {porcupine.sample_rate}Hz)")
    except Exception as e:
        print(f"✗ Failed to initialize Porcupine: {e}")
        pa.terminate()
        return False
    
    # Try to open stream
    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=porcupine.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=porcupine.frame_length
        )
        print(f"✓ Stream opened successfully")
    except Exception as e:
        print(f"✗ Failed to open stream: {e}")
        porcupine.delete()
        pa.terminate()
        return False
    
    # Try to read audio
    print("\nTesting audio read (10 frames)...")
    success = True
    for i in range(10):
        try:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            
            # Check audio level
            max_val = max(abs(x) for x in pcm)
            print(f"  Frame {i+1}: max amplitude = {max_val}", end='')
            
            if result >= 0:
                print(" - WAKE WORD DETECTED!")
                break
            else:
                print()
                
        except Exception as e:
            print(f"✗ Error reading frame {i+1}: {e}")
            success = False
            break
    
    stream.stop_stream()
    stream.close()
    porcupine.delete()
    pa.terminate()
    
    return success

def main():
    print("\nAudio Device Diagnostic Tool")
    print("="*60)
    
    # List all devices
    list_all_devices()
    
    # Test specific devices
    print("\n" + "="*60)
    print("TESTING DEVICES")
    print("="*60)
    
    pa = pyaudio.PyAudio()
    device_count = pa.get_device_count()
    pa.terminate()
    
    # Test input devices
    input_devices = []
    pa = pyaudio.PyAudio()
    for i in range(device_count):
        try:
            info = pa.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(i)
        except:
            pass
    pa.terminate()
    
    print(f"\nFound {len(input_devices)} input devices: {input_devices}")
    print("\nTesting each device...")
    
    working_devices = []
    for dev_idx in input_devices:
        if test_device(dev_idx):
            working_devices.append(dev_idx)
            print(f"✓ Device {dev_idx} works!")
        else:
            print(f"✗ Device {dev_idx} failed")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if working_devices:
        print(f"✓ Working devices: {working_devices}")
        print(f"\nRECOMMENDATION: Use device index {working_devices[0]}")
        print(f"Add to config.json: \"mic_device_index\": {working_devices[0]}")
    else:
        print("✗ No working devices found")

if __name__ == "__main__":
    main()
