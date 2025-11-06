# Voice-Controlled Music Player for Raspberry Pi

A Python-based voice assistant designed for bathroom use on Raspberry Pi 4. Uses offline voice recognition to control music playback through Snapcast and Mopidy.

## Hardware Requirements

- **Raspberry Pi 4** (hostname: snapbath)
- **USB Microphone**: Sony PS3 Eye (card 3, device 0; 4 channels, 16kHz, S16_LE)
- **Bluetooth Speaker** (MAC address to be configured)
- **RPi 4 Headphone Out** (card 0, device 0; plughw:0,0)
- Optional: USB speaker for shower (future enhancement)

## Features

- **Offline Operation**: All processing happens locally
- **Wakeword Detection**: "Computer" triggers listening mode
- **Voice Commands**: Play music, control volume, skip tracks, manage playlists
- **Automatic Bluetooth Management**: Checks and reconnects Bluetooth speaker
- **TuneIn Radio & Local Music**: Via Mopidy integration
- **Snapcast Integration**: Multi-room audio capability

## Software Architecture

```
┌─────────────────┐
│  Wakeword Loop  │ (Porcupine)
│   "Computer"    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   TTS Response  │ (Piper: "Listening")
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Record Audio   │ (PyAudio, 3s timeout)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Speech-to-Text │ (Vosk)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Command Parser  │ (Regex patterns)
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│   Bluetooth  │   │    Mopidy    │
│   Check      │   │   Control    │
└──────────────┘   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Snapserver  │
                   │    (FIFO)    │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Snapclient  │
                   │  (Playback)  │
                   └──────────────┘
```

## Installation

### 1. System Dependencies

```bash
sudo apt update
sudo apt install -y ffmpeg alsa-utils python3-pip python3-venv git bluetoothctl
```

### 2. Create Virtual Environment

```bash
cd /home/pi/voice-music-player
python3 -m venv venv
source venv/bin/activate
```

### 3. Python Dependencies

```bash
pip install --upgrade pip
pip install pvporcupine vosk pyaudio python-snapcast requests
```

### 4. Download Vosk Model

```bash
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 vosk-model-en
rm vosk-model-small-en-us-0.15.zip
cd ..
```

### 5. Download Piper TTS

```bash
mkdir -p tts
cd tts
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz
tar -xzf piper_arm64.tar.gz
rm piper_arm64.tar.gz
# Download a voice model
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ..
```

### 6. Get Picovoice Access Key

Visit https://console.picovoice.ai/ to get your free access key for Porcupine.
Add it to `config/config.json`.

### 7. Configure ALSA

Copy the provided `config/asound.conf` to `/etc/asound.conf` or `~/.asoundrc`:

```bash
sudo cp config/asound.conf /etc/asound.conf
```

### 8. Find Bluetooth Speaker MAC

```bash
bluetoothctl
scan on
# Wait for your speaker to appear
# Note the MAC address
pair <MAC>
trust <MAC>
connect <MAC>
exit
```

Add the MAC address to `config/config.json`.

### 9. Configure Mopidy

Ensure Mopidy is installed and configured with TuneIn and local music sources.
Configure Mopidy to output to Snapserver FIFO (`/tmp/snapfifo`).

### 10. Install Systemd Service

```bash
sudo cp systemd/voice-music-player.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable voice-music-player
sudo systemctl start voice-music-player
```

## Configuration

Edit `config/config.json` to customize:

- Picovoice access key
- Bluetooth speaker MAC address
- Audio device indices
- Mopidy server address
- Snapcast server address
- Volume step size
- Timeout values

## Voice Commands

### Playback Commands
- "Play [artist/song name] random" - Search and play random track
- "Play [playlist name] playlist [number]" - Play specific playlist
- "Next" / "Skip" - Next track
- "Previous" - Previous track
- "Pause" - Pause playback
- "Resume" / "Play" - Resume playback
- "Stop" - Stop playback

### Volume Commands
- "Volume up" - Increase volume
- "Volume down" - Decrease volume
- "Set volume [0-100]" - Set specific volume level
- "Mute" - Mute audio
- "Unmute" - Unmute audio

### System Commands
- "What's playing?" - Get current track info
- "Check bluetooth" - Check Bluetooth connection status

## File Structure

```
voice-music-player/
├── README.md
├── requirements.txt
├── setup.sh
├── config/
│   ├── config.json
│   └── asound.conf
├── src/
│   ├── main.py
│   ├── audio_manager.py
│   ├── wakeword_detector.py
│   ├── speech_recognizer.py
│   ├── command_parser.py
│   ├── music_controller.py
│   ├── bluetooth_manager.py
│   ├── tts_engine.py
│   └── utils.py
├── systemd/
│   └── voice-music-player.service
├── scripts/
│   ├── test_audio.sh
│   └── test_bluetooth.sh
├── logs/
│   └── .gitkeep
├── models/
│   └── vosk-model-en/
└── tts/
    ├── piper
    ├── en_US-lessac-medium.onnx
    └── en_US-lessac-medium.onnx.json
```

## Debugging

### Enable Debug Mode

```bash
sudo systemctl stop voice-music-player
cd /home/pi/voice-music-player
source venv/bin/activate
python src/main.py --debug
```

### Check Logs

```bash
sudo journalctl -u voice-music-player -f
```

### Test Audio Devices

```bash
./scripts/test_audio.sh
```

### Test Bluetooth

```bash
./scripts/test_bluetooth.sh
```

## Troubleshooting

### No Wakeword Detection
- Check microphone is card 3, device 0: `arecord -l`
- Test recording: `arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 test.wav`
- Verify Picovoice access key is valid

### No Audio Output
- Check ALSA configuration: `aplay -L`
- Test playback: `aplay -D plughw:0,0 test.wav`
- Verify Snapclient is running and connected

### Bluetooth Issues
- Check device status: `bluetoothctl info <MAC>`
- Reconnect manually: `bluetoothctl connect <MAC>`
- Check Bluetooth service: `sudo systemctl status bluetooth`

### STT Not Working
- Verify Vosk model is downloaded
- Check for ALSA errors in logs
- Ensure ffmpeg is installed for audio conversion

### Mopidy Connection Issues
- Check Mopidy is running: `sudo systemctl status mopidy`
- Verify Mopidy HTTP API is accessible: `curl http://localhost:6680/mopidy/rpc`
- Check Snapserver FIFO exists: `ls -l /tmp/snapfifo`

## Performance

- **Wakeword Detection**: ~50ms latency
- **STT Processing**: 1-3 seconds (depending on utterance length)
- **Command Execution**: <500ms
- **Total Response Time**: 2-4 seconds from command to playback

## Future Enhancements

- USB speaker in shower
- Multi-user voice profiles
- Custom wake words
- Music recommendations
- Timer/alarm integration
- Weather updates

## License

MIT License - See LICENSE file for details

## Credits

- **Picovoice Porcupine**: Wake word detection
- **Vosk**: Offline speech recognition
- **Piper**: Text-to-speech
- **Mopidy**: Music server
- **Snapcast**: Multi-room audio
