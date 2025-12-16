#!/usr/bin/env python3

import os
import json
import tempfile

# This script is called by ncspot's --on-song-change-hook
# It receives song metadata via environment variables and writes them to a JSON file
# for the main spotrec.py process to read.

METADATA_FILE = os.path.join(tempfile.gettempdir(), 'spotrec_metadata.json')

def main():
    # ncspot sets environment variables like TRACK_ID, TRACK_ARTIST, etc.
    metadata = {
        'artist': os.environ.get('TRACK_ARTIST'),
        'album': os.environ.get('TRACK_ALBUM'),
        'title': os.environ.get('TRACK_TITLE'),
        'trackNumber': os.environ.get('TRACK_NUM'),
        'artUrl': os.environ.get('COVER_URL'),
        'playbackStatus': os.environ.get('PLAYER_EVENT'), # e.g., 'change', 'play', 'pause'
        'trackid': os.environ.get('TRACK_ID'),
    }

    # Only write to file if we have a valid track ID
    if metadata['trackid']:
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
        except Exception:
            # If something goes wrong, we don't want to crash ncspot
            pass

if __name__ == "__main__":
    main()
