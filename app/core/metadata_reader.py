#core/metadata_reader.py
from pathlib import Path

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis

class MetadataReader:
    """Class for reading metadata of audio files."""    
    def __format_duration(seconds: float) -> str:
        """Formating seconds to str type 'MM:SS' or 'H:MM:SS'."""
        if seconds <= 0:
            return "00:00"
        
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def get_metadata(file_path: Path) -> dict:
        """ Read metadata from audio file.
        Args:
            file_path (Path): Path to file
        Returns:
            dict: metadata {"track", "title", "artist", "album", "cover_data"}
        """
        metadata = {
            "track": 0,
            "title": file_path.stem,
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "song_dur": "00:00",
            "cover_data": None
        }

        try:
            audio = mutagen.File(file_path)
            if audio is None:
                return metadata
            
            if audio.info and hasattr(audio.info, 'length'):
                length = audio.info.length
                metadata['song_dur'] = MetadataReader.__format_duration(length)
            

            if isinstance(audio, MP3):
                # MP3 often requires EasyID3 or direct access to ID3
                tags = audio.tags
                if tags:
                    metadata['title'] = tags.get('TIT2', [metadata['title']])[0]
                    metadata['artist'] = tags.get('TPE1', [metadata['artist']])[0]
                    metadata['album'] = tags.get('TALB', [metadata['album']])[0]
                    
                    # Tracking number can be "1/12" or just "1"
                    trck = tags.get('TRCK')
                    if trck:
                        metadata['track'] = int(str(trck[0]).split('/')[0])
                        
                    # Cover for MP3 (APIC frame)
                    for tag in tags.values():
                        if hasattr(tag, 'FrameID') and tag.FrameID == 'APIC':
                            metadata['cover_data'] = tag.data
                            break

            elif isinstance(audio, (FLAC, OggVorbis)):
                metadata['title'] = audio.get('TITLE', [metadata['title']])[0]
                metadata['artist'] = audio.get('ARTIST', [metadata['artist']])[0]
                metadata['album'] = audio.get('ALBUM', [metadata['album']])[0]
                
                trck = audio.get('TRACKNUMBER')
                if trck:
                    metadata['track'] = int(str(trck[0]).split('/')[0])

                # Cover for FLAC/Vorbis (usually in pictures)
                if hasattr(audio, 'pictures') and audio.pictures:
                    metadata['cover_data'] = audio.pictures[0].data

            elif isinstance(audio, mutagen.wave.WAVE):
                # WAV files can contain ID3 tags or RIFF INFO chunks. Mutagen attempts to abstract this.
                
                # Check for tags (usually ID3v2 inside WAV)
                if audio.tags:
                    metadata['title'] = audio.tags.get('TIT2', [metadata['title']])[0]
                    metadata['artist'] = audio.tags.get('TPE1', [metadata['artist']])[0]
                    metadata['album'] = audio.tags.get('TALB', [metadata['album']])[0]
                    
                    trck = audio.tags.get('TRCK')
                    if trck:
                        metadata['track'] = int(str(trck[0]).split('/')[0])
                        
                    # Cover for WAV (also APIC frame, if there are ID3 tags)
                    for tag in audio.tags.values():
                        if hasattr(tag, 'FrameID') and tag.FrameID == 'APIC':
                            metadata['cover_data'] = tag.data
                            break

        except Exception as e:
            print(f"Error reading metadata for {file_path}: {e}")

        return metadata
    