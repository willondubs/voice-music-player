# Troubleshooting Guide

## Issue 1: Wake Word Not Detecting

The app is running but not detecting the wake word "Computer". Let's test:

### Test Wake Word Detection

**[Download test script](test_wakeword.py)**

```bash
cd ~/voice-music-player
source venv/bin/activate

# Copy the test script
# Then run it
python test_wakeword.py
```

When prompted, enter your Picovoice access key (same one in config.json).

The script will:
1. List all audio devices
2. Find your PS3 Eye
3. Listen for "Computer"
4. Tell you if detection is working

### Common Wake Word Issues:

**Issue: Wrong microphone**
- Check the log shows: "Found PS3 Eye device"
- If not, verify PS3 Eye is plugged in: `arecord -l`

**Issue: Too quiet**
- Speak louder and closer to microphone
- Increase sensitivity in config.json (0.5 → 0.7)

**Issue: Background noise**
- Reduce background noise
- Decrease sensitivity (0.5 → 0.3)

**Issue: Wrong access key**
- Verify key in config.json matches console.picovoice.ai

### Test Microphone Recording:

```bash
# Record 5 seconds
arecord -D plughw:3,0 -f S16_LE -r 16000 -c 4 -d 5 test.wav

# Play it back
aplay test.wav
```

Should hear your voice clearly.

---

## Issue 2: Bluetooth Not Reconnecting

The error `br-connection-profile-unavailable` means the speaker is powered off or out of range.

### Manual Connection:

```bash
# Power on bluetooth
bluetoothctl power on

# Turn ON your JBL Clip 5 speaker first!

# Then connect
bluetoothctl connect E8:26:CF:7A:84:40
```

### In the App:

The app will try to reconnect when you issue a music command, not at startup. This is by design so the speaker can be off when the Pi boots.

**Flow:**
1. Start app (Bluetooth check happens but doesn't reconnect)
2. Say "Computer" → "Play music"
3. App checks Bluetooth before playing
4. If disconnected, attempts reconnect
5. If successful, plays music

### Test Bluetooth:

```bash
# Check status
bluetoothctl info E8:26:CF:7A:84:40

# If not connected, connect manually:
bluetoothctl connect E8:26:CF:7A:84:40
```

### Auto-reconnect Settings:

In `config.json`:

```json
"bluetooth": {
    "speaker_mac": "E8:26:CF:7A:84:40",
    "check_on_command": true,      // Check before each music command
    "auto_reconnect": true,         // Try to reconnect if disconnected
    "connection_timeout": 10
}
```

---

## Issue 3: ALSA Warnings (Can Ignore)

The ALSA errors like:
```
ALSA lib pcm.c:2722:(snd_pcm_open_noupdate) Unknown PCM front
```

These are just PyAudio scanning for devices. They don't affect functionality. You can ignore them.

To reduce them, you could set `PYTHONWARNINGS=ignore` but it's not necessary.

---

## Testing Workflow

### 1. Test Wake Word

```bash
cd ~/voice-music-player
source venv/bin/activate
python test_wakeword.py
```

Say "Computer" - should detect within 1-2 seconds.

### 2. Connect Bluetooth Manually

```bash
# Turn on your speaker first!
bluetoothctl connect E8:26:CF:7A:84:40
```

### 3. Run the App

```bash
python src/main.py --debug
```

### 4. Test Voice Commands

1. Say "**Computer**" (wait for response)
2. Say "**Play music**" (or any command)
3. App should:
   - Check Bluetooth (reconnect if needed)
   - Search Mopidy
   - Play music

---

## Common Commands to Test

After wake word:
- "Play music" (searches for "music")
- "Next"
- "Pause"
- "Volume up"
- "What's playing?"

---

## Debug Checklist

- [ ] Picovoice access key is correct in config.json
- [ ] PS3 Eye is plugged in (check: `arecord -l`)
- [ ] Can record from microphone (test above)
- [ ] JBL speaker is powered ON
- [ ] Speaker is paired/trusted (check: `bluetoothctl devices`)
- [ ] Mopidy is running (check: `systemctl status mopidy`)
- [ ] Vosk model is downloaded (check: `ls models/vosk-model-en/`)

---

## Quick Fixes

### Bluetooth speaker won't connect:

```bash
# Remove and re-pair
bluetoothctl
> remove E8:26:CF:7A:84:40
> scan on
# Wait for device to appear
> pair E8:26:CF:7A:84:40
> trust E8:26:CF:7A:84:40
> connect E8:26:CF:7A:84:40
> exit
```

### Wake word not working:

Edit `config/config.json`:
```json
"picovoice": {
    "sensitivity": 0.7   // Increase from 0.5 to 0.7
}
```

### Need to change wake word:

Visit console.picovoice.ai and create a custom wake word, then update config.json with the path.

---

## Expected Behavior

**Startup:**
```
Voice Music Player Starting
✓ All components initialized
✓ Bluetooth manager initialized for MAC: E8:26:CF:7A:84:40
⚠ Bluetooth speaker not connected (OK - will connect when needed)
Voice Music Player started - listening for wake word...
```

**After "Computer":**
```
🎤 Wake word detected!
[TTS says "Listening"]
Recording user command...
Processing speech...
Recognized: 'play music'
Parsed command: {'type': 'play', 'query': 'music', 'play_type': 'random'}
✓ Bluetooth connected
Searching for: 'music'
Found 15 tracks
Playing random track
✓ Playing
```

---

## Files to Check

Updated files with fixes:
- `src/bluetooth_manager.py` - Better reconnection logic
- `src/main.py` - Non-blocking startup Bluetooth check
- `test_wakeword.py` - Wake word testing script

Make sure you have the latest versions!
