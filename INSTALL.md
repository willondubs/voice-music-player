# Installation Guide

This guide will walk you through installing and configuring the Voice-Controlled Music Player on your Raspberry Pi 4.

## Prerequisites

- Raspberry Pi 4 (hostname: snapbath recommended)
- Raspberry Pi OS (64-bit recommended for Piper TTS)
- Sony PS3 Eye USB microphone
- Bluetooth speaker
- Internet connection for initial setup
- Mopidy music server
- Snapcast for multi-room audio

## Quick Start

If you want to get up and running quickly, run the automated setup script:

```bash
cd /path/to/voice-music-player
chmod +x setup.sh
./setup.sh
```

The script will guide you through the installation process.

## Manual Installation

### 1. System Dependencies

Update your system and install required packages:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ffmpeg alsa-utils python3-pip python3-venv git curl wget bluez bluetooth
```

### 2. Clone or Copy Project

If you received this as a zip file, extract it to your home directory:

```bash
cd ~
unzip voice-music-player.zip
cd voice-music-player
```

Or clone from repository:

```bash
cd ~
git clone <repository-url> voice-music-player
cd voice-music-player
```

### 3. Python Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download Vosk Speech Recognition Model

Download the small English model (approximately 40 MB):

```bash
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-model-en
rm vosk-model-small-en-us-0.15.zip
cd ..
```

For better accuracy, you can download the larger model:

```bash
cd models
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
unzip vosk-model-en-us-0.22.zip
mv vosk-model-en-us-0.22 vosk-model-en
rm vosk-model-en-us-0.22.zip
cd ..
```

Then update `config/config.json` to point to the larger model.

### 5. Download Piper TTS

Download Piper binary and voice model:

```bash
cd tts

# Download Piper binary for ARM64
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz
rm piper_arm64.tar.gz
chmod +x piper

# Download a voice model (lessac - medium quality)
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json

cd ..
```

Other voice options are available at: https://github.com/rhasspy/piper/blob/master/VOICES.md

### 6. Get Picovoice Access Key

1. Visit https://console.picovoice.ai/
2. Sign up for a free account
3. Create a new project or use the default
4. Copy your Access Key
5. Edit `config/config.json` and replace `YOUR_PICOVOICE_ACCESS_KEY_HERE` with your key

The free tier includes 3 wake words and is sufficient for this project.

### 7. Configure Bluetooth Speaker

Find your Bluetooth speaker's MAC address:

```bash
bluetoothctl
```

In the bluetoothctl prompt:

```
power on
scan on
```

Wait for your speaker to appear in the list. Note its MAC address (format: XX:XX:XX:XX:XX:XX).

Pair and trust the device:

```
pair XX:XX:XX:XX:XX:XX
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

Edit `config/config.json` and replace `YOUR_BLUETOOTH_MAC_HERE` with your speaker's MAC address.

### 8. Configure ALSA (Audio System)

Copy the ALSA configuration:

```bash
sudo cp config/asound.conf /etc/asound.conf
```

Or for user-only configuration:

```bash
cp config/asound.conf ~/.asoundrc
```

Verify audio devices:

```bash
arecord -l  # List capture devices
aplay -l    # List playback devices
```

Test microphone:

```bash
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 3 test.wav
aplay test.wav
```

### 9. Install and Configure Mopidy

Install Mopidy:

```bash
sudo apt install mopidy mopidy-local mopidy-tunein
```

Configure Mopidy to output to Snapserver FIFO. Edit `/etc/mopidy/mopidy.conf`:

```ini
[audio]
output = audioresample ! audioconvert ! audio/x-raw,rate=48000,channels=2,format=S16LE ! wavenc ! filesink location=/tmp/snapfifo

[http]
enabled = true
hostname = 0.0.0.0
port = 6680

[local]
enabled = true
media_dir = /home/pi/Music

[tunein]
enabled = true
timeout = 10
```

Enable and start Mopidy:

```bash
sudo systemctl enable mopidy
sudo systemctl start mopidy
```

### 10. Install and Configure Snapcast

Install Snapserver and Snapclient:

```bash
# Add Snapcast repository
wget https://github.com/badaix/snapcast/releases/download/v0.27.0/snapserver_0.27.0-1_arm64.deb
wget https://github.com/badaix/snapcast/releases/download/v0.27.0/snapclient_0.27.0-1_arm64.deb

sudo dpkg -i snapserver_0.27.0-1_arm64.deb snapclient_0.27.0-1_arm64.deb
sudo apt install -f  # Fix any dependency issues
```

Configure Snapserver. Edit `/etc/snapserver.conf`:

```ini
[stream]
source = pipe:///tmp/snapfifo?name=Mopidy&mode=read
```

Create the FIFO:

```bash
mkfifo /tmp/snapfifo
```

Enable and start services:

```bash
sudo systemctl enable snapserver
sudo systemctl start snapserver
sudo systemctl enable snapclient
sudo systemctl start snapclient
```

### 11. Test the Installation

Run the test scripts:

```bash
# Test audio devices
./scripts/test_audio.sh

# Test Bluetooth connection
./scripts/test_bluetooth.sh
```

### 12. Configure the Application

Edit `config/config.json` and verify all settings:

- Picovoice access key
- Bluetooth MAC address
- Audio device indices (if needed)
- Mopidy and Snapcast addresses

### 13. Test Run

Test the application in debug mode:

```bash
source venv/bin/activate
python src/main.py --debug
```

Say "Computer" (the wake word) and then a command like "Play music".

### 14. Install as Service

To run the application automatically on boot:

```bash
sudo cp systemd/voice-music-player.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-music-player
sudo systemctl start voice-music-player
```

Check status:

```bash
sudo systemctl status voice-music-player
```

View logs:

```bash
sudo journalctl -u voice-music-player -f
```

## Troubleshooting

### Wake Word Not Detected

1. Check microphone is working:
   ```bash
   arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 5 test.wav
   aplay test.wav
   ```

2. Verify Picovoice access key is correct in config.json

3. Try adjusting sensitivity in config.json (0.0-1.0)

### Speech Recognition Not Working

1. Verify Vosk model is downloaded:
   ```bash
   ls -la models/vosk-model-en/
   ```

2. Check for ALSA errors in logs:
   ```bash
   dmesg | grep -i alsa
   ```

3. Ensure ffmpeg is installed:
   ```bash
   ffmpeg -version
   ```

### No Audio Output

1. Check Snapclient is running:
   ```bash
   sudo systemctl status snapclient
   ```

2. Verify Bluetooth is connected:
   ```bash
   bluetoothctl info <MAC>
   ```

3. Check Mopidy output configuration:
   ```bash
   cat /etc/mopidy/mopidy.conf | grep -A 5 "\\[audio\\]"
   ```

### Bluetooth Connection Issues

1. Check Bluetooth service:
   ```bash
   sudo systemctl status bluetooth
   ```

2. Reconnect manually:
   ```bash
   bluetoothctl connect <MAC>
   ```

3. Check logs:
   ```bash
   sudo journalctl -u bluetooth -f
   ```

### Service Won't Start

1. Check logs:
   ```bash
   sudo journalctl -u voice-music-player -n 50
   ```

2. Test manually:
   ```bash
   cd /home/pi/voice-music-player
   source venv/bin/activate
   python src/main.py --debug
   ```

3. Verify permissions:
   ```bash
   ls -la /home/pi/voice-music-player
   ```

## Optimization

### Performance Tuning

1. Reduce logging in production:
   - Set log level to WARNING in config.json

2. Use smaller Vosk model for faster recognition:
   - Already using vosk-model-small-en-us

3. Adjust audio chunk size:
   - Modify chunk_size in config.json (512-2048)

### Audio Quality

1. Increase Snapcast buffer:
   - Edit /etc/snapclient.conf
   - Add: `--hostID snapbath --soundcard plughw:0,0 --buffer 1000`

2. Adjust Mopidy output quality:
   - Increase sample rate in mopidy.conf

### Reliability

1. Enable watchdog timer on Raspberry Pi
2. Add monitoring with systemd service
3. Configure log rotation
4. Set up automatic Bluetooth reconnection

## Next Steps

Once installed:

1. Create custom playlists in Mopidy
2. Add more voice commands in command_parser.py
3. Customize TTS voice or messages
4. Add wake word customization via Picovoice Console
5. Integrate with home automation systems

## Support

For issues or questions:
- Check logs: `sudo journalctl -u voice-music-player -f`
- Run in debug mode: `python src/main.py --debug`
- Review README.md for command reference
- Check hardware connections

## Updates

To update the software:

```bash
cd ~/voice-music-player
git pull  # If using git
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart voice-music-player
```
