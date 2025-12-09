# SpotRec

Python script to record the audio of Spotify clients (official Spotify client or ncspot) using FFmpeg.

- **Linux**: Uses PulseAudio for audio routing
- **macOS**: Uses BlackHole virtual audio device for audio routing

Supports both the official Spotify desktop client and ncspot (terminal-based client).

AUR (Linux): https://aur.archlinux.org/packages/spotrec/



## macOS Setup

### Prerequisites

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install required dependencies**:
   ```bash
   brew install python3 ffmpeg dbus pygobject3
   ```

3. **Install BlackHole** (virtual audio device):
   ```bash
   brew install blackhole-2ch
   ```
   Or download from: https://existential.audio/blackhole/

4. **Install ncspot** (recommended for macOS):
   ```bash
   brew install ncspot
   ```

5. **Install Python packages**:
   ```bash
   pip3 install requests dbus-python PyGObject
   ```

### Configure ncspot

Run the provided configuration script to set up ncspot optimally:

```bash
./configure-ncspot.sh
```

This will create a configuration file at `~/Library/Application Support/ncspot/config.toml` with optimal settings for recording.

### Configure Audio Routing (BlackHole)

To record audio while still hearing it through your speakers:

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`)
2. Click the **'+'** button at the bottom left
3. Select **'Create Multi-Output Device'**
4. Check both your regular speakers/headphones **and** **'BlackHole 2ch'**
5. (Optional) Right-click the Multi-Output Device and select "Use This Device For Sound Output"

Now audio will play through your speakers AND be routed to BlackHole for recording.

### Usage on macOS

1. **Start ncspot**:
   ```bash
   ncspot
   ```
   Login with your Spotify credentials if this is your first time.

2. **In another terminal, start SpotRec**:
   ```bash
   python3 spotrec.py --client ncspot -o ~/Music/SpotRec
   ```

3. **Play music in ncspot** - SpotRec will automatically record each track!

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
