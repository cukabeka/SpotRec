# SpotRec

Python script to record audio from Spotify clients (ncspot or official Spotify desktop client) using FFmpeg and PulseAudio

**Default Client**: ncspot (terminal-based, lightweight Spotify client)

AUR: https://aur.archlinux.org/packages/spotrec/



## Quick Start

### Recommended: Using ncspot (Default)

The easiest way to get started with SpotRec is using ncspot:

1. **Run the configuration script** (installs and configures ncspot automatically):
```bash
./configure-ncspot.sh
```

2. **Start recording**:
```bash
python3 spotrec.py
```

That's it! The script will automatically start ncspot recording. ncspot is now the default client.

### Alternative: Using Official Spotify Client

If you prefer the official Spotify desktop client:

```bash
python3 spotrec.py --client spotify
```

## Installation

### Dependencies

- Python 3
- python-dbus
- python-gi (GLib)
- FFmpeg (with libmp3lame, libvorbis, AAC codec support)
- PulseAudio (pactl)
- gawk
- ncspot (installed automatically via configure-ncspot.sh)

### Installing ncspot

The `configure-ncspot.sh` script will automatically install ncspot for your distribution:

```bash
chmod +x configure-ncspot.sh
./configure-ncspot.sh
```

Supported distributions:
- Arch Linux / Manjaro / EndeavourOS (via pacman)
- Ubuntu / Debian / Linux Mint / Pop!_OS (via cargo)
- Fedora / RHEL / CentOS (via cargo)
- openSUSE (via cargo)
- Other distributions (via cargo)

The script will also:
- Configure optimal recording settings (320kbps bitrate)
- Set up PulseAudio backend
- Disable volume normalization
- Guide you through Spotify authentication

## Usage

### Basic Recording

```bash
# Record with ncspot (default)
python3 spotrec.py

# Record with official Spotify client
python3 spotrec.py --client spotify

# Custom output directory
python3 spotrec.py -o ~/Music/Recordings
```

### Output Formats and Quality

SpotRec supports multiple output formats:

```bash
# FLAC (lossless, default)
python3 spotrec.py --format flac

# MP3 with quality settings
python3 spotrec.py --format mp3 --quality 320   # 320kbps (best)
python3 spotrec.py --format mp3 --quality 256   # 256kbps
python3 spotrec.py --format mp3 --quality 192   # 192kbps

# OGG Vorbis with quality settings
python3 spotrec.py --format ogg --quality 10    # Quality 10 (best)
python3 spotrec.py --format ogg --quality 6     # Quality 6 (good)

# M4A (AAC) with bitrate
python3 spotrec.py --format m4a --quality 256   # 256kbps
```

**Default**: FLAC (lossless) at 320kbps source quality from Spotify

### Recording Playlists

You can specify a playlist ID to automatically record an entire playlist:

```bash
# Record specific playlist
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M

# With custom format
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M --format mp3 --quality 320
```

**To find a playlist ID:**
1. Open Spotify Web Player
2. Navigate to the playlist
3. Copy the ID from the URL: `https://open.spotify.com/playlist/[YOUR_PLAYLIST_ID]`

### Advanced Options

```bash
# Add cover art to recordings
python3 spotrec.py -a

# Custom filename pattern
python3 spotrec.py -p "{artist}/{album}/{trackNumber} {title}"

# Use internal track counter (preserves playlist order)
python3 spotrec.py -c

# Underscored filenames (no spaces)
python3 spotrec.py -u

# Mute audio output while recording
python3 spotrec.py -m

# Skip intro message
python3 spotrec.py -s

# Debug mode
python3 spotrec.py -d
```

### Command-Line Options

```
  -h, --help            Show help message
  -d, --debug           Print debug information
  -s, --skip-intro      Skip the intro message
  -m, --mute-recording  Mute the client on your main output device while recording
  -o, --output-directory
                        Where to save the recordings (default: ~/SpotRec)
  -p, --filename-pattern
                        Pattern for file names (default: "{trackNumber} - {artist} - {title}")
                        Available placeholders: {artist}, {album}, {trackNumber}, {title}
  -u, --underscored-filenames
                        Use underscores instead of spaces in filenames
  -c, --internal-track-counter
                        Use internal track counter (useful for playlists)
  -a, --add-cover-art   Embed cover art into the recorded files
  --client {spotify,ncspot}
                        Spotify client to use (default: ncspot)
  --playlist-id PLAYLIST_ID
                        Spotify playlist ID to record
  --format {flac,mp3,ogg,m4a}
                        Output audio format (default: flac)
  --quality QUALITY     Audio quality for lossy formats
                        MP3/M4A: bitrate in kbps (128, 192, 256, 320)
                        OGG: quality level 0-10 (10 is best)
                        Default: 320
```

