"""
Сервис для синхронизации файлов с устройствами
"""
import shutil
from pathlib import Path
from typing import List, Callable, Optional, Set
from datetime import datetime

from .audio_file import AudioFile


class SyncService:
    """Сервис для синхронизации музыкальной библиотеки с устройствами"""
    
    @staticmethod
    def get_available_drives() -> List[Path]:
        """
        Возвращает список доступных съемных носителей
        """
        drives = []
        
        # Для Windows
        try:
            import string
            import ctypes
            if hasattr(ctypes, 'windll'):
                bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive_path = Path(f"{letter}:/")
                        if drive_path.exists():
                            # Проверяем, является ли диск съемным
                            drive_type = ctypes.windll.kernel32.GetDriveTypeW(str(drive_path))
                            if drive_type == 2:  # DRIVE_REMOVABLE
                                drives.append(drive_path)
                    bitmask >>= 1
        except:
            pass
        
        # Для Linux
        try:
            media_path = Path('/media')
            if media_path.exists():
                for user_dir in media_path.iterdir():
                    if user_dir.is_dir():
                        for device in user_dir.iterdir():
                            if device.is_dir():
                                drives.append(device)
            
            mnt_path = Path('/mnt')
            if mnt_path.exists():
                for device in mnt_path.iterdir():
                    if device.is_dir() and device.name not in ['wsl', 'wslg']:
                        drives.append(device)
        except:
            pass
        
        return drives
    
    @staticmethod
    def get_device_info(device_path: Path) -> dict:
        """
        Получает информацию об устройстве
        
        Returns:
            Словарь с информацией: name, total_space, free_space
        """
        info = {
            'name': device_path.name,
            'path': device_path,
            'total_space': 0,
            'free_space': 0,
            'used_space': 0
        }
        
        try:
            import shutil
            usage = shutil.disk_usage(device_path)
            info['total_space'] = usage.total
            info['free_space'] = usage.free
            info['used_space'] = usage.used
        except:
            pass
        
        return info
    
    @staticmethod
    def scan_device_files(device_path: Path, progress_callback: Optional[Callable[[str], None]] = None) -> Set[Path]:
        """
        Сканирует файлы на устройстве
        
        Returns:
            Множество относительных путей файлов
        """
        from .tag_service import TagService
        
        files = set()
        try:
            for file_path in device_path.rglob('*'):
                if file_path.is_file() and TagService.is_supported(file_path):
                    rel_path = file_path.relative_to(device_path)
                    files.add(rel_path)
                    if progress_callback:
                        progress_callback(f"Найден: {rel_path}")
        except Exception as e:
            if progress_callback:
                progress_callback(f"Ошибка сканирования: {e}")
        
        return files
    
    @staticmethod
    def calculate_sync_plan(source_files: List[AudioFile], 
                           device_path: Path,
                           organize: bool = True) -> dict:
        """
        Рассчитывает план синхронизации
        
        Returns:
            Словарь с планом: to_copy, to_delete, total_size, existing_files
        """
        plan = {
            'to_copy': [],  # Файлы для копирования
            'to_delete': [],  # Файлы для удаления
            'total_size': 0,
            'existing_files': []
        }
        
        # Создаем карту файлов на устройстве
        device_files = {}
        if device_path.exists():
            existing = SyncService.scan_device_files(device_path)
            for rel_path in existing:
                device_files[rel_path] = device_path / rel_path
        
        # Определяем, какие файлы нужно скопировать
        source_paths = set()
        for audio_file in source_files:
            if organize:
                target_path = audio_file.get_organized_path(device_path)
                rel_path = target_path.relative_to(device_path)
            else:
                rel_path = Path(audio_file.filename)
            
            source_paths.add(rel_path)
            
            if rel_path not in device_files:
                plan['to_copy'].append((audio_file, device_path / rel_path))
                plan['total_size'] += audio_file.size
            else:
                plan['existing_files'].append(rel_path)
        
        # Определяем, какие файлы нужно удалить с устройства
        for rel_path, full_path in device_files.items():
            if rel_path not in source_paths:
                plan['to_delete'].append(full_path)
        
        return plan
    
    @staticmethod
    def sync_to_device(source_files: List[AudioFile],
                      device_path: Path,
                      organize: bool = True,
                      delete_extra: bool = False,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None) -> dict:
        """
        Синхронизирует файлы с устройством
        
        Args:
            source_files: Список файлов для синхронизации
            device_path: Путь к устройству
            organize: Организовать файлы в иерархию
            delete_extra: Удалить лишние файлы с устройства
            progress_callback: Callback для отчета о прогрессе
        
        Returns:
            Словарь с результатами: copied, deleted, failed, skipped
        """
        results = {
            'copied': 0,
            'deleted': 0,
            'failed': 0,
            'skipped': 0
        }
        
        if not device_path.exists():
            return results
        
        # Рассчитываем план
        plan = SyncService.calculate_sync_plan(source_files, device_path, organize)
        
        total_operations = len(plan['to_copy']) + (len(plan['to_delete']) if delete_extra else 0)
        current = 0
        
        # Копируем новые файлы
        for audio_file, target_path in plan['to_copy']:
            current += 1
            try:
                if progress_callback:
                    progress_callback(f"Копирование: {audio_file.filename}", current, total_operations)
                
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(audio_file.path, target_path)
                results['copied'] += 1
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Ошибка: {audio_file.filename} - {e}", current, total_operations)
                results['failed'] += 1
        
        # Удаляем лишние файлы
        if delete_extra:
            for file_path in plan['to_delete']:
                current += 1
                try:
                    if progress_callback:
                        progress_callback(f"Удаление: {file_path.name}", current, total_operations)
                    
                    file_path.unlink()
                    results['deleted'] += 1
                    
                    # Удаляем пустые папки
                    try:
                        file_path.parent.rmdir()
                    except:
                        pass
                        
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Ошибка удаления: {file_path.name} - {e}", current, total_operations)
                    results['failed'] += 1
        
        results['skipped'] = len(plan['existing_files'])
        
        return results
