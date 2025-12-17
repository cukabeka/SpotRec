#!/usr/bin/python3

# License: https://raw.githubusercontent.com/Bleuzen/SpotRec/master/LICENSE

import json
import tempfile
from pathlib import Path

# Conditional DBus imports
try:
    import dbus
    from dbus.exceptions import DBusException
    import dbus.mainloop.glib
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

from threading import Thread
import subprocess
import time
import sys
import shutil
import re
import os
import argparse
import traceback
import logging
import shlex
import requests
import platform
from urllib.parse import urlparse, parse_qs

# Deps:
# 'python'
# 'ffmpeg'
# Linux: 'gawk': awk in command to get sink input id of spotify
# Linux: 'pulseaudio': sink control stuff
# macOS: 'BlackHole': virtual audio device (https://existential.audio/blackhole/)
# macOS: 'SwitchAudioSource': command-line audio device switcher
# 'bash': shell commands
# 'requests': get album art
# For DBus functionality (Linux, or macOS with official client): 'python-dbus', 'pygobject'


# TODO:
# - set fixed latency on pipewire (currently only done by ffmpeg while it is recording ("fragment_size" parameter), but should ideally be set before recording)

app_name = "SpotRec"
app_version = "0.17.0" # Version bump for new feature

# Settings with Defaults
_debug_logging = False
_skip_intro = False
_mute_pa_recording_sink = False
_output_directory = f"{Path.home()}/{app_name}"
_filename_pattern = "{trackNumber} - {artist} - {title}"
_underscored_filenames = False
_use_internal_track_counter = False
_add_cover_art = False
_client_type = "spotify"  # "spotify" or "ncspot"
_playlist_id = None
_output_format = "flac"  # flac, ogg, mp3, mp4
_audio_quality = "320"  # bitrate for lossy formats
_is_macos = platform.system() == "Darwin"

# Hard-coded settings
_pa_recording_sink_name = "spotrec"
_blackhole_device_name = "BlackHole 2ch"  # macOS virtual audio device
_pa_max_volume = "65536"
_recording_time_before_song = 0.25
_recording_time_after_song = 1.25
_shell_executable = "/bin/bash"  # Default: "/bin/sh"
_shell_encoding = "utf-8"
_ffmpeg_executable = "ffmpeg"  # Example: "/usr/bin/ffmpeg"
_METADATA_FILE = os.path.join(tempfile.gettempdir(), 'spotrec_metadata.json')


# Variables that change during runtime
is_script_paused = False
is_first_playing = True
pa_spotify_sink_input_id = -1
internal_track_counter = 1
is_shutting_down = False
_player_provider = None


def main():
    handle_command_line()

    if not _skip_intro:
        print(app_name + " v" + app_version)
        print("You should not pause, seek or change volume during recording!")
        print("Existing files will be overridden!")
        print("Use --help as argument to see all options.")
        print()
        print("Disclaimer:")
        print('This software is for "educational" purposes only. No responsibility is held or accepted for misuse.')
        print()
        print("Output directory:")
        print(_output_directory)
        print()

    init_log()

    # Create the output directory
    Path(_output_directory).mkdir(
        parents=True, exist_ok=True)

    # Choose the correct metadata provider
    global _player_provider
    if _is_macos and _client_type == 'ncspot':
        log.info(f"[{app_name}] Using ncspot Hook Provider for macOS")
        _player_provider = NcspotHookProvider()
    else:
        if not DBUS_AVAILABLE:
            log.error("D-Bus Python libraries are not installed. Please install 'dbus-python' and 'PyGObject'.")
            sys.exit(1)
        log.info(f"[{app_name}] Using D-Bus Provider")
        _player_provider = DBusProvider()
    
    _player_provider.start()


    # Load PulseAudio sink
    PulseAudio.load_sink()
    _player_provider.init_pa_stuff_if_needed()

    # Keep the main thread alive (to be able to handle KeyboardInterrupt)
    while not is_shutting_down:
        time.sleep(1)


def doExit():
    log.info(f"[{app_name}] Shutting down ...")

    global is_shutting_down
    is_shutting_down = True
    
    if _player_provider:
        _player_provider.stop()

    # Kill all FFmpeg subprocesses
    FFmpeg.killAll()

    # Unload PulseAudio sink
    PulseAudio.unload_sink()

    log.info(f"[{app_name}] Bye")
    os._exit(0)


def handle_command_line():
    global _debug_logging, _skip_intro, _mute_pa_recording_sink, _output_directory
    global _filename_pattern, _underscored_filenames, _use_internal_track_counter
    global _add_cover_art, _client_type, _playlist_id, _output_format, _audio_quality

    parser = argparse.ArgumentParser(
        description=f"{app_name} v{app_version}", formatter_class=argparse.RawTextHelpFormatter)
    # ... (rest of argument parsing is unchanged)
    parser.add_argument("-d", "--debug", help="Print a little more",
                        action="store_true", default=_debug_logging)
    parser.add_argument("-s", "--skip-intro", help="Skip the intro message",
                        action="store_true", default=_skip_intro)
    parser.add_argument("-m", "--mute-recording", help="Mute Spotify on your main output device while recording (Linux only)",
                        action="store_true", default=_mute_pa_recording_sink)
    parser.add_argument("-o", "--output-directory", help="Where to save the recordings\n"
                                                         "Default: " + _output_directory, default=_output_directory)
    parser.add_argument("-p", "--filename-pattern", help="A pattern for the file names of the recordings\n"
                                                         "Available: {artist}, {album}, {trackNumber}, {title}\n"
                                                         "Default: \"" + _filename_pattern + "\"\n"
                                                         "May contain slashes to create sub directories\n"
                                                         "Example: \"{artist}/{album}/{trackNumber} {title}\"", default=_filename_pattern)
    parser.add_argument("-u", "--underscored-filenames", help="Force the file names to have underscores instead of whitespaces",
                        action="store_true", default=_underscored_filenames)
    parser.add_argument("-c", "--internal-track-counter", help="Replace Spotify's trackNumber with own counter. Useable for preserving a playlist file order",
                        action="store_true", default=_use_internal_track_counter)
    parser.add_argument("-a", "--add-cover-art", help="Embed the cover art from Spotify into the file",
                        action="store_true", default=_add_cover_art)
    parser.add_argument("--client", help="Spotify client type: 'spotify' (default), 'ncspot', or 'spotify-player'\n"
                                         "Default: " + _client_type, 
                        choices=["spotify", "ncspot", "spotify-player"], default=_client_type)
    parser.add_argument("--playlist-id", help="Spotify playlist ID or URL to automatically record.\n"
                                              "Example: 37i9dQZF1DXcBWIGoYBM5M or\n"
                                              "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
                        default=_playlist_id)
    parser.add_argument("-f", "--format", help="Output audio format\n"
                                               "Choices: flac, ogg, mp3, mp4\n"
                                               "Default: flac",
                        choices=["flac", "ogg", "mp3", "mp4"], default=_output_format)
    parser.add_argument("-q", "--quality", help="Audio quality/bitrate for lossy formats (mp3, ogg, mp4)\n"
                                                "For mp3/mp4: bitrate in kbps (e.g., 128, 192, 256, 320)\n"
                                                "For ogg: quality level 0-10 (e.g., 6, 8, 10)\n"
                                                "Default: 320",
                        default=_audio_quality)

    args = parser.parse_args()

    _debug_logging = args.debug
    _skip_intro = args.skip_intro
    _mute_pa_recording_sink = args.mute_recording
    _filename_pattern = args.filename_pattern
    _output_directory = args.output_directory
    _underscored_filenames = args.underscored_filenames
    _use_internal_track_counter = args.internal_track_counter
    _add_cover_art = args.add_cover_art
    _client_type = args.client
    _playlist_id = args.playlist_id
    _output_format = args.format
    _audio_quality = args.quality
    
    if _output_format == "ogg":
        try:
            quality_val = float(_audio_quality)
            if quality_val < 0 or quality_val > 10:
                print("Error: OGG quality must be between 0 and 10")
                sys.exit(1)
        except ValueError:
            print("Error: OGG quality must be a number between 0 and 10")
            sys.exit(1)
    elif _output_format in ["mp3", "mp4"]:
        try:
            bitrate_val = int(_audio_quality)
            if bitrate_val < 64 or bitrate_val > 320:
                print("Error: Bitrate for MP3/MP4 must be between 64 and 320 kbps")
                sys.exit(1)
        except ValueError:
            print("Error: Bitrate for MP3/MP4 must be a number")
            sys.exit(1)


def init_log():
    global log
    log = logging.getLogger()
    FORMAT = '%(asctime)-15s - %(levelname)s - %(message)s' if _debug_logging else '%(message)s'
    log.setLevel(logging.DEBUG if _debug_logging else logging.INFO)
    logging.basicConfig(format=FORMAT)
    log.debug("Logger initialized")

class BaseProvider:
    """Base class for metadata providers."""
    def __init__(self):
        self.trackid = None
        self.track = None
        self.playbackstatus = "Stopped"
        self.metadata_artist = ""
        self.metadata_album = ""
        self.metadata_title = ""
        self.metadata_trackNumber = ""
        self.metadata_artUrl = ""
        self.application_name = _client_type
    
    def start(self):
        raise NotImplementedError
        
    def stop(self):
        pass # Optional for providers that don't need cleanup

    def playing_song_changed(self):
        log.info(f"[{_client_type}] Song changed: {self.track}")
        self.start_record()

    def playbackstatus_changed(self):
        log.info(f"[{_client_type}] State changed: {self.playbackstatus}")
        self.init_pa_stuff_if_needed()

    def get_metadata_for_ffmpeg(self):
        return {
            "artist": self.metadata_artist or "",
            "album": self.metadata_album or "",
            "track": (self.metadata_trackNumber or "1").lstrip("0"),
            "title": self.metadata_title or "",
            "cover_url": self.metadata_artUrl or "",
        }

    def get_track(self):
        if not all([self.metadata_artist, self.metadata_album, self.metadata_trackNumber, self.metadata_title]):
            return "unknown_track"

        if _underscored_filenames:
            filename_pattern = re.sub(" - ", "__", _filename_pattern)
        else:
            filename_pattern = _filename_pattern

        ret = str(filename_pattern.format(
            artist=self.metadata_artist.replace("/", "_"),
            album=self.metadata_album.replace("/", "_"),
            trackNumber=self.metadata_trackNumber,
            title=self.metadata_title.replace("/", "_")
        ))

        if _underscored_filenames:
            ret = ret.replace(".", "").lower()
            ret = re.sub(r"[\s\-\[\]()']+", "_", ret)
            ret = re.sub("__+", "__", ret)
        return ret

    def is_playing(self):
        return self.playbackstatus in ["Playing", "change", "play"]

    def start_record(self):
        raise NotImplementedError

    def stop_old_recording(self, instances):
        if len(instances) > 0:
            class OverheadRecordingStopThread(Thread):
                def run(self):
                    time.sleep(_recording_time_after_song)
                    instances[0].stop_blocking()
            overhead_recording_stop_thread = OverheadRecordingStopThread()
            overhead_recording_stop_thread.start()

    def init_pa_stuff_if_needed(self):
        if self.is_playing():
            global is_first_playing
            if is_first_playing:
                is_first_playing = False
                log.debug(f"[{app_name}] Initializing PulseAudio stuff")
                PulseAudio.init_spotify_sink_input_id()
                PulseAudio.set_sink_volumes_to_100()
                PulseAudio.move_spotify_to_own_sink()

