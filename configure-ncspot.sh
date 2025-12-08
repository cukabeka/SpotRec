#!/bin/bash

# configure-ncspot.sh
# Script to configure ncspot for use with SpotRec

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  ncspot Configuration for SpotRec"
echo "======================================"
echo

# Check if ncspot is installed
if ! command -v ncspot &> /dev/null; then
    echo -e "${RED}Error: ncspot is not installed.${NC}"
    echo "Please install ncspot first:"
    echo "  - Arch Linux: sudo pacman -S ncspot"
    echo "  - Ubuntu/Debian: cargo install --locked ncspot"
    echo "  - macOS: brew install ncspot"
    echo "  - Or visit: https://github.com/hrkfdn/ncspot"
    exit 1
fi

echo -e "${GREEN}✓ ncspot is installed${NC}"

# Get ncspot config directory
CONFIG_DIR="$HOME/.config/ncspot"
CONFIG_FILE="$CONFIG_DIR/config.toml"

# Create config directory if it doesn't exist
if [ ! -d "$CONFIG_DIR" ]; then
    mkdir -p "$CONFIG_DIR"
    echo -e "${GREEN}✓ Created ncspot config directory: $CONFIG_DIR${NC}"
else
    echo -e "${GREEN}✓ Config directory exists: $CONFIG_DIR${NC}"
fi

# Check if config file exists
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}! Config file already exists: $CONFIG_FILE${NC}"
    read -p "Do you want to backup and update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup existing config
        BACKUP_FILE="$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backed up existing config to: $BACKUP_FILE${NC}"
    else
        echo "Keeping existing configuration."
        exit 0
    fi
fi

# Create/update the configuration file
cat > "$CONFIG_FILE" << 'EOF'
# ncspot configuration for SpotRec
# This configuration optimizes ncspot for audio recording

# Audio settings
bitrate = 320  # Highest quality for recording
gapless = true  # Enable gapless playback
volnorm = false  # Disable volume normalization for consistent recording levels

# Backend settings (use PulseAudio for SpotRec compatibility)
backend = "pulseaudio"
# If you need a specific audio device, uncomment and set:
# backend_device = "your_device_name"

# Playback settings
shuffle = false  # Disable shuffle by default for playlist recording
repeat = "playlist"  # Repeat playlist for continuous recording

# Cache settings
audio_cache = true  # Enable audio caching
audio_cache_size = 1024  # Cache size in MiB

# Notification settings (optional)
notify = true  # Enable notifications to track recording progress

# Default screen
initial_screen = "library"

# Use nerdfont icons (set to false if you don't have a nerd font)
use_nerdfont = false
EOF

echo -e "${GREEN}✓ Created/updated ncspot config file: $CONFIG_FILE${NC}"
echo

# Additional instructions
echo "======================================"
echo "  Configuration Complete!"
echo "======================================"
echo
echo "Next steps:"
echo "1. Start ncspot: ncspot"
echo "2. Log in to your Spotify account (if not already logged in)"
echo "3. Navigate to the playlist you want to record"
echo "4. In another terminal, run SpotRec with ncspot:"
echo "   python3 spotrec.py --client ncspot"
echo
echo "Optional: To record a specific playlist by ID:"
echo "   python3 spotrec.py --client ncspot --playlist-id YOUR_PLAYLIST_ID"
echo
echo "To find a playlist ID:"
echo "  - Open Spotify Web Player"
echo "  - Navigate to the playlist"
echo "  - Copy the ID from the URL: spotify.com/playlist/[ID]"
echo
echo -e "${YELLOW}Important notes:${NC}"
echo "  - Make sure PulseAudio is running"
echo "  - Don't change volume or seek during recording"
echo "  - The recording will start when you play music in ncspot"
echo

# Check for PulseAudio
if ! command -v pactl &> /dev/null; then
    echo -e "${RED}Warning: PulseAudio (pactl) not found!${NC}"
    echo "SpotRec requires PulseAudio. Please install it:"
    echo "  - Arch Linux: sudo pacman -S pulseaudio"
    echo "  - Ubuntu/Debian: sudo apt install pulseaudio"
fi

echo "======================================"
