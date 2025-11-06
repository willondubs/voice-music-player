# Quick Start Guide

Get your Voice-Controlled Music Player running in 15 minutes!

## Prerequisites Checklist

- [ ] Raspberry Pi 4 with Raspberry Pi OS (64-bit)
- [ ] Sony PS3 Eye USB microphone plugged in
- [ ] Bluetooth speaker paired and connected
- [ ] Mopidy installed and configured
- [ ] Snapcast (snapserver + snapclient) installed
- [ ] Internet connection

## Installation Steps

### 1. Run Setup Script (5 minutes)

```bash
cd voice-music-player
chmod +x setup.sh
./setup.sh
```

Follow the prompts. The script will:
- Install system dependencies
- Create Python virtual environment
- Download Vosk speech model (~40 MB)
- Download Piper TTS binary and voice
- Configure ALSA (optional)
- Set up systemd service (optional)

### 2. Get Picovoice Access Key (2 minutes)

1. Visit: https://console.picovoice.ai/
2. Sign up (free)
3. Copy your Access Key
4. Edit `config/config.json`:
   ```json
   "access_key": "YOUR_KEY_HERE"
   ```

### 3. Configure Bluetooth (3 minutes)

```bash
# Find your speaker's MAC address
bluetoothctl
> scan on
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
> exit

# Add MAC to config
nano config/config.json
```

Update:
```json
"speaker_mac": "XX:XX:XX:XX:XX:XX"
```

### 4. Test It! (5 minutes)

```bash
# Activate virtual environment
source venv/bin/activate

# Run in debug mode
python src/main.py --debug
```

Say: **"Computer"** (wake word)
Then: **"Play music"** or any command

## Voice Commands

### Music Playback
- "Play [artist] random" - Play random track
- "Play [playlist] playlist 1" - Play specific playlist
- "Next" - Skip to next track
- "Previous" - Go to previous track
- "Pause" - Pause playback
- "Resume" - Resume playback
- "Stop" - Stop playback

### Volume Control
- "Volume up" - Increase volume
- "Volume down" - Decrease volume
- "Set volume 50" - Set to specific level
- "Mute" - Mute audio
- "Unmute" - Unmute audio

### Information
- "What's playing?" - Get current track info
- "Check bluetooth" - Check Bluetooth status

## Common Issues

### Wake word not detected
```bash
# Test microphone
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 3 test.wav
aplay test.wav
```

### No audio output
```bash
# Check Snapclient
sudo systemctl status snapclient

# Check Bluetooth
bluetoothctl info XX:XX:XX:XX:XX:XX
```

### Speech not recognized
```bash
# Verify Vosk model
ls -la models/vosk-model-en/

# Check logs
tail -f logs/voice-music-player.log
```

## Running as Service

```bash
# Start service
sudo systemctl start voice-music-player

# Check status
sudo systemctl status voice-music-player

# View logs
sudo journalctl -u voice-music-player -f

# Stop service
sudo systemctl stop voice-music-player
```

## File Locations

```
voice-music-player/
├── config/config.json       # Main configuration
├── src/main.py              # Application entry point
├── logs/                    # Log files
├── models/vosk-model-en/    # Speech recognition model
└── tts/                     # Text-to-speech files
```

## Next Steps

1. **Customize wake word**: Visit Picovoice Console
2. **Add playlists**: Configure in Mopidy
3. **Adjust sensitivity**: Edit config.json
4. **Enable auto-start**: Install systemd service
5. **Fine-tune audio**: Adjust ALSA configuration

## Tips

- Speak clearly and wait for "Listening" confirmation
- Keep background noise minimal for better recognition
- Check logs when troubleshooting: `tail -f logs/voice-music-player.log`
- Test Bluetooth before each session: `bluetoothctl info <MAC>`
- Use debug mode during setup: `python src/main.py --debug`

## Architecture Overview

```
Wake Word (Porcupine) → TTS "Listening" (Piper) → Record Audio (PyAudio)
    ↓
Speech-to-Text (Vosk) → Parse Command → Execute
    ↓
Check Bluetooth → Control Mopidy → Play via Snapcast → Bluetooth Speaker
```

## Support Resources

- **Detailed Installation**: See INSTALL.md
- **Full Documentation**: See README.md
- **Test Scripts**: 
  - `./scripts/test_audio.sh`
  - `./scripts/test_bluetooth.sh`

## Performance

- Wake word detection: ~50ms
- Speech recognition: 1-3s
- Command execution: <500ms
- **Total response time**: 2-4s

Perfect for bathroom use! 🎵

---

**Need Help?**
- Check logs: `tail -f logs/voice-music-player.log`
- Debug mode: `python src/main.py --debug`
- Test audio: `./scripts/test_audio.sh`
- Test Bluetooth: `./scripts/test_bluetooth.sh`
