#core/metadata_reader.py
from pathlib import Path

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

class MetadataReader:
    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Форматирует секунды в строку вида 'MM:SS' или 'H:MM:SS'.
        Пример: 245.5 -> '04:05'
        """
        # >>> ИЗМЕНЕНИЕ: Новый хелпер для форматирования
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
                metadata['song_dur'] = MetadataReader.format_duration(length)
            

            if isinstance(audio, MP3):
                # MP3 часто требует EasyID3 или прямого доступа к ID3
                tags = audio.tags
                if tags:
                    metadata['title'] = tags.get('TIT2', [metadata['title']])[0]
                    metadata['artist'] = tags.get('TPE1', [metadata['artist']])[0]
                    metadata['album'] = tags.get('TALB', [metadata['album']])[0]
                    
                    # Трек номер может быть "1/12" или просто "1"
                    trck = tags.get('TRCK')
                    if trck:
                        metadata['track'] = int(str(trck[0]).split('/')[0])
                        
                    # Обложка для MP3 (APIC frame)
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

                # Обложка для FLAC/Vorbis (обычно в pictures)
                if hasattr(audio, 'pictures') and audio.pictures:
                    metadata['cover_data'] = audio.pictures[0].data

            elif isinstance(audio, MP4):
                metadata['title'] = audio.get('\xa9nam', [metadata['title']])[0]
                metadata['artist'] = audio.get('\xa9ART', [metadata['artist']])[0]
                metadata['album'] = audio.get('\xa9alb', [metadata['album']])[0]
                
                trck = audio.get('trkn')
                if trck:
                    metadata['track'] = trck[0][0] # В MP4 это кортеж (track, total)

                # Обложка для MP4 (covr)
                cover = audio.get('covr')
                if cover:
                    metadata['cover_data'] = cover[0]

        except Exception as e:
            print(f"Error reading metadata for {file_path}: {e}")

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