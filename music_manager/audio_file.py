"""
Модель для представления аудиофайла с метаданными
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class AudioFile:
    """Представление аудиофайла с метаданными"""
    
    path: Path
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[str] = None
    track_number: Optional[str] = None
    genre: Optional[str] = None
    duration: Optional[int] = None  # в секундах
    bitrate: Optional[int] = None  # в kbps
    format: Optional[str] = None
    
    @property
    def filename(self) -> str:
        """Возвращает имя файла"""
        return self.path.name
    
    @property
    def size(self) -> int:
        """Возвращает размер файла в байтах"""
        try:
            return self.path.stat().st_size
        except:
            return 0
    
    @property
    def size_mb(self) -> float:
        """Возвращает размер файла в мегабайтах"""
        return self.size / (1024 * 1024)
    
    def get_organized_path(self, base_dir: Path) -> Path:
        """
        Возвращает путь для организованного хранения файла
        Формат: {Исполнитель}/{Год} - {Альбом}/{Номер} - {Название}
        """
        artist = self.artist or "Unknown Artist"
        album = self.album or "Unknown Album"
        year = self.year or "0000"
        track = self.track_number or "00"
        title = self.title or self.path.stem
        
        # Очищаем от недопустимых символов
        from pathvalidate import sanitize_filename, sanitize_filepath
        
        artist_dir = sanitize_filename(artist)
        album_dir = sanitize_filename(f"{year} - {album}")
        filename = sanitize_filename(f"{track} - {title}{self.path.suffix}")
        
        return base_dir / artist_dir / album_dir / filename
