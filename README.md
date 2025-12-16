# SpotRec

Python script to record the audio of Spotify clients (official Spotify client or ncspot) using FFmpeg.

- **Linux**: Uses PulseAudio for audio routing
- **macOS**: Uses BlackHole virtual audio device for audio routing

Supports both the official Spotify desktop client and ncspot (terminal-based client).

AUR (Linux): https://aur.archlinux.org/packages/spotrec/



## macOS Setup

The setup process for macOS is handled by a comprehensive setup script.

### 1. Run the Setup Script

First, make the script executable, then run it:

```bash
chmod +x ./configure-ncspot.sh
./configure-ncspot.sh
```

This script will automatically:
- Check for and install required Homebrew packages (like `dbus`, `ncspot`, `ffmpeg`).
- Start the D-Bus service required for communication.
- Create a Python virtual environment (`venv`) to keep dependencies isolated.
- Install the required Python packages (`requests`, `dbus-python`, etc.) into the virtual environment.
- Create a configuration file for `ncspot` that enables the D-Bus interface, which is essential for `SpotRec` to work.

### 2. Configure Audio Routing (One-Time Setup)

To record `ncspot`'s audio while still hearing it through your speakers, you need to create a "Multi-Output Device". You only have to do this once.

1. Open **Audio MIDI Setup** (located in `/Applications/Utilities/`).
2. Click the **`+`** button at the bottom left and select **'Create Multi-Output Device'**.
3. In the list for the new device, check the boxes for both your regular speakers/headphones **and** `BlackHole 2ch`.
4. Right-click the "Multi-Output Device" you just created and select **"Use This Device For Sound Output"**.

Now, all system audio will play through your speakers AND be silently routed to the `BlackHole` device, where `SpotRec` can record it.

## Usage on macOS

1. **Start ncspot**:
   Open a terminal and run `ncspot`. If this is your first time, log in. If `ncspot` was running during the setup, **you must restart it** for the new configuration to load.

2. **Run SpotRec**:
   Open a **second terminal window**, navigate to the `SpotRec` project directory, and then:

   ```bash
   # Activate the virtual environment
   source venv/bin/activate

   # Run SpotRec (it will now use the packages from the venv)
   python3 spotrec.py --client ncspot -o ~/Music/SpotRec
   ```

3. **Play Music**:
   Start playing music in `ncspot`. `SpotRec` will automatically detect and record each new track into your output directory.

## How it Works on macOS (ncspot)

- **`ncspot`**: A music player for Spotify that runs in the terminal. We install it with Homebrew.
- **D-Bus**: A system that allows different applications to talk to each other. `SpotRec` uses it to get information from `ncspot` (like the current song title) and to send commands (like "go to previous track" to ensure a clean recording). The setup script enables D-Bus inside `ncspot`'s configuration and makes sure the D-Bus service is running.
- **`venv` (Virtual Environment)**: This is an isolated sandbox for `SpotRec`'s Python packages (like `dbus-python` and `requests`). It prevents conflicts with other Python projects on your system. `ncspot` does **not** run inside the `venv`; it's a separate, system-level application. The two processes communicate via D-Bus, not via the Python environment.
- **BlackHole**: A virtual audio driver that creates an invisible audio input/output. We route `ncspot`'s sound to BlackHole so `SpotRec` (using `ffmpeg`) can listen to it and record.
- **Multi-Output Device**: A feature in macOS that lets you send audio to multiple devices at once. We use it to send `ncspot`'s audio to both your speakers (so you can hear it) and to BlackHole (so `SpotRec` can record it).

### macOS Command-line Options

```bash
# Record with ncspot to a custom directory
python3 spotrec.py --client ncspot -o ~/Music/Recordings

# Record a specific playlist
python3 spotrec.py --client ncspot --playlist-id 37i9dQZF1DXcBWIGoYBM5M

# Record in MP3 format with 320kbps quality
python3 spotrec.py --client ncspot -f mp3 -q 320

# Record in OGG format with quality level 8
python3 spotrec.py --client ncspot -f ogg -q 8

# Add cover art to recordings
python3 spotrec.py --client ncspot -a
```