class NcspotHookProvider(BaseProvider):
    """Metadata provider for ncspot on macOS using a file hook."""
    def __init__(self):
        super().__init__()
        self._polling_thread = None
        self._last_mtime = 0
        log.info(f"[{app_name}] Waiting for song change from ncspot...")
        log.info(f"[{app_name}] Make sure you start ncspot with the hook:")
        log.info(f"ncspot --on-song-change-hook \"{os.path.abspath('ncspot_hook.py')}\"")


    def start(self):
        self._polling_thread = Thread(target=self.poll_file, daemon=True)
        self._polling_thread.start()

    def stop(self):
        # The thread is a daemon, so it will exit automatically.
        pass
    
    def poll_file(self):
        while not is_shutting_down:
            try:
                if os.path.exists(_METADATA_FILE):
                    mtime = os.path.getmtime(_METADATA_FILE)
                    if mtime > self._last_mtime:
                        self._last_mtime = mtime
                        with open(_METADATA_FILE, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        self.process_metadata(data)
            except (IOError, json.JSONDecodeError):
                pass # Ignore errors if file is being written or malformed
            time.sleep(0.5)

    def process_metadata(self, data):
        new_trackid = data.get('trackid')
        if not new_trackid:
            return

        new_playbackstatus = data.get('playbackStatus')

        if self.trackid != new_trackid:
            self.metadata_artist = data.get('artist', 'Unknown Artist')
            self.metadata_album = data.get('album', 'Unknown Album')
            self.metadata_title = data.get('title', 'Unknown Title')
            self.metadata_trackNumber = str(data.get('trackNumber', '1')).zfill(2)
            self.metadata_artUrl = data.get('artUrl', '')
            
            global internal_track_counter
            if _use_internal_track_counter:
                self.metadata_trackNumber = str(internal_track_counter).zfill(3)
                internal_track_counter += 1

            self.trackid = new_trackid
            self.track = self.get_track()
            self.playbackstatus = new_playbackstatus
            self.playing_song_changed()

        elif self.playbackstatus != new_playbackstatus:
            self.playbackstatus = new_playbackstatus
            self.playbackstatus_changed()

    def start_record(self):
        class RecordThread(Thread):
            def __init__(self, parent, *args):
                Thread.__init__(self)
                self.parent = parent

            def run(self):
                if not self.parent.is_playing():
                    log.info(f"[{app_name}] ncspot is not playing. Maybe the current album or playlist has ended.")
                    return

                if self.parent.trackid and self.parent.trackid.startswith("spotify:ad:"):
                    log.debug(f"[{app_name}] Skipping ad")
                    return
                
                log.info(f"[{app_name}] Starting recording")
                
                self.parent.stop_old_recording(FFmpeg.instances.copy())

                out_dir = os.path.join(_output_directory, os.path.dirname(self.parent.track))
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                
                ff = FFmpeg()
                ff.record(out_dir, self.parent.track, self.parent.get_metadata_for_ffmpeg())

        record_thread = RecordThread(self)
        record_thread.start()

class DBusProvider(BaseProvider):
    """Metadata provider using D-Bus (for Linux or official Spotify client on macOS)."""
    def __init__(self):
        super().__init__()
        self.glibloop = None
        
        if _client_type == "ncspot":
            self.dbus_dest = "org.mpris.MediaPlayer2.ncspot"
        elif _client_type == "spotify-player":
            self.dbus_dest = "org.mpris.MediaPlayer2.spotify-player"
        else:
            self.dbus_dest = "org.mpris.MediaPlayer2.spotify"
        
        self.dbus_path = "/org/mpris/MediaPlayer2"
        self.mpris_player_string = "org.mpris.MediaPlayer2.Player"
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        try:
            bus = dbus.SessionBus()
            player = bus.get_object(self.dbus_dest, self.dbus_path)
            self.iface = dbus.Interface(player, "org.freedesktop.DBus.Properties")
            self.pull_metadata()
            self.update_metadata()
        except DBusException as e:
            log.debug(e)
            log.error(f"Error: Could not connect to the D-Bus interface for {_client_type}.")
            if _client_type == 'ncspot':
                log.error("This can happen if ncspot is not configured correctly.")
                log.error("Please ensure you have enabled the MPRIS interface in ncspot's config file.")
                log.error("Run './configure-ncspot.sh' to create a valid configuration, then restart ncspot.")
            else:
                log.error(f"Please ensure the {_client_type} client is running.")
            sys.exit(1)
        
        if _playlist_id:
            self.load_playlist(_playlist_id)

        self.track = self.get_track()
        self.trackid = self.metadata.get(dbus.String(u'mpris:trackid'))
        self.playbackstatus = self.iface.Get(self.mpris_player_string, "PlaybackStatus")
        self.iface.connect_to_signal("PropertiesChanged", self.on_playing_uri_changed)

    def start(self):
        class DBusListenerThread(Thread):
            def __init__(self, parent):
                Thread.__init__(self)
                self.parent = parent
            def run(self):
                self.parent.glibloop = GLib.MainLoop()
                self.parent.glibloop.run()
                log.info(f"[{app_name}] GLib Loop thread killed")
        
        dbuslistener = DBusListenerThread(self)
        dbuslistener.start()
        log.info(f"[{app_name}] {_client_type} D-Bus listener started")
        log.info(f"[{app_name}] Current song: {self.track}")
        log.info(f"[{app_name}] Current state: {self.playbackstatus}")

    def stop(self):
        if self.glibloop is not None:
            self.glibloop.quit()
        log.info(f"[{app_name}] D-Bus listener stopped")
    
    def load_playlist(self, playlist_input):
        playlist_id = playlist_input
        if "open.spotify.com/playlist/" in playlist_input or "spotify.com/playlist/" in playlist_input:
            try:
                parsed_url = urlparse(playlist_input)
                path_parts = parsed_url.path.split('/')
                if 'playlist' in path_parts:
                    playlist_id = path_parts[path_parts.index('playlist') + 1]
            except Exception as e:
                log.warning(f"[{app_name}] Could not parse playlist URL: {e}")
                return
        
        playlist_uri = f"spotify:playlist:{playlist_id}"
        log.info(f"[{app_name}] Loading playlist: {playlist_uri}")
        try:
            self.send_dbus_cmd(f'OpenUri string:{shlex.quote(playlist_uri)}')
            time.sleep(2)
        except Exception as e:
            log.warning(f"[{app_name}] Could not load playlist: {e}")

    def send_dbus_cmd(self, cmd):
        Shell.run(f'dbus-send --print-reply --dest={self.dbus_dest} {self.dbus_path} {self.mpris_player_string}.{cmd}')

    def on_playing_uri_changed(self, Player, three, four):
        self.pull_metadata()
        new_trackid = self.metadata.get(dbus.String(u'mpris:trackid'))
        if self.trackid != new_trackid:
            self.update_metadata()
            self.trackid = new_trackid
            self.track = self.get_track()
            self.playing_song_changed()
            if _use_internal_track_counter:
                global internal_track_counter
                internal_track_counter += 1

        new_playbackstatus = self.iface.Get(Player, "PlaybackStatus")
        if self.playbackstatus != new_playbackstatus:
            self.playbackstatus = new_playbackstatus
            self.playbackstatus_changed()

    def pull_metadata(self):
        self.metadata = self.iface.Get(self.mpris_player_string, "Metadata")

    def update_metadata(self):
        self.metadata_artist = ", ".join(self.metadata.get(dbus.String(u'xesam:artist'), ['']))
        self.metadata_album = self.metadata.get(dbus.String(u'xesam:album'), '')
        self.metadata_title = self.metadata.get(dbus.String(u'xesam:title'), '')
        self.metadata_trackNumber = str(self.metadata.get(dbus.String(u'xesam:trackNumber'), '1')).zfill(2)
        self.metadata_artUrl = str(self.metadata.get(dbus.String(u'mpris:artUrl'), '')).replace("https://open.spotify.com/image/", "https://i.scdn.co/image/")
        
        if _use_internal_track_counter:
            global internal_track_counter
            self.metadata_trackNumber = str(internal_track_counter).zfill(3)
    
    def start_record(self):
        class RecordThread(Thread):
            def __init__(self, parent, *args):
                Thread.__init__(self)
                self.parent = parent
            def run(self):
                global is_script_paused
                trackid_when_started = self.parent.trackid
                
                self.parent.stop_old_recording(FFmpeg.instances.copy())
                
                time.sleep(5.0) # _playback_time_before_seeking_to_beginning

                if trackid_when_started != self.parent.trackid: return
                if not self.parent.is_playing():
                    log.info(f"[{app_name}] Client is paused. Maybe the playlist ended.")
                    if not is_script_paused: doExit()
                    return
                if self.parent.trackid.startswith("spotify:ad:"):
                    log.debug(f"[{app_name}] Skipping ad")
                    return

                log.info(f"[{app_name}] Starting recording")
                is_script_paused = True
                self.parent.send_dbus_cmd("Pause")
                
                out_dir = os.path.join(_output_directory, os.path.dirname(self.parent.track))
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                
                is_script_paused = False
                self.parent.send_dbus_cmd("Previous")
                
                ff = FFmpeg()
                ff.record(out_dir, self.parent.track, self.parent.get_metadata_for_ffmpeg())
                
                time.sleep(_recording_time_before_song)
                self.parent.send_dbus_cmd("Play")

        record_thread = RecordThread(self)
        record_thread.start()





class FFmpeg:
    instances = []

    def record(self, out_dir: str, file: str, metadata_for_file={}):
        self.out_dir = out_dir

        # Determine audio input based on platform
        if _is_macos:
            # macOS uses BlackHole virtual audio device
            self.audio_input = _blackhole_device_name
            self.input_format = 'avfoundation'
        else:
            # Linux uses PulseAudio
            self.audio_input = _pa_recording_sink_name + ".monitor"
            self.input_format = 'pulse'

        # Use a dot as filename prefix to hide the file until the recording was successful
        self.tmp_file_prefix = "."
        self.filename = self.tmp_file_prefix + \
            os.path.basename(file) + "." + _output_format

        # save this to self because metadata_params is discarded after this function
        self.cover_url = metadata_for_file.pop('cover_url')
        # build metadata param
        metadata_params = ''
        for key, value in metadata_for_file.items():
            metadata_params += ' -metadata ' + key + '=' + shlex.quote(str(value))

        # FFmpeg encoding options based on format
        codec_params = self._get_codec_params()

        # FFmpeg Options:
        #  "-hide_banner": short the debug log a little
        #  "-y": overwrite existing files
        #  "-ac 2": always use 2 audio channels (stereo) (same as Spotify)
        #  "-ar 44100": always use 44.1k samplerate (same as Spotify)
        if _is_macos:
            # macOS doesn't use fragment_size
            # avfoundation format uses ':device_name' syntax
            # Device name comes from hardcoded constant but escape for robustness
            escaped_device = shlex.quote(self.audio_input)
            self.process = Shell.Popen(_ffmpeg_executable + ' -hide_banner -y '
                                       f'-f {self.input_format} ' +
                                       '-ac 2 -ar 44100 ' +
                                       f'-i ":{escaped_device}" ' + metadata_params + ' ' +
                                       codec_params +
                                       ' ' + shlex.quote(os.path.join(self.out_dir, self.filename)))
        else:
            #  "-fragment_size 8820": set recording latency to 50 ms (0.05*44100*2*2) (very high values can cause ffmpeg to not stop fast enough, so post-processing fails)
            self.process = Shell.Popen(_ffmpeg_executable + ' -hide_banner -y '
                                       f'-f {self.input_format} ' +
                                       '-ac 2 -ar 44100 -fragment_size 8820 ' +
                                       '-i ' + shlex.quote(self.audio_input) + metadata_params + ' ' +
                                       codec_params +
                                       ' ' + shlex.quote(os.path.join(self.out_dir, self.filename)))

        self.pid = str(self.process.pid)

        self.instances.append(self)

        log.info(f"[FFmpeg] [{self.pid}] Recording started")
    
    def _get_codec_params(self):
        """Get FFmpeg codec parameters based on output format and quality"""
        if _output_format == "flac":
            return "-acodec flac"
        elif _output_format == "ogg":
            # For ogg, quality is 0-10 scale
            return f"-acodec libvorbis -qscale:a {_audio_quality}"
        elif _output_format == "mp3":
            # For mp3, bitrate in kbps
            return f"-acodec libmp3lame -b:a {_audio_quality}k"
        elif _output_format == "mp4":
            # For mp4/m4a with AAC codec
            return f"-acodec aac -b:a {_audio_quality}k"
        else:
            # Default to FLAC
            return "-acodec flac"

    # The blocking version of this method waits until the process is dead
    def stop_blocking(self):
        # Remove from instances list (and terminate)
        if self in self.instances:
            self.instances.remove(self)

            # Send CTRL_C
            self.process.terminate()

            log.info(f"[FFmpeg] [{self.pid}] terminated")

            # Sometimes this is not enough and ffmpeg survives, so we have to kill it after some time
            time.sleep(1)

            if self.process.poll() == None:
                # None means it has no return code (yet), with other words: it is still running

                self.process.kill()

                log.info(f"[FFmpeg] [{self.pid}] killed")
            else:
                global is_shutting_down
                if not is_shutting_down:  # Do not post-process unfinished recordings
                    tmp_file = os.path.join(
                        self.out_dir, self.filename)
                    new_file = os.path.join(self.out_dir,
                                            self.filename[len(self.tmp_file_prefix):])
                    if os.path.exists(tmp_file):
                        shutil.move(tmp_file, new_file)
                        log.debug(
                            f"[FFmpeg] [{self.pid}] Successfully renamed {self.filename}")
                        global _add_cover_art
                        if _add_cover_art:
                            class AddCoverArtThread(Thread):
                                def __init__(self, parent, fullfilepath):
                                    Thread.__init__(self)
                                    self.parent = parent
                                    self.fullfilepath = fullfilepath

                                def run(self):
                                    self.parent.add_cover_art(
                                        self.fullfilepath)

                            add_cover_art_thread = AddCoverArtThread(
                                self, new_file)
                            add_cover_art_thread.start()
                    else:
                        log.warning(
                            f"[FFmpeg] [{self.pid}] Failed renaming {self.filename}")

            # Remove process from memory (and don't left a ffmpeg 'zombie' process)
            self.process = None

    # Kill the process in the background
    def stop(self):
        class KillThread(Thread):
            def __init__(self, parent, *args):
                Thread.__init__(self)
                self.parent = parent

            def run(self):
                self.parent.stop_blocking()

        kill_thread = KillThread(self)
        kill_thread.start()

    # add cover art to temp _withArtwork file
    # and then move it to replace the original file
    def add_cover_art(self, fullfilepath):
        if self.cover_url is None:
            log.debug(f'[FFmpeg] No cover art found for {fullfilepath}')
            return
        # save the image locally -> could use a temp file here
        #   but might add option to keep image later
        cover_file = fullfilepath.rsplit(
            f'.{_output_format}', 1)[0]  # remove the extension
        log.debug(f'Saving cover art to {cover_file} + image_ext')
        temp_file = cover_file + '_withArtwork.' + _output_format
        if self.cover_url.startswith('file://'):
            log.debug(f'[FFmpeg] Cover art is local for {fullfilepath}')
            path = self.cover_url[len('file://'):]
            _, ext = os.path.splitext(path)
            cover_file += ext
            shutil.copy2(path, cover_file)
        else:
            log.debug(f'[FFmpeg] Cover art is on server for {fullfilepath}')
            answer = requests.get(self.cover_url)
            if not answer.ok:
                log.debug(
                    f'[FFmpeg] Cover art not loaded from server for {fullfilepath}')
                return
            cover_file += "." + answer.headers["Content-Type"].rsplit("/")[-1]
            with open(cover_file, "wb") as fd:
                fd.write(answer.content)
        # add it to a temporary file
        log.debug(f'[FFmpeg] Merging cover art into {fullfilepath}')
        # no need for separate thread / logging here because quick
        returncode = Shell.run(_ffmpeg_executable + ' ' +
                               '-y -i {} -i {} -map 0:a -map 1 '.format(
                                   shlex.quote(fullfilepath), shlex.quote(cover_file)) +
                               '-codec copy -id3v2_version 3 ' +
                               '-metadata:s:v title="Album cover" ' +
                               '-metadata:s:v comment="Cover (front)" ' +
                               '-disposition:v attached_pic ' +
                               shlex.quote(temp_file)).returncode
        if returncode != 0:
            log.warning(f"[FFmpeg] Failed adding artwork to {fullfilepath}")
            return
        # overwrite the actual file by the temp file
        log.debug(
            f'[FFmpeg] Added cover art for {fullfilepath} in temp file, moving it')
        shutil.move(temp_file, fullfilepath)
        os.remove(cover_file)   # now delete the cover art

    @staticmethod
    def killAll():
        log.info("[FFmpeg] Killing all instances")

        # Run as long as list ist not empty
        while FFmpeg.instances:
            FFmpeg.instances[0].stop_blocking()

        log.info("[FFmpeg] All instances killed")


class Shell:
    @staticmethod
    def run(cmd):
        # 'run()' waits until the process is done
        log.debug(f"[Shell] run: {cmd}")
        if _debug_logging:
            return subprocess.run(cmd.encode(_shell_encoding), stdin=None, shell=True, executable=_shell_executable, encoding=_shell_encoding)
        else:
            return subprocess.run(cmd.encode(_shell_encoding), stdin=None, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable=_shell_executable, encoding=_shell_encoding)

    @staticmethod
    def Popen(cmd):
        # 'Popen()' continues running in the background
        log.debug(f"[Shell] Popen: {cmd}")
        if _debug_logging:
            return subprocess.Popen(cmd.encode(_shell_encoding), stdin=None, shell=True, executable=_shell_executable, encoding=_shell_encoding)
        else:
            return subprocess.Popen(cmd.encode(_shell_encoding), stdin=None, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, executable=_shell_executable, encoding=_shell_encoding)

    @staticmethod
    def check_output(cmd):
        log.debug(f"[Shell] check_output: {cmd}")
        out = subprocess.check_output(cmd.encode(
            _shell_encoding), shell=True, executable=_shell_executable, encoding=_shell_encoding)
        # when not using 'encoding=' -> out.decode()
        # but since it is set, decode() ist not needed anymore
        # out = out.decode()
        return out.rstrip('\n')


class PulseAudio:
    sink_id = ""

    @staticmethod
    def load_sink():
        if _is_macos:
            log.info(f"[{app_name}] macOS detected - assuming BlackHole is installed")
            # On macOS, BlackHole should already be installed and configured
            # No need to create a virtual sink like on Linux
            return
        
        log.info(f"[{app_name}] Creating pulse sink")

        if _mute_pa_recording_sink:
            PulseAudio.sink_id = Shell.check_output('pactl load-module module-null-sink sink_name="' + _pa_recording_sink_name +
                                                    '" sink_properties=device.description="' + _pa_recording_sink_name + '" rate=44100 channels=2')
        else:
            PulseAudio.sink_id = Shell.check_output('pactl load-module module-remap-sink sink_name="' + _pa_recording_sink_name +
                                                    '" sink_properties=device.description="' + _pa_recording_sink_name + '" rate=44100 channels=2 remix=no')
            # To use another master sink where to play:
            # pactl load-module module-remap-sink sink_name=spotrec sink_properties=device.description="spotrec" master=MASTER_SINK_NAME channels=2 remix=no

    @staticmethod
    def unload_sink():
        if _is_macos:
            log.info(f"[{app_name}] macOS - no sink to unload")
            return
        
        log.info(f"[{app_name}] Unloading pulse sink")
        Shell.run('pactl unload-module ' + PulseAudio.sink_id)

    @staticmethod
    def init_spotify_sink_input_id():
        if _is_macos:
            # macOS doesn't need to find sink input ID
            return
        
        global pa_spotify_sink_input_id

        if pa_spotify_sink_input_id > -1:
            return

        # Use the application name based on client type
        application_name = _player_provider.application_name if _player_provider else _client_type
        cmdout = Shell.check_output(
            "pactl list sink-inputs | awk '{print tolower($0)};' | awk '/ #/ {print $0} /application.name = \"" + application_name + "\"/ {print $3};'")
        index = -1
        last = ""

        for line in cmdout.split('\n'):
            if line == '"' + application_name + '"':
                index = last.split(" #", 1)[1]
                break
            last = line

        pa_spotify_sink_input_id = int(index)

    @staticmethod
    def move_spotify_to_own_sink():
        if _is_macos:
            # macOS: use SwitchAudioSource to route audio to BlackHole
            class SetBlackHoleThread(Thread):
                def run(self):
                    # Try to set the audio output to BlackHole for the application
                    # Note: This requires the user to manually configure their audio routing
                    # or use tools like BlackHole + Multi-Output Device
                    log.info(f"[{app_name}] macOS: Please ensure {_client_type} is routed to BlackHole")
                    log.info(f"[{app_name}] You can use Audio MIDI Setup to create a Multi-Output Device")
            
            set_blackhole_thread = SetBlackHoleThread()
            set_blackhole_thread.start()
            return
        
        class MoveSpotifyToSinkThread(Thread):
            def run(self):
                if pa_spotify_sink_input_id > -1:
                    exit_code = Shell.run("pactl move-sink-input " + str(
                        pa_spotify_sink_input_id) + " " + _pa_recording_sink_name).returncode

                    if exit_code == 0:
                        log.info(f"[{app_name}] Moved Spotify to own sink")
                    else:
                        log.warning(
                            f"[{app_name}] Failed to move Spotify to own sink")

        move_spotify_to_sink_thread = MoveSpotifyToSinkThread()
        move_spotify_to_sink_thread.start()

    @staticmethod
    def set_sink_volumes_to_100():
        if _is_macos:
            # macOS volume control is handled differently
            log.debug(f"[{app_name}] macOS: Volume control not implemented")
            return
        
        log.debug(f"[{app_name}] Set sink volumes to 100%")

        # Set Spotify volume to 100%
        Shell.Popen("pactl set-sink-input-volume " +
                    str(pa_spotify_sink_input_id) + " " + _pa_max_volume)

        # Set recording sink volume to 100%
        Shell.Popen("pactl set-sink-volume " +
                    _pa_recording_sink_name + " " + _pa_max_volume)


if __name__ == "__main__":
    # Handle exit (not print error when pressing Ctrl^C)
    try:
        main()
    except KeyboardInterrupt:
        doExit()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)
    sys.exit(0)
