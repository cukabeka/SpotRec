#!/bin/bash
# Comprehensive setup script for SpotRec on macOS

set -e # Exit immediately if a command exits with a non-zero status.

echo "SpotRec - macOS Setup Script"
echo "=============================="
echo ""
echo "This script will check for dependencies, set up a Python virtual environment,"
echo "and configure ncspot for use with SpotRec."
echo ""

# --- 1. Check for Homebrew ---
if ! command -v brew &> /dev/null; then
    echo "❌ Error: Homebrew is not installed."
    echo "Please install Homebrew first: https://brew.sh/"
    exit 1
fi
echo "✅ Homebrew is available."
echo ""

# --- 2. Install Homebrew Dependencies ---
echo "Checking and installing Homebrew dependencies..."
# ncspot is the recommended client
# ffmpeg is for recording
BREW_DEPS=("ncspot" "ffmpeg")
for dep in "${BREW_DEPS[@]}"; do
    if brew list "$dep" &> /dev/null; then
        echo "   - $dep is already installed."
    else
        echo "   - Installing $dep..."
        brew install "$dep"
    fi
done
echo "✅ Homebrew dependencies are set up."
echo ""


# --- 3. Set up Python Virtual Environment ---
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in './$VENV_DIR/'..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created."
else
    echo "✅ Python virtual environment already exists."
fi
echo ""

# --- 4. Install Python Dependencies ---
echo "Installing Python dependencies into the virtual environment..."
# Activate venv and install from requirements.txt
source "$VENV_DIR/bin/activate"
pip3 install -r requirements.txt
deactivate
echo "✅ Python dependencies installed."
echo ""

# --- 5. Configure ncspot ---
CONFIG_DIR="$HOME/Library/Application Support/ncspot"
CONFIG_FILE="$CONFIG_DIR/config.toml"
echo "Configuring ncspot..."

mkdir -p "$CONFIG_DIR"

if [ -f "$CONFIG_FILE" ]; then
    echo "   - Found existing ncspot config. Creating backup: $CONFIG_FILE.bak"
    cp "$CONFIG_FILE" "$CONFIG_FILE.bak"
fi

cat > "$CONFIG_FILE" << 'EOF'
# ncspot configuration for SpotRec

[audio]
backend = "portaudio"
bitrate = 320
gapless = true
EOF
echo "✅ ncspot configuration file created."
echo ""


# --- 6. Final Instructions ---
HOOK_SCRIPT_PATH="$(pwd)/ncspot_hook.py"

echo "🎉 Setup Complete! 🎉"
echo ""
echo "Next Steps:"
echo "-----------"
echo "1. IMPORTANT: If ncspot is running, please RESTART it now."
echo ""
echo "2. Configure your audio for recording (you only need to do this once):"
echo "   a. Open 'Audio MIDI Setup' (in /Applications/Utilities/)"
echo "   b. Click '+' at the bottom left and 'Create Multi-Output Device'."
echo "   c. In the new device, check the boxes for your main speakers AND for 'BlackHole 2ch'."
echo "   d. Set the 'Multi-Output Device' as your system's default sound output."
echo ""
echo "3. To run SpotRec:"
echo "   a. Start ncspot in a terminal using this command:"
echo "      ncspot --on-song-change-hook \"$HOOK_SCRIPT_PATH\""
echo ""
echo "   b. In ANOTHER terminal, navigate to the SpotRec directory and run:"
echo "      source venv/bin/activate"
echo "      python3 spotrec.py --client ncspot -o ~/Music/SpotRec"
echo ""

exit 0