## Linux Setup

### Prerequisites

On Linux, install the required dependencies:

**Arch Linux**:
```bash
sudo pacman -S python python-dbus ffmpeg pulseaudio gawk
pip install requests
```

**Ubuntu/Debian**:
```bash
sudo apt install python3 python3-dbus ffmpeg pulseaudio gawk python3-gi python3-requests
```

**Fedora**:
```bash
sudo dnf install python3 python3-dbus ffmpeg pulseaudio gawk python3-gobject python3-requests
```

### Usage on Linux

If you use the AUR package, you can simply run:

```
spotrec
```

Otherwise run:

```
python3 spotrec.py
```

### Example (Linux)

First start Spotify or ncspot.

Then you can run the python script which will record the music:

```
./spotrec.py -o ./my_song_dir --skip-intro
```

For ncspot:
```
./spotrec.py --client ncspot -o ./my_song_dir
```

Check the pulseaudio configuration:

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


## Command-line Options

SpotRec supports various command-line options to customize recording:

### Basic Options

```
-h, --help              Show help message and exit
-d, --debug             Enable debug logging
-s, --skip-intro        Skip the intro message
-o, --output-directory  Set output directory (default: ~/SpotRec)
```

### Client Options

```
--client {spotify,ncspot}
                        Choose client: 'spotify' (default) or 'ncspot'
```

### Playlist Recording

```
--playlist-id PLAYLIST_ID
                        Spotify playlist ID or URL to automatically record
                        Example: --playlist-id 37i9dQZF1DXcBWIGoYBM5M
                        Example: --playlist-id https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
```

### Output Format Options

```
-f, --format {flac,ogg,mp3,mp4}
                        Output audio format (default: flac)
-q, --quality QUALITY   Audio quality/bitrate
                        For mp3/mp4: bitrate in kbps (128, 192, 256, 320)
                        For ogg: quality level 0-10
                        Default: 320
```

### File Naming Options

```
-p, --filename-pattern  Pattern for file names
                        Available: {artist}, {album}, {trackNumber}, {title}
                        Default: "{trackNumber} - {artist} - {title}"
-u, --underscored-filenames
                        Use underscores instead of spaces in filenames
-c, --internal-track-counter
                        Use internal counter instead of track number
```

### Advanced Options

```
-a, --add-cover-art     Embed cover art into files
-m, --mute-recording    Mute on main output while recording (Linux only)
```

### Usage Examples

```bash
# Record from ncspot in MP3 format with 320kbps
python3 spotrec.py --client ncspot -f mp3 -q 320

# Record a playlist in FLAC format with cover art
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M -a

# Record in OGG format (quality 8) with custom filename pattern
python3 spotrec.py -f ogg -q 8 -p "{artist}/{album}/{trackNumber} {title}"

# Record from ncspot to specific directory with underscored filenames
python3 spotrec.py --client ncspot -o ~/Music/Recordings -u
```


## Hints

- Disable volume normalization in the Spotify Client

- Do not change the volume during recording

- For lossy formats (MP3, OGG, MP4), recordings are transcoded from the stream quality. For best quality, use FLAC and convert later if needed.

- Use Audacity for post processing

  * because SpotRec records a little longer at the end to ensure that nothing is missing of the song. But sometimes this also includes the beginning of the next song. So you should use Audacity to cut the audio to what you want. From Audacity you can also export it to other formats if needed.


## Troubleshooting

Start the script with the debug flag:

```
./spotrec.py --debug
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
  the spotify client
* stop everything and start over, after some tries it usually works :)


**Note: sometimes spotify detects when the user does not interact with the
application for a long time (more or less an hour) and starts looping over a
song, to avoid this scenario I would suggest to keep interacting with the
spotify client.**
