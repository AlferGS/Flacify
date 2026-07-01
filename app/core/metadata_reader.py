from pathlib import Path

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

class MetadataReader:
    @staticmethod
    def get_metadata(file_path: Path) -> dict:
        """ Read metadata from audio file.
        
        Args:
            file_path (Path): Path to file

        Returns:
            dict: metadata {"title", "artist", "album", "cover_data"}
        """
        metadata = {
            "title": file_path.stem,
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "cover_data": None
        }

        try:
            audio = mutagen.File(file_path, easy=True)
            if audio is None:
                return metadata
            
            if "title" in audio and audio["title"]:
                metadata["title"] = str(audio["title"][0])
            if "artist" in audio and audio["artist"]:
                metadata["artist"] = str(audio["artist"][0])
            if "album" in audio and audio["album"]:
                metadata["album"] = str(audio["album"][0])
            
            # Попытка извлечь обложку (зависит от формата)
            metadata["cover_data"] = MetadataReader._extract_cover(file_path)

        except Exception as e:
            print(f"Error reading metadata for {file_path.name}: {e}")

        return metadata
    
    @staticmethod
    def _extract_cover(file_path: Path) -> bytes | None:
        """
        Try to extract cover from audio file
        """
        try:
            audio = mutagen.File(file_path)
            if not audio:
                return None

            # MP3 (ID3)
            if isinstance(audio, MP3):
                if audio.tags and "APIC:" in audio.tags:
                    # Берем первую найденную картинку
                    return audio.tags["APIC:"].data
            
            # FLAC
            elif isinstance(audio, FLAC):
                if audio.pictures:
                    return audio.pictures[0].data

            # OGG Vorbis
            elif isinstance(audio, OggVorbis):
                # В OGG обложки часто хранятся в тегах METADATA_BLOCK_PICTURE
                # Mutagen может не распаковывать их автоматически в easy-режиме,
                # но можно попробовать прочитать сырые теги
                pass 

            # MP4 (M4A/AAC)
            elif isinstance(audio, MP4):
                if "covr" in audio:
                    return audio["covr"][0]

        except Exception as e:
            print(f"Error extracting cover: {e}")
        
        return None