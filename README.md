# SpotRec

Python script to record the audio of Spotify clients (official Spotify desktop client or ncspot) using FFmpeg and PulseAudio

AUR: https://aur.archlinux.org/packages/spotrec/



## Usage

### With Official Spotify Client

If you use the AUR package,
you can simply run:

```
spotrec
```

If you have a GNU/Linux distribution with a different package manager system,
run:

```
python3 spotrec.py
```

### With ncspot (Terminal Client)

ncspot is a lightweight, terminal-based Spotify client. To use SpotRec with ncspot:

1. Install ncspot (see [ncspot installation](https://github.com/hrkfdn/ncspot))

2. Configure ncspot for SpotRec:
```bash
./configure-ncspot.sh
```

3. Start ncspot:
```bash
ncspot
```

4. In another terminal, run SpotRec with the `--client ncspot` option:
```bash
python3 spotrec.py --client ncspot
```

### Recording a Specific Playlist

You can specify a playlist ID to automatically start recording:

```bash
# For official Spotify client
python3 spotrec.py --playlist-id 37i9dQZF1DXcBWIGoYBM5M

# For ncspot
python3 spotrec.py --client ncspot --playlist-id 37i9dQZF1DXcBWIGoYBM5M
```

To find a playlist ID:
- Open Spotify Web Player
- Navigate to the playlist
- Copy the ID from the URL: `https://open.spotify.com/playlist/[YOUR_PLAYLIST_ID]`

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
  -u, --underscored-filenames
                        Use underscores instead of spaces in filenames
  -c, --internal-track-counter
                        Use internal track counter (useful for playlists)
  -a, --add-cover-art   Embed cover art into the recorded files
  --client {spotify,ncspot}
                        Spotify client to use (default: spotify)
  --playlist-id PLAYLIST_ID
                        Spotify playlist ID to record
```



### Example

First of all run spotify (or ncspot).

Then you can run the python script which will record the music:

```
./spotrec.py -o ./my_song_dir --skip-intro
```

For ncspot:

```
./spotrec.py --client ncspot -o ./my_song_dir --skip-intro
```

Check the  pulseaudio configuration:

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

- Disable volume normalization in the Spotify Client (or in ncspot's config)

- Do not change the volume during recording

- For ncspot users: The `configure-ncspot.sh` script sets optimal recording settings including:
  - 320 kbps bitrate for best quality
  - Disabled volume normalization
  - PulseAudio backend compatibility

- Use Audacity for post processing

  * because SpotRec records a little longer at the end to ensure that nothing is missing of the song. But sometimes this also includes the beginning of the next song. So you should use Audacity to cut the audio to what you want. From Audacity you can also export it to the format you like (ogg/mp3/...).


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
