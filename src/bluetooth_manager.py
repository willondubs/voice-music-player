#!/usr/bin/env python3
"""
Bluetooth Manager
Manages Bluetooth speaker connection via bluetoothctl
"""

import logging
import subprocess
import re


class BluetoothManager:
    """Manages Bluetooth speaker connection"""
    
    def __init__(self, config):
        """Initialize Bluetooth manager"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.speaker_mac = config['bluetooth']['speaker_mac']
        self.connection_timeout = config['bluetooth']['connection_timeout']
        
        if self.speaker_mac == "YOUR_BLUETOOTH_MAC_HERE":
            self.logger.warning(
                "Bluetooth MAC address not configured in config/config.json. "
                "Bluetooth management will be disabled."
            )
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info(f"Bluetooth manager initialized for MAC: {self.speaker_mac}")
    
    def check_connection(self):
        """
        Check if Bluetooth speaker is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Run bluetoothctl info command
            cmd = ['bluetoothctl', 'info', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                self.logger.warning(f"bluetoothctl info failed: {result.stderr}")
                return False
            
            # Check if "Connected: yes" is in output
            output = result.stdout.lower()
            connected = 'connected: yes' in output
            
            if connected:
                self.logger.info("Bluetooth speaker is connected")
            else:
                self.logger.warning(f"Bluetooth speaker not connected. Output: {result.stdout[:200]}")
            
            return connected
            
        except subprocess.TimeoutExpired:
            self.logger.error("Bluetooth check timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking Bluetooth connection: {e}")
            return False
    
    def reconnect(self):
        """
        Reconnect to Bluetooth speaker
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        self.logger.info(f"Attempting to reconnect to {self.speaker_mac}...")
        
        try:
            # First, make sure bluetooth is powered on
            power_cmd = ['bluetoothctl', 'power', 'on']
            subprocess.run(power_cmd, capture_output=True, timeout=2)
            
            # Small delay
            import time
            time.sleep(0.5)
            
            # Try to connect
            cmd = ['bluetoothctl', 'connect', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.connection_timeout
            )
            
            if result.returncode == 0:
                # Check for success message
                output = result.stdout.lower()
                if 'connection successful' in output or 'connected' in output:
                    self.logger.info("Bluetooth reconnection successful")
                    return True
            
            # Log the specific error
            error_msg = result.stdout + result.stderr
            self.logger.warning(f"Bluetooth reconnection failed: {error_msg.strip()}")
            
            # If it's a profile unavailable error, the device may need to be manually powered on
            if 'br-connection-profile-unavailable' in error_msg.lower():
                self.logger.info("Device may be powered off or out of range")
            
            return False
            
        except subprocess.TimeoutExpired:
            self.logger.error("Bluetooth reconnection timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error reconnecting Bluetooth: {e}")
            return False
    
    def disconnect(self):
        """
        Disconnect from Bluetooth speaker
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        self.logger.info(f"Disconnecting from {self.speaker_mac}...")
        
        try:
            cmd = ['bluetoothctl', 'disconnect', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.info("Bluetooth disconnected")
                return True
            
            self.logger.warning(f"Bluetooth disconnect failed: {result.stdout}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error disconnecting Bluetooth: {e}")
            return False
    
    def get_device_info(self):
        """
        Get detailed information about the Bluetooth device
        
        Returns:
            dict: Device information, or None on error
        """
        if not self.enabled:
            return None
        
        try:
            cmd = ['bluetoothctl', 'info', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output
            info = {}
            for line in result.stdout.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return None
    
    def is_paired(self):
        """
        Check if device is paired
        
        Returns:
            bool: True if paired, False otherwise
        """
        info = self.get_device_info()
        if info:
            paired = info.get('Paired', '').lower()
            return paired == 'yes'
        return False
    
    def pair(self):
        """
        Pair with Bluetooth device
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        self.logger.info(f"Pairing with {self.speaker_mac}...")
        
        try:
            cmd = ['bluetoothctl', 'pair', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Also trust the device
                self.trust()
                self.logger.info("Bluetooth pairing successful")
                return True
            
            self.logger.warning(f"Bluetooth pairing failed: {result.stdout}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error pairing Bluetooth: {e}")
            return False
    
    def trust(self):
        """
        Trust Bluetooth device
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            cmd = ['bluetoothctl', 'trust', self.speaker_mac]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error trusting Bluetooth device: {e}")
            return False
