#!/bin/bash
# Setup Script for Voice-Controlled Music Player
# Automates installation and configuration

set -e  # Exit on error

echo "=========================================="
echo "Voice-Controlled Music Player Setup"
echo "=========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -qi "raspberry pi" /proc/device-tree/model; then
    echo "⚠ Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Step 1: Installing System Dependencies"
echo "---------------------------------------"
sudo apt update
sudo apt install -y ffmpeg alsa-utils python3-pip python3-venv git curl wget

# Check for bluetoothctl
if ! command_exists bluetoothctl; then
    echo "Installing Bluetooth support..."
    sudo apt install -y bluez bluetooth
fi

echo "✓ System dependencies installed"
echo ""

echo "Step 2: Creating Virtual Environment"
echo "-------------------------------------"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

echo "Step 3: Installing Python Dependencies"
echo "---------------------------------------"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Python dependencies installed"
echo ""

echo "Step 4: Creating Directories"
echo "-----------------------------"
mkdir -p models tts logs
echo "✓ Directories created"
echo ""

echo "Step 5: Downloading Vosk Model"
echo "-------------------------------"
if [ ! -d "models/vosk-model-en" ]; then
    cd models
    echo "Downloading Vosk small English model..."
    wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    echo "Extracting..."
    unzip -q vosk-model-small-en-us-0.15.zip
    mv vosk-model-small-en-us-0.15 vosk-model-en
    rm vosk-model-small-en-us-0.15.zip
    cd ..
    echo "✓ Vosk model downloaded"
else
    echo "✓ Vosk model already exists"
fi
echo ""

echo "Step 6: Downloading Piper TTS"
echo "------------------------------"
if [ ! -f "tts/piper" ]; then
    cd tts
    echo "Downloading Piper for ARM64..."
    wget -q --show-progress https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
    echo "Extracting..."
    tar -xzf piper_arm64.tar.gz
    rm piper_arm64.tar.gz
    chmod +x piper
    
    echo "Downloading Piper voice model..."
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
    wget -q --show-progress https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
    cd ..
    echo "✓ Piper TTS downloaded"
else
    echo "✓ Piper TTS already exists"
fi
echo ""

echo "Step 7: Configuration"
echo "---------------------"
echo "⚠ Important: You need to configure the following:"
echo ""
echo "1. Picovoice Access Key:"
echo "   - Visit https://console.picovoice.ai/"
echo "   - Sign up for a free account"
echo "   - Get your access key"
echo "   - Edit config/config.json and add your key"
echo ""
echo "2. Bluetooth Speaker MAC:"
echo "   - Run: ./scripts/test_bluetooth.sh"
echo "   - Follow instructions to find your speaker's MAC"
echo "   - Edit config/config.json and add the MAC address"
echo ""

read -p "Press Enter to continue..."
echo ""

echo "Step 8: ALSA Configuration (Optional)"
echo "--------------------------------------"
read -p "Install ALSA configuration to /etc/asound.conf? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cp config/asound.conf /etc/asound.conf
    echo "✓ ALSA configuration installed"
    echo "⚠ You may need to reboot for changes to take effect"
else
    echo "⊘ Skipped ALSA configuration"
    echo "  You can manually copy config/asound.conf to ~/.asoundrc"
fi
echo ""

echo "Step 9: Testing"
echo "---------------"
echo "Making test scripts executable..."
chmod +x scripts/*.sh
echo "✓ Test scripts ready"
echo ""
echo "Run these tests:"
echo "  - Audio: ./scripts/test_audio.sh"
echo "  - Bluetooth: ./scripts/test_bluetooth.sh"
echo ""

read -p "Run audio test now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./scripts/test_audio.sh
fi
echo ""

echo "Step 10: Systemd Service (Optional)"
echo "------------------------------------"
read -p "Install as systemd service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update service file with current user and path
    CURRENT_USER=$(whoami)
    CURRENT_PATH=$(pwd)
    
    sed "s|/home/pi|$HOME|g" systemd/voice-music-player.service > /tmp/voice-music-player.service.tmp
    sed -i "s|User=pi|User=$CURRENT_USER|g" /tmp/voice-music-player.service.tmp
    sed -i "s|Group=pi|Group=$CURRENT_USER|g" /tmp/voice-music-player.service.tmp
    
    sudo cp /tmp/voice-music-player.service.tmp /etc/systemd/system/voice-music-player.service
    rm /tmp/voice-music-player.service.tmp
    
    sudo systemctl daemon-reload
    sudo systemctl enable voice-music-player
    
    echo "✓ Systemd service installed and enabled"
    echo ""
    echo "Service commands:"
    echo "  - Start:   sudo systemctl start voice-music-player"
    echo "  - Stop:    sudo systemctl stop voice-music-player"
    echo "  - Status:  sudo systemctl status voice-music-player"
    echo "  - Logs:    sudo journalctl -u voice-music-player -f"
else
    echo "⊘ Skipped systemd service installation"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Edit config/config.json and add:"
echo "   - Picovoice access key"
echo "   - Bluetooth speaker MAC address"
echo ""
echo "2. Ensure Mopidy is installed and configured:"
echo "   - TuneIn plugin enabled"
echo "   - Local music configured"
echo "   - Output to Snapserver FIFO: /tmp/snapfifo"
echo ""
echo "3. Ensure Snapserver and Snapclient are running"
echo ""
echo "4. Test the application:"
echo "   source venv/bin/activate"
echo "   python src/main.py --debug"
echo ""
echo "5. Or start the service:"
echo "   sudo systemctl start voice-music-player"
echo ""
echo "For help, see README.md"
echo "=========================================="
