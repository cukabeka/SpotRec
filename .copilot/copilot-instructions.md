# SpotRec - GitHub Copilot Instructions

## Project Overview

SpotRec is a Python-based audio recording tool that captures Spotify playback from both the official Spotify desktop client and ncspot (a terminal-based Spotify client) using FFmpeg and PulseAudio.

## Key Parameters and Settings

### Default Configuration
- **Default Client**: `ncspot` (terminal-based Spotify client)
- **Alternative Client**: `spotify` (official Spotify desktop client)
- **Default Output Format**: `flac` (lossless)
- **Default Audio Quality**: `320` (kbps for lossy formats)
- **Default Output Directory**: `~/SpotRec`
- **Default Filename Pattern**: `{trackNumber} - {artist} - {title}`

### Supported Audio Formats
- **FLAC**: Lossless format (default), no quality parameter needed
- **MP3**: Lossy format, uses libmp3lame codec
  - Quality: bitrate in kbps (128, 192, 256, 320)
- **OGG**: Lossy format, uses libvorbis codec
  - Quality: quality level 0-10 (10 is best)
- **M4A**: Lossy format, uses AAC codec
  - Quality: bitrate in kbps

### Client Configuration

#### ncspot (Default)
- D-Bus destination: `org.mpris.MediaPlayer2.ncspot`
- PulseAudio application name: `ncspot`
- Bitrate setting: 320 kbps (highest available in Spotify)
- Volume normalization: Disabled (for consistent recording)
- Backend: PulseAudio (required for SpotRec)

#### Spotify Desktop Client
- D-Bus destination: `org.mpris.MediaPlayer2.spotify`
- PulseAudio application name: `spotify`

## Important Code Patterns

### Security
- **Always use `shlex.quote()`** for shell command parameters to prevent injection
- **Specific exception handling**: Use `subprocess.CalledProcessError` and `DBusException` instead of broad `Exception`

### Audio Recording
- Sample rate: 44.1 kHz (matches Spotify)
- Channels: Stereo (2 channels)
- Fragment size: 8820 (50ms latency)
- Recording sink: PulseAudio null/remap sink named "spotrec"

### File Naming
- Temporary files use dot prefix (e.g., `.filename.flac`) to hide until complete
- Supports subdirectory patterns: `{artist}/{album}/{trackNumber} {title}`
- Underscored filenames option replaces spaces with underscores

## Dependencies

### Runtime Dependencies
- Python 3
- python-dbus
- python-gi (GLib)
- ffmpeg (with libmp3lame, libvorbis, AAC support)
- PulseAudio (pactl, pacmd)
- gawk (for PulseAudio sink detection)
- bash
- requests (Python library for cover art)

### Client Dependencies
- **ncspot**: Rust-based, installable via:
  - Arch: `pacman -S ncspot`
  - Other: `cargo install --locked ncspot`
- **spotify**: Official Spotify desktop client

## Command-Line Interface

### Basic Usage
```bash
python3 spotrec.py                    # Record with ncspot (default)
python3 spotrec.py --client spotify   # Use Spotify desktop client
```

### Format and Quality
```bash
python3 spotrec.py --format mp3 --quality 320   # MP3 at 320kbps
python3 spotrec.py --format ogg --quality 10    # OGG at quality 10
python3 spotrec.py --format m4a --quality 256   # M4A at 256kbps
python3 spotrec.py --format flac                # FLAC (lossless, default)
```

### Playlist Recording
```bash
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M
```

### Output Options
```bash
python3 spotrec.py -o /path/to/output           # Custom output directory
python3 spotrec.py -p "{artist}/{album}/{trackNumber} {title}"  # Custom pattern
python3 spotrec.py -a                           # Add cover art
python3 spotrec.py -c                           # Use internal track counter
```

## Configuration Script

### configure-ncspot.sh
- Automatically detects Linux distribution
- Installs ncspot if not present (via package manager or cargo)
- Creates optimal configuration for recording
- Handles Spotify authentication interactively
- Sets bitrate to 320kbps
- Disables volume normalization
- Configures PulseAudio backend

## Architecture

### Main Components

1. **Spotify Class**: Handles D-Bus communication with Spotify/ncspot clients
   - Monitors playback state changes
   - Triggers recording on track changes
   - Manages playlist playback

2. **FFmpeg Class**: Manages audio recording processes
   - Records from PulseAudio monitor sink
   - Supports multiple concurrent instances
   - Handles metadata embedding
   - Post-processes files (cover art, format conversion)

3. **PulseAudio Class**: Manages PulseAudio sink configuration
   - Creates recording sink (null or remap)
   - Moves client audio to recording sink
   - Sets volumes to 100%

4. **Shell Class**: Wrapper for subprocess execution
   - Handles encoding and output redirection
   - Provides run(), Popen(), and check_output() methods

### Recording Flow
1. Client (ncspot/spotify) starts playing
2. D-Bus signals track change
3. Script pauses playback, seeks to beginning
4. FFmpeg starts recording from PulseAudio monitor
5. Playback resumes
6. Recording continues until next track
7. FFmpeg stops, file is renamed and post-processed

## File Structure
```
SpotRec/
├── spotrec.py              # Main Python script
├── configure-ncspot.sh     # ncspot installation and config script
├── README.md               # User documentation
├── LICENSE                 # MIT License
├── build-standalone.sh     # Standalone build script
├── .copilot/
│   └── copilot-instructions.md  # This file
└── img/                    # Screenshots for documentation
```

## Testing Considerations

### Manual Testing Required
- D-Bus communication (requires running Spotify/ncspot)
- PulseAudio sink manipulation
- Actual audio recording and playback
- Format conversion with different codecs

### Syntax Validation
```bash
python3 -m py_compile spotrec.py
bash -n configure-ncspot.sh
```

### Help Output Verification
```bash
python3 spotrec.py --help
```

## Common Issues and Solutions

### ncspot Not Found
- Verify installation with `which ncspot`
- Check `~/.cargo/bin` is in PATH
- Run configure-ncspot.sh for automatic installation

### D-Bus Connection Errors
- Ensure client is running before starting SpotRec
- Check D-Bus service availability: `dbus-send --session --dest=org.mpris.MediaPlayer2.ncspot --print-reply /org/mpris/MediaPlayer2 org.freedesktop.DBus.Introspectable.Introspect`

### PulseAudio Sink Issues
- Verify PulseAudio is running: `pactl info`
- Check sink inputs: `pactl list sink-inputs`
- Ensure client appears in sink inputs when playing

### Authentication Issues (ncspot)
- Run `ncspot` manually first to authenticate
- Credentials stored in `~/.cache/ncspot`
- Requires Spotify Premium account

## Code Style Guidelines

### String Formatting
- Use f-strings for dynamic content: `f"[{app_name}] Message"`
- Use `shlex.quote()` for shell arguments

### Logging
- Use appropriate log levels (info, debug, warning, error)
- Include context: component name, PID for processes

### Error Handling
- Catch specific exceptions
- Provide helpful error messages
- Exit gracefully on fatal errors

### Threading
- Use Thread subclasses for concurrent operations
- Name threads descriptively
- Clean up threads on shutdown

## Version Information
- Current Version: 0.15.1
- Python: 3.x required
- FFmpeg: Recent version with libmp3lame, libvorbis, AAC support

## Future Improvements
- PipeWire support (alternative to PulseAudio)
- Additional format support (ALAC, OPUS)
- Web interface for remote control
- Batch playlist processing
- Automatic metadata fetching improvements
