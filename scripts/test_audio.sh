#!/bin/bash
# Test Audio Devices Script
# Tests microphone input and speaker output

echo "=========================================="
echo "Audio Device Testing Script"
echo "=========================================="
echo ""

# Check for required tools
if ! command -v arecord &> /dev/null; then
    echo "Error: arecord not found. Install with: sudo apt install alsa-utils"
    exit 1
fi

if ! command -v aplay &> /dev/null; then
    echo "Error: aplay not found. Install with: sudo apt install alsa-utils"
    exit 1
fi

echo "1. Listing Audio Capture Devices:"
echo "----------------------------------"
arecord -l
echo ""

echo "2. Listing Audio Playback Devices:"
echo "----------------------------------"
aplay -l
echo ""

echo "3. Testing Microphone (PS3 Eye - Card 3, Device 0):"
echo "----------------------------------------------------"
echo "Recording 3 seconds of audio..."
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 3 /tmp/test_mic.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Recording successful"
    echo "File size: $(du -h /tmp/test_mic.wav | cut -f1)"
else
    echo "✗ Recording failed"
fi
echo ""

echo "4. Testing Playback (RPi Headphone - Card 0, Device 0):"
echo "--------------------------------------------------------"
echo "Playing back recorded audio..."
aplay -D plughw:0,0 /tmp/test_mic.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Playback successful"
else
    echo "✗ Playback failed"
fi
echo ""

echo "5. Testing ALSA Configuration:"
echo "------------------------------"
if [ -f ~/.asoundrc ]; then
    echo "User ALSA config found: ~/.asoundrc"
elif [ -f /etc/asound.conf ]; then
    echo "System ALSA config found: /etc/asound.conf"
else
    echo "⚠ No ALSA configuration file found"
fi
echo ""

echo "6. Checking for ALSA Errors:"
echo "----------------------------"
dmesg | grep -i "alsa\|audio" | tail -5
echo ""

echo "7. Testing Default Devices:"
echo "---------------------------"
echo "Recording 2 seconds from default capture device..."
arecord -d 2 /tmp/test_default.wav 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Default capture works"
    echo "Playing back via default playback device..."
    aplay /tmp/test_default.wav 2>&1
    if [ $? -eq 0 ]; then
        echo "✓ Default playback works"
    else
        echo "✗ Default playback failed"
    fi
else
    echo "✗ Default capture failed"
fi
echo ""

# Cleanup
rm -f /tmp/test_mic.wav /tmp/test_default.wav

echo "=========================================="
echo "Audio testing complete!"
echo "=========================================="
