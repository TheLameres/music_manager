"""
Сервис для чтения и записи метаданных аудиофайлов
"""
from pathlib import Path
from typing import Optional
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from .audio_file import AudioFile


class TagService:
    """Сервис для работы с метаданными аудиофайлов"""
    
    SUPPORTED_FORMATS = ['.mp3', '.flac', '.ogg', '.m4a', '.wma', '.opus', '.ape']
    
    @staticmethod
    def is_supported(file_path: Path) -> bool:
        """Проверяет, поддерживается ли формат файла"""
        return file_path.suffix.lower() in TagService.SUPPORTED_FORMATS
    
    @staticmethod
    def read_tags(file_path: Path) -> Optional[AudioFile]:
        """
        Читает метаданные из аудиофайла
        Возвращает объект AudioFile или None при ошибке
        """
        if not file_path.exists() or not TagService.is_supported(file_path):
            return None
        
        try:
            audio = mutagen.File(file_path)
            if audio is None:
                return None
            
            audio_file = AudioFile(path=file_path)
            
            # Определяем формат
            audio_file.format = type(audio).__name__
            
            # Длительность и битрейт
            if hasattr(audio.info, 'length'):
                audio_file.duration = int(audio.info.length)
            if hasattr(audio.info, 'bitrate'):
                audio_file.bitrate = int(audio.info.bitrate / 1000)
            
            # Читаем теги в зависимости от формата
            if isinstance(audio, mutagen.mp3.MP3):
                TagService._read_mp3_tags(audio, audio_file)
            elif isinstance(audio, FLAC):
                TagService._read_flac_tags(audio, audio_file)
            elif isinstance(audio, MP4):
                TagService._read_mp4_tags(audio, audio_file)
            elif isinstance(audio, OggVorbis):
                TagService._read_ogg_tags(audio, audio_file)
            else:
                # Универсальный метод для других форматов
                TagService._read_generic_tags(audio, audio_file)
            
            return audio_file
            
        except Exception as e:
            print(f"Ошибка чтения тегов {file_path}: {e}")
            return None
    
    @staticmethod
    def _read_mp3_tags(audio, audio_file: AudioFile):
        """Читает теги из MP3"""
        try:
            easy = EasyID3(audio_file.path)
            audio_file.title = easy.get('title', [None])[0]
            audio_file.artist = easy.get('artist', [None])[0]
            audio_file.album = easy.get('album', [None])[0]
            audio_file.year = easy.get('date', [None])[0]
            audio_file.genre = easy.get('genre', [None])[0]
            track = easy.get('tracknumber', [None])[0]
            if track:
                audio_file.track_number = track.split('/')[0].zfill(2)
        except ID3NoHeaderError:
            pass
    
    @staticmethod
    def _read_flac_tags(audio, audio_file: AudioFile):
        """Читает теги из FLAC"""
        audio_file.title = audio.get('title', [None])[0]
        audio_file.artist = audio.get('artist', [None])[0]
        audio_file.album = audio.get('album', [None])[0]
        audio_file.year = audio.get('date', [None])[0]
        audio_file.genre = audio.get('genre', [None])[0]
        track = audio.get('tracknumber', [None])[0]
        if track:
            audio_file.track_number = str(track).split('/')[0].zfill(2)
    
    @staticmethod
    def _read_mp4_tags(audio, audio_file: AudioFile):
        """Читает теги из M4A/MP4"""
        tags = audio.tags
        if tags:
            audio_file.title = tags.get('\xa9nam', [None])[0]
            audio_file.artist = tags.get('\xa9ART', [None])[0]
            audio_file.album = tags.get('\xa9alb', [None])[0]
            audio_file.year = tags.get('\xa9day', [None])[0]
            audio_file.genre = tags.get('\xa9gen', [None])[0]
            track = tags.get('trkn', [None])[0]
            if track:
                audio_file.track_number = str(track[0]).zfill(2)
    
    @staticmethod
    def _read_ogg_tags(audio, audio_file: AudioFile):
        """Читает теги из OGG"""
        audio_file.title = audio.get('title', [None])[0]
        audio_file.artist = audio.get('artist', [None])[0]
        audio_file.album = audio.get('album', [None])[0]
        audio_file.year = audio.get('date', [None])[0]
        audio_file.genre = audio.get('genre', [None])[0]
        track = audio.get('tracknumber', [None])[0]
        if track:
            audio_file.track_number = str(track).split('/')[0].zfill(2)
    
    @staticmethod
    def _read_generic_tags(audio, audio_file: AudioFile):
        """Универсальный метод чтения тегов"""
        if hasattr(audio, 'tags') and audio.tags:
            tags = audio.tags
            audio_file.title = tags.get('title', [None])[0] if hasattr(tags, 'get') else None
            audio_file.artist = tags.get('artist', [None])[0] if hasattr(tags, 'get') else None
            audio_file.album = tags.get('album', [None])[0] if hasattr(tags, 'get') else None
    
    @staticmethod
    def write_tags(audio_file: AudioFile) -> bool:
        """
        Записывает метаданные в аудиофайл
        Возвращает True при успехе, False при ошибке
        """
        try:
            audio = mutagen.File(audio_file.path)
            if audio is None:
                return False
            
            if isinstance(audio, mutagen.mp3.MP3):
                return TagService._write_mp3_tags(audio_file)
            elif isinstance(audio, FLAC):
                return TagService._write_flac_tags(audio_file)
            elif isinstance(audio, MP4):
                return TagService._write_mp4_tags(audio_file)
            elif isinstance(audio, OggVorbis):
                return TagService._write_ogg_tags(audio_file)
            else:
                return TagService._write_generic_tags(audio_file)
                
        except Exception as e:
            print(f"Ошибка записи тегов {audio_file.path}: {e}")
            return False
    
    @staticmethod
    def _write_mp3_tags(audio_file: AudioFile) -> bool:
        """Записывает теги в MP3"""
        try:
            try:
                easy = EasyID3(audio_file.path)
            except ID3NoHeaderError:
                easy = mutagen.File(audio_file.path, easy=True)
                easy.add_tags()
            
            if audio_file.title:
                easy['title'] = audio_file.title
            if audio_file.artist:
                easy['artist'] = audio_file.artist
            if audio_file.album:
                easy['album'] = audio_file.album
            if audio_file.year:
                easy['date'] = audio_file.year
            if audio_file.genre:
                easy['genre'] = audio_file.genre
            if audio_file.track_number:
                easy['tracknumber'] = audio_file.track_number
            
            easy.save()
            return True
        except Exception as e:
            print(f"Ошибка записи MP3 тегов: {e}")
            return False
    
    @staticmethod
    def _write_flac_tags(audio_file: AudioFile) -> bool:
        """Записывает теги в FLAC"""
        try:
            audio = FLAC(audio_file.path)
            if audio_file.title:
                audio['title'] = audio_file.title
            if audio_file.artist:
                audio['artist'] = audio_file.artist
            if audio_file.album:
                audio['album'] = audio_file.album
            if audio_file.year:
                audio['date'] = audio_file.year
            if audio_file.genre:
                audio['genre'] = audio_file.genre
            if audio_file.track_number:
                audio['tracknumber'] = audio_file.track_number
            
            audio.save()
            return True
        except Exception as e:
            print(f"Ошибка записи FLAC тегов: {e}")
            return False
    
    @staticmethod
    def _write_mp4_tags(audio_file: AudioFile) -> bool:
        """Записывает теги в M4A/MP4"""
        try:
            audio = MP4(audio_file.path)
            if audio_file.title:
                audio['\xa9nam'] = audio_file.title
            if audio_file.artist:
                audio['\xa9ART'] = audio_file.artist
            if audio_file.album:
                audio['\xa9alb'] = audio_file.album
            if audio_file.year:
                audio['\xa9day'] = audio_file.year
            if audio_file.genre:
                audio['\xa9gen'] = audio_file.genre
            if audio_file.track_number:
                audio['trkn'] = [(int(audio_file.track_number), 0)]
            
            audio.save()
            return True
        except Exception as e:
            print(f"Ошибка записи MP4 тегов: {e}")
            return False
    
    @staticmethod
    def _write_ogg_tags(audio_file: AudioFile) -> bool:
        """Записывает теги в OGG"""
        try:
            audio = OggVorbis(audio_file.path)
            if audio_file.title:
                audio['title'] = audio_file.title
            if audio_file.artist:
                audio['artist'] = audio_file.artist
            if audio_file.album:
                audio['album'] = audio_file.album
            if audio_file.year:
                audio['date'] = audio_file.year
            if audio_file.genre:
                audio['genre'] = audio_file.genre
            if audio_file.track_number:
                audio['tracknumber'] = audio_file.track_number
            
            audio.save()
            return True
        except Exception as e:
            print(f"Ошибка записи OGG тегов: {e}")
            return False
    
    @staticmethod
    def _write_generic_tags(audio_file: AudioFile) -> bool:
        """Универсальный метод записи тегов"""
        try:
            audio = mutagen.File(audio_file.path)
            if hasattr(audio, 'tags') and audio.tags:
                if audio_file.title:
                    audio.tags['title'] = audio_file.title
                if audio_file.artist:
                    audio.tags['artist'] = audio_file.artist
                if audio_file.album:
                    audio.tags['album'] = audio_file.album
                audio.save()
                return True
            return False
        except Exception as e:
            print(f"Ошибка записи тегов: {e}")
            return False
