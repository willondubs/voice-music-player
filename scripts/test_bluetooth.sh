#!/bin/bash
# Test Bluetooth Connection Script
# Tests Bluetooth speaker connection and configuration

echo "=========================================="
echo "Bluetooth Testing Script"
echo "=========================================="
echo ""

# Check for bluetoothctl
if ! command -v bluetoothctl &> /dev/null; then
    echo "Error: bluetoothctl not found. Install with: sudo apt install bluez"
    exit 1
fi

# Get MAC address from config if available
CONFIG_FILE="../config/config.json"
if [ -f "$CONFIG_FILE" ]; then
    MAC=$(grep -o '"speaker_mac":\s*"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
    if [ "$MAC" != "YOUR_BLUETOOTH_MAC_HERE" ] && [ -n "$MAC" ]; then
        echo "Using MAC address from config: $MAC"
    else
        echo "⚠ MAC address not configured in config.json"
        MAC=""
    fi
else
    MAC=""
fi

echo ""
echo "1. Checking Bluetooth Service:"
echo "------------------------------"
systemctl status bluetooth --no-pager -l | head -5
echo ""

echo "2. Bluetooth Controller Status:"
echo "-------------------------------"
bluetoothctl show
echo ""

echo "3. Paired Devices:"
echo "------------------"
bluetoothctl devices
echo ""

if [ -n "$MAC" ]; then
    echo "4. Device Information (MAC: $MAC):"
    echo "-----------------------------------"
    bluetoothctl info "$MAC"
    echo ""
    
    echo "5. Connection Status:"
    echo "---------------------"
    INFO=$(bluetoothctl info "$MAC")
    if echo "$INFO" | grep -q "Connected: yes"; then
        echo "✓ Device is CONNECTED"
    else
        echo "✗ Device is NOT connected"
        echo ""
        echo "Attempting to connect..."
        bluetoothctl connect "$MAC"
        sleep 2
        
        INFO=$(bluetoothctl info "$MAC")
        if echo "$INFO" | grep -q "Connected: yes"; then
            echo "✓ Connection successful!"
        else
            echo "✗ Connection failed"
            echo ""
            echo "Troubleshooting steps:"
            echo "1. Make sure the speaker is powered on"
            echo "2. Make sure the speaker is in pairing mode"
            echo "3. Try: bluetoothctl"
            echo "        > remove $MAC"
            echo "        > scan on"
            echo "        > pair $MAC"
            echo "        > trust $MAC"
            echo "        > connect $MAC"
        fi
    fi
    echo ""
    
    echo "6. Testing Audio Output (if connected):"
    echo "---------------------------------------"
    INFO=$(bluetoothctl info "$MAC")
    if echo "$INFO" | grep -q "Connected: yes"; then
        echo "Playing test tone through Bluetooth..."
        # Try to play a test sound
        speaker-test -t sine -f 1000 -l 1 -p 100000 2>&1 | head -3
        echo "Did you hear the tone? (Check your Bluetooth speaker)"
    else
        echo "⚠ Skipping audio test - device not connected"
    fi
else
    echo "4. MAC Address Not Configured:"
    echo "------------------------------"
    echo "To find your speaker's MAC address:"
    echo "1. Put your speaker in pairing mode"
    echo "2. Run: bluetoothctl"
    echo "3. Run: scan on"
    echo "4. Wait for your device to appear"
    echo "5. Note the MAC address (format: XX:XX:XX:XX:XX:XX)"
    echo "6. Run: pair <MAC>"
    echo "7. Run: trust <MAC>"
    echo "8. Run: connect <MAC>"
    echo "9. Add the MAC to config/config.json"
fi

echo ""
echo "=========================================="
echo "Bluetooth testing complete!"
echo "=========================================="
