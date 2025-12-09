#!/bin/bash

# Script to configure ncspot for use with SpotRec on macOS
# This script sets up the ncspot configuration file with optimal settings

echo "SpotRec - ncspot Configuration Script"
echo "======================================"
echo ""

# Detect OS
OS=$(uname -s)

if [ "$OS" = "Darwin" ]; then
    echo "macOS detected"
    CONFIG_DIR="$HOME/Library/Application Support/ncspot"
else
    echo "Linux detected"
    CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/ncspot"
fi

CONFIG_FILE="$CONFIG_DIR/config.toml"

echo "Configuration directory: $CONFIG_DIR"
echo "Configuration file: $CONFIG_FILE"
echo ""

# Create config directory if it doesn't exist
mkdir -p "$CONFIG_DIR"

# Check if config file already exists
if [ -f "$CONFIG_FILE" ]; then
    echo "Warning: Configuration file already exists"
    echo "Creating backup at $CONFIG_FILE.bak"
    if ! cp "$CONFIG_FILE" "$CONFIG_FILE.bak"; then
        echo "Error: Failed to create backup. Aborting to prevent data loss."
        exit 1
    fi
    # Verify backup was created successfully
    if [ ! -f "$CONFIG_FILE.bak" ] || [ ! -r "$CONFIG_FILE.bak" ]; then
        echo "Error: Backup file is not readable. Aborting to prevent data loss."
        exit 1
    fi
    echo "✓ Backup created successfully"
fi

# Create the configuration file
cat > "$CONFIG_FILE" << 'EOF'
# ncspot configuration for SpotRec
# This configuration optimizes ncspot for recording with SpotRec

[theme]
# You can customize the theme here

[audio]
# Audio backend (alsa, pulseaudio, portaudio, rodio)
# On macOS, use portaudio or rodio
backend = "portaudio"

# Audio quality: 96, 160, 320
bitrate = 320

# Enable gapless playback
gapless = true

[mpris]
# Enable MPRIS D-Bus interface (required for SpotRec)
enable = true

[behavior]
# Shuffle mode
shuffle = false

# Repeat mode: off, track, playlist
repeat = "playlist"

# Notify on track change
notify = true

# Save playback state
save_state = true

[keybindings]
# You can customize keybindings here

# Example custom keybindings:
# "Ctrl+p" = "playpause"
# "Ctrl+n" = "next"
# "Ctrl+b" = "previous"

[credentials]
# You can store credentials here or login interactively
# username = "your_username"
# password = "your_password"
EOF

echo "✓ Configuration file created successfully"
echo ""

if [ "$OS" = "Darwin" ]; then
    echo "macOS Setup Instructions:"
    echo "========================="
    echo ""
    echo "1. Install ncspot:"
    echo "   brew install ncspot"
    echo ""
    echo "2. Install BlackHole (virtual audio device):"
    echo "   brew install blackhole-2ch"
    echo "   or download from: https://existential.audio/blackhole/"
    echo ""
    echo "3. Configure Multi-Output Device:"
    echo "   a. Open 'Audio MIDI Setup' (in /Applications/Utilities/)"
    echo "   b. Click '+' button at bottom left and select 'Create Multi-Output Device'"
    echo "   c. Check both your regular speakers and 'BlackHole 2ch'"
    echo "   d. Your music will play through speakers AND be recorded via BlackHole"
    echo ""
    echo "4. Optional: Install SwitchAudioSource for command-line audio control:"
    echo "   brew install switchaudio-osx"
    echo ""
    echo "5. Start ncspot and login with your Spotify credentials:"
    echo "   ncspot"
    echo ""
    echo "6. Run SpotRec with ncspot:"
    echo "   python3 spotrec.py --client ncspot -o ~/Music/SpotRec"
    echo ""
else
    echo "Linux Setup Instructions:"
    echo "========================="
    echo ""
    echo "1. Install ncspot:"
    echo "   - Arch: yay -S ncspot"
    echo "   - Ubuntu/Debian: snap install ncspot"
    echo "   - From source: cargo install ncspot"
    echo ""
    echo "2. Start ncspot and login:"
    echo "   ncspot"
    echo ""
    echo "3. Run SpotRec with ncspot:"
    echo "   python3 spotrec.py --client ncspot"
    echo ""
fi

echo "Configuration complete!"
echo ""
echo "Note: Make sure to enable MPRIS in ncspot for SpotRec to work."
echo "      This is enabled by default in the generated config."
