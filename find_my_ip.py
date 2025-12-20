#!/usr/bin/env python3
"""
Script to find your computer's IP address
Run this on the laptop that's running the server
"""

import socket
import platform

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote server (doesn't actually send data)
        # This gets the IP of the interface that would be used for internet
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    print("=" * 50)
    print("Bus Tracker - Find Your Server IP")
    print("=" * 50)

    print(f"\nYour computer's IP address: {get_local_ip()}")
    print(f"\nUse this IP in your Raspberry Pi receiver code:")
    print(f'SERVER_IP = "{get_local_ip()}"')

    print("\n" + "=" * 50)
    print("To use with your Pi 3B:")
    print("1. Update the SERVER_IP in your receiver code")
    print("2. Make sure both devices are on same WiFi")
    print("3. The server port is always 3000")
    print("=" * 50)

if __name__ == "__main__":
    main()