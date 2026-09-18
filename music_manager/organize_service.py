"""
Сервис для организации файлов в иерархическую структуру
"""
import shutil
from pathlib import Path
from typing import List, Callable, Optional

from .audio_file import AudioFile


class OrganizeService:
    """Сервис для организации музыкальных файлов"""
    
    @staticmethod
    def organize_file(audio_file: AudioFile, target_dir: Path, 
                     copy: bool = True,
                     progress_callback: Optional[Callable[[str], None]] = None) -> Optional[Path]:
        """
        Организует файл в целевую директорию
        
        Args:
            audio_file: Файл для организации
            target_dir: Целевая директория
            copy: True - копировать, False - перемещать
            progress_callback: Callback для отчета о прогрессе
        
        Returns:
            Путь к новому файлу или None при ошибке
        """
        try:
            new_path = audio_file.get_organized_path(target_dir)
            
            # Создаем директории
            new_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Если файл уже существует, добавляем суффикс
            if new_path.exists() and new_path != audio_file.path:
                stem = new_path.stem
                suffix = new_path.suffix
                counter = 1
                while new_path.exists():
                    new_path = new_path.parent / f"{stem} ({counter}){suffix}"
                    counter += 1
            
            if progress_callback:
                progress_callback(f"Обработка: {audio_file.filename}")
            
            # Копируем или перемещаем
            if new_path != audio_file.path:
                if copy:
                    shutil.copy2(audio_file.path, new_path)
                else:
                    shutil.move(str(audio_file.path), str(new_path))
            
            return new_path
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Ошибка: {audio_file.filename} - {e}")
            return None
    
    @staticmethod
    def organize_files(audio_files: List[AudioFile], target_dir: Path,
                      copy: bool = True,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> dict:
        """
        Организует список файлов
        
        Args:
            audio_files: Список файлов для организации
            target_dir: Целевая директория
            copy: True - копировать, False - перемещать
            progress_callback: Callback для отчета о прогрессе (message, current, total)
        
        Returns:
            Словарь с результатами: {'success': int, 'failed': int, 'skipped': int}
        """
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        total = len(audio_files)
        
        for idx, audio_file in enumerate(audio_files, 1):
            if progress_callback:
                progress_callback(f"Обработка: {audio_file.filename}", idx, total)
            
            result = OrganizeService.organize_file(
                audio_file, 
                target_dir, 
                copy=copy
            )
            
            if result:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        return results
    
    @staticmethod
    def preview_organization(audio_files: List[AudioFile], target_dir: Path) -> List[tuple]:
        """
        Предпросмотр организации файлов
        
        Returns:
            Список кортежей (old_path, new_path)
        """
        preview = []
        for audio_file in audio_files:
            new_path = audio_file.get_organized_path(target_dir)
            preview.append((audio_file.path, new_path))
        return preview
