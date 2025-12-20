#!/bin/bash
# Setup script for Raspberry Pi 3B LoRa Receiver

echo "=========================================="
echo "Setting up LoRa GPS Receiver for Pi 3B"
echo "=========================================="

# Update package list
echo "Updating package list..."
sudo apt update

# Install Python dependencies
echo "Installing Python dependencies..."
sudo apt install -y python3-pip python3-serial

# Install Python packages
echo "Installing required Python packages..."
pip3 install requests

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Check for USB devices
echo ""
echo "Checking for connected USB devices..."
lsusb | grep -i "serial\|usb\|uart"

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Reboot your Pi (required for dialout group)"
echo "2. Connect your LoRa module"
echo "3. Run: python3 pi3_lora_receiver.py"
echo ""
echo "Common serial port locations:"
echo "- USB to Serial: /dev/ttyUSB0"
echo "- GPIO pins: /dev/ttyS0"