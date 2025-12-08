#!/bin/bash

# configure-ncspot.sh
# Script to install and configure ncspot for use with SpotRec

# Define colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "======================================"
echo "  ncspot Installation & Configuration"
echo "  for SpotRec"
echo "======================================"
echo

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        echo "$DISTRIB_ID" | tr '[:upper:]' '[:lower:]'
    else
        echo "unknown"
    fi
}

# Function to install ncspot
install_ncspot() {
    local distro=$(detect_distro)
    echo -e "${BLUE}Detected distribution: $distro${NC}"
    echo
    
    case "$distro" in
        arch|manjaro|endeavouros)
            echo -e "${YELLOW}Installing ncspot via pacman...${NC}"
            sudo pacman -S --noconfirm ncspot
            ;;
        ubuntu|debian|linuxmint|pop)
            echo -e "${YELLOW}Installing dependencies and ncspot via cargo...${NC}"
            echo "Note: This requires Rust/cargo to be installed"
            
            # Check if cargo is installed
            if ! command -v cargo &> /dev/null; then
                echo -e "${YELLOW}Cargo not found. Installing Rust...${NC}"
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
                source "$HOME/.cargo/env"
            fi
            
            # Install build dependencies
            echo -e "${YELLOW}Installing build dependencies...${NC}"
            sudo apt-get update
            sudo apt-get install -y build-essential pkg-config libssl-dev libdbus-1-dev \
                libncurses-dev libpulse-dev libxcb1-dev libxcb-render0-dev libxcb-shape0-dev \
                libxcb-xfixes0-dev
            
            # Install ncspot
            cargo install --locked ncspot
            ;;
        fedora|rhel|centos)
            echo -e "${YELLOW}Installing dependencies and ncspot via cargo...${NC}"
            
            # Check if cargo is installed
            if ! command -v cargo &> /dev/null; then
                echo -e "${YELLOW}Cargo not found. Installing Rust...${NC}"
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
                source "$HOME/.cargo/env"
            fi
            
            # Install build dependencies
            echo -e "${YELLOW}Installing build dependencies...${NC}"
            sudo dnf install -y gcc pkg-config openssl-devel dbus-devel ncurses-devel \
                pulseaudio-libs-devel libxcb-devel
            
            # Install ncspot
            cargo install --locked ncspot
            ;;
        opensuse*|suse)
            echo -e "${YELLOW}Installing dependencies and ncspot via cargo...${NC}"
            
            # Check if cargo is installed
            if ! command -v cargo &> /dev/null; then
                echo -e "${YELLOW}Cargo not found. Installing Rust...${NC}"
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
                source "$HOME/.cargo/env"
            fi
            
            # Install build dependencies
            sudo zypper install -y gcc pkg-config openssl-devel dbus-1-devel \
                ncurses-devel libpulse-devel libxcb-devel
            
            # Install ncspot
            cargo install --locked ncspot
            ;;
        *)
            echo -e "${RED}Distribution not directly supported.${NC}"
            echo "Attempting to install via cargo..."
            
            # Check if cargo is installed
            if ! command -v cargo &> /dev/null; then
                echo -e "${YELLOW}Cargo not found. Installing Rust...${NC}"
                curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
                source "$HOME/.cargo/env"
            fi
            
            echo "Please ensure you have the following dependencies installed:"
            echo "  - build-essential / gcc"
            echo "  - pkg-config"
            echo "  - libssl-dev / openssl-devel"
            echo "  - libdbus-1-dev / dbus-devel"
            echo "  - libncurses-dev / ncurses-devel"
            echo "  - libpulse-dev / pulseaudio-libs-devel"
            echo "  - libxcb-dev / libxcb-devel"
            echo
            read -p "Press Enter to continue with installation or Ctrl+C to cancel..."
            
            cargo install --locked ncspot
            ;;
    esac
    
    # Verify installation
    if command -v ncspot &> /dev/null; then
        echo -e "${GREEN}✓ ncspot installed successfully${NC}"
        return 0
    else
        # Check if it's in cargo bin directory
        if [ -f "$HOME/.cargo/bin/ncspot" ]; then
            echo -e "${GREEN}✓ ncspot installed in ~/.cargo/bin/${NC}"
            echo -e "${YELLOW}Adding ~/.cargo/bin to PATH for this session${NC}"
            export PATH="$HOME/.cargo/bin:$PATH"
            return 0
        else
            echo -e "${RED}✗ ncspot installation failed${NC}"
            return 1
        fi
    fi
}

# Check if ncspot is installed
if ! command -v ncspot &> /dev/null; then
    echo -e "${YELLOW}ncspot is not installed.${NC}"
    read -p "Would you like to install ncspot now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_ncspot
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install ncspot. Please install it manually.${NC}"
            echo "Visit: https://github.com/hrkfdn/ncspot for installation instructions"
            exit 1
        fi
    else
        echo -e "${RED}ncspot is required. Exiting.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ ncspot is already installed${NC}"
fi

echo

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
        echo -e "${YELLOW}Note: Make sure your config has these settings for optimal recording:${NC}"
        echo "  bitrate = 320"
        echo "  volnorm = false"
        echo "  backend = \"pulseaudio\""
        exit 0
    fi
fi

# Create/update the configuration file
cat > "$CONFIG_FILE" << 'EOF'
# ncspot configuration for SpotRec
# This configuration optimizes ncspot for audio recording

# Audio settings
bitrate = 320  # Highest quality for recording (96, 160, or 320)
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

# Check for PulseAudio
if ! command -v pactl &> /dev/null; then
    echo -e "${RED}Warning: PulseAudio (pactl) not found!${NC}"
    echo "SpotRec requires PulseAudio. Please install it:"
    echo "  - Arch Linux: sudo pacman -S pulseaudio"
    echo "  - Ubuntu/Debian: sudo apt install pulseaudio"
    echo "  - Fedora: sudo dnf install pulseaudio"
fi

echo

# Spotify Authentication
echo "======================================"
echo "  Spotify Authentication"
echo "======================================"
echo
echo -e "${BLUE}ncspot needs your Spotify Premium credentials to work.${NC}"
echo
echo "Two options:"
echo "1. Log in interactively when you start ncspot (recommended)"
echo "2. Start ncspot now to set up authentication"
echo
read -p "Would you like to start ncspot now to authenticate? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo
    echo -e "${GREEN}Starting ncspot...${NC}"
    echo "After authentication, press 'q' to quit ncspot and continue setup."
    echo
    sleep 2
    
    # Start ncspot
    ncspot
    
    echo
    echo -e "${GREEN}✓ Authentication complete${NC}"
else
    echo
    echo -e "${YELLOW}You can authenticate later by running: ncspot${NC}"
    echo "The first time you run ncspot, it will ask for your credentials."
fi

echo

# Additional instructions
echo "======================================"
echo "  Configuration Complete!"
echo "======================================"
echo
echo -e "${GREEN}SpotRec is now ready to use with ncspot!${NC}"
echo
echo "Quick Start:"
echo "1. Start ncspot in one terminal:"
echo "   ${BLUE}ncspot${NC}"
echo
echo "2. In another terminal, start SpotRec:"
echo "   ${BLUE}python3 spotrec.py${NC}"
echo "   (ncspot is now the default client)"
echo
echo "3. Play music in ncspot - recording starts automatically!"
echo
echo "Advanced options:"
echo "  # Record with specific format and quality"
echo "  ${BLUE}python3 spotrec.py --format mp3 --quality 320${NC}"
echo
echo "  # Record specific playlist"
echo "  ${BLUE}python3 spotrec.py --playlist-id YOUR_PLAYLIST_ID${NC}"
echo
echo "  # Use original Spotify client instead"
echo "  ${BLUE}python3 spotrec.py --client spotify${NC}"
echo
echo "  # See all options"
echo "  ${BLUE}python3 spotrec.py --help${NC}"
echo
echo "To find a playlist ID:"
echo "  - Open Spotify Web Player"
echo "  - Navigate to the playlist"
echo "  - Copy the ID from the URL: spotify.com/playlist/[ID]"
echo
echo -e "${YELLOW}Important notes:${NC}"
echo "  - Make sure PulseAudio is running"
echo "  - Don't change volume or seek during recording"
echo "  - Recording quality matches ncspot bitrate (320kbps)"
echo "  - Default output format is FLAC (lossless)"
echo
echo "======================================"