## Examples

### Example 1: High-Quality Playlist Recording

```bash
# Record entire playlist in FLAC
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M -a -c
```

### Example 2: MP3 Recording for Portable Device

```bash
# Record in MP3 at 320kbps with cover art
python3 spotrec.py --format mp3 --quality 320 -a -o ~/Music/Portable
```

### Example 3: Organized File Structure

```bash
# Save with artist/album folder structure
python3 spotrec.py -p "{artist}/{album}/{trackNumber} - {title}" -a
```

### Example 4: Using Official Spotify Client

```bash
# Use official client instead of ncspot
python3 spotrec.py --client spotify -o ~/Music/Recordings
```

## Audio Quality Settings

### Spotify/ncspot Streaming Quality

The `configure-ncspot.sh` script sets ncspot to stream at **320 kbps** (highest quality available from Spotify). This is the source quality that SpotRec records from.

### Recording Quality

- **FLAC (default)**: Lossless recording - captures the full 320kbps stream without quality loss
- **MP3**: Lossy format - recommended quality: 320kbps for near-transparent quality
- **OGG Vorbis**: Lossy format - recommended quality: 8-10 for high quality
- **M4A (AAC)**: Lossy format - recommended quality: 256-320kbps

**Recommendation**: Use FLAC for archival/maximum quality, then convert to lossy formats as needed.

## PulseAudio Configuration

```
pavucontrol
```

Pay attention to the red circles, everything else is muted and with volume set
to 0%

![playback tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_playback_tab.jpeg)

Note: actually "Lavf..." will appear after you start playing a song

![recording tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_recording_tab.jpeg)

![output devices tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_output_devices_tab.jpeg)

![input devices tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_input_devices_tab.jpeg)

![configuration tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_configuration_tab.jpeg)

Finally start playing whatever you want


## Hints

- **ncspot is now the default client** - just run `python3 spotrec.py`

- **Use the configuration script**: Run `./configure-ncspot.sh` for automatic setup

- **Audio quality**: ncspot is configured for 320kbps streaming (highest Spotify quality)

- **Disable volume normalization** in the Spotify Client or ncspot config (done automatically by configure-ncspot.sh)

- **Do not change the volume** during recording for consistent quality

- **Output formats**: 
  - FLAC (default): Lossless, best quality, larger files
  - MP3: Universal compatibility, 320kbps recommended
  - OGG: Good quality/size ratio, quality 8-10 recommended
  - M4A: Apple ecosystem, 256-320kbps recommended

- **Playlist recording**: Use `--playlist-id` with `-c` (internal counter) to preserve track order

- **Cover art**: Use `-a` flag to embed album artwork into files

- **Post-processing**: Use Audacity to trim recordings if needed (SpotRec records slightly longer to ensure nothing is missed)

## ncspot Configuration

The `configure-ncspot.sh` script automatically configures ncspot with optimal settings:

- **Bitrate**: 320 kbps (highest quality)
- **Volume normalization**: Disabled (for consistent recording levels)
- **Backend**: PulseAudio (required for SpotRec)
- **Gapless playback**: Enabled
- **Audio caching**: Enabled (1GB cache)

Configuration file location: `~/.config/ncspot/config.toml`


## Troubleshooting

Start the script with the debug flag:

```
./spotrec.py --debug

# For ncspot
./spotrec.py --client ncspot --debug
```

If one of the following scenarios happens:

* you do not see something like the ffmpeg output, which should appear right
  few seconds after the song start

```
# what you should see when ffmpeg is recording ...
size=56400kB time=00:00:04.15 bitrate= 130.7kbits/s speed=1x
```

* you do not see any "Lavf..." in the pavucontrol
  [recording tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_recording_tab.jpeg)
* you get a stacktrace ending with:

```
ValueError: invalid literal for int() with base 10: 'nput'
```

I would suggest you to:

* quickly press the "next song button" and then the "previous song button" in
  the spotify client (or use keyboard shortcuts in ncspot)
* stop everything and start over, after some tries it usually works :)


**Note: sometimes spotify detects when the user does not interact with the
application for a long time (more or less an hour) and starts looping over a
song, to avoid this scenario I would suggest to keep interacting with the
spotify client.**

### ncspot-specific troubleshooting

- Make sure ncspot is using the PulseAudio backend (configured by `configure-ncspot.sh`)
- Verify ncspot is running before starting SpotRec
- Check that ncspot appears in `pactl list sink-inputs` when playing music
- If playlist recording doesn't work, try manually playing the playlist in ncspot first
