"""
Примеры использования API Music Manager
"""

# Пример 1: Чтение тегов из файла
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService
from music_manager.audio_file import AudioFile

# Чтение одного файла
file_path = Path("/path/to/music/song.mp3")
audio_file = TagService.read_tags(file_path)

if audio_file:
    print(f"Название: {audio_file.title}")
    print(f"Исполнитель: {audio_file.artist}")
    print(f"Альбом: {audio_file.album}")
    print(f"Год: {audio_file.year}")
    print(f"Трек: {audio_file.track_number}")
    print(f"Размер: {audio_file.size_mb:.2f} МБ")


# Пример 2: Изменение тегов
# ====================================

from music_manager.tag_service import TagService

# Читаем файл
audio_file = TagService.read_tags(Path("/path/to/song.mp3"))

# Изменяем теги
audio_file.title = "Новое название"
audio_file.artist = "Новый исполнитель"
audio_file.album = "Новый альбом"
audio_file.year = "2024"
audio_file.track_number = "01"

# Сохраняем
if TagService.write_tags(audio_file):
    print("Теги успешно сохранены")
else:
    print("Ошибка сохранения тегов")


# Пример 3: Пакетная обработка папки
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService

def process_folder(folder_path: Path):
    """Обрабатывает все аудиофайлы в папке"""
    audio_files = []
    
    # Ищем все поддерживаемые файлы
    for ext in TagService.SUPPORTED_FORMATS:
        audio_files.extend(folder_path.rglob(f"*{ext}"))
    
    print(f"Найдено файлов: {len(audio_files)}")
    
    # Читаем теги
    for file_path in audio_files:
        audio_file = TagService.read_tags(file_path)
        if audio_file:
            print(f"{audio_file.filename}: {audio_file.artist} - {audio_file.title}")

# Использование
process_folder(Path("/path/to/music"))


# Пример 4: Организация библиотеки
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService
from music_manager.organize_service import OrganizeService

# Источник
source_folder = Path("/path/to/unorganized/music")
# Назначение
target_folder = Path("/path/to/organized/music")

# Собираем файлы
audio_files = []
for ext in TagService.SUPPORTED_FORMATS:
    for file_path in source_folder.rglob(f"*{ext}"):
        audio_file = TagService.read_tags(file_path)
        if audio_file:
            audio_files.append(audio_file)

print(f"Найдено файлов: {len(audio_files)}")

# Предпросмотр
preview = OrganizeService.preview_organization(audio_files, target_folder)
for old_path, new_path in preview[:5]:  # Показываем первые 5
    print(f"{old_path} -> {new_path}")

# Организуем (копируем)
def progress_callback(message, current, total):
    print(f"[{current}/{total}] {message}")

results = OrganizeService.organize_files(
    audio_files,
    target_folder,
    copy=True,  # True = копировать, False = переместить
    progress_callback=progress_callback
)

print(f"Успешно: {results['success']}")
print(f"Ошибок: {results['failed']}")


# Пример 5: Синхронизация с устройством
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService
from music_manager.sync_service import SyncService

# Получаем список доступных устройств
devices = SyncService.get_available_drives()
print("Доступные устройства:")
for device in devices:
    info = SyncService.get_device_info(device)
    print(f"  {device}: {info['free_space'] / (1024**3):.1f} ГБ свободно")

# Выбираем устройство
device_path = devices[0] if devices else Path("/mnt/usb")

# Загружаем библиотеку
library_folder = Path("/path/to/music/library")
audio_files = []
for ext in TagService.SUPPORTED_FORMATS:
    for file_path in library_folder.rglob(f"*{ext}"):
        audio_file = TagService.read_tags(file_path)
        if audio_file:
            audio_files.append(audio_file)

# Предпросмотр синхронизации
plan = SyncService.calculate_sync_plan(audio_files, device_path, organize=True)
print(f"Файлов для копирования: {len(plan['to_copy'])}")
print(f"Размер: {plan['total_size'] / (1024**2):.1f} МБ")
print(f"Файлов для удаления: {len(plan['to_delete'])}")

# Синхронизируем
def sync_progress(message, current, total):
    print(f"[{current}/{total}] {message}")

results = SyncService.sync_to_device(
    audio_files,
    device_path,
    organize=True,        # Организовать в иерархию
    delete_extra=False,   # Не удалять лишние файлы
    progress_callback=sync_progress
)

print(f"Скопировано: {results['copied']}")
print(f"Удалено: {results['deleted']}")
print(f"Пропущено: {results['skipped']}")


# Пример 6: Массовое изменение тегов альбома
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService

def update_album_tags(folder: Path, album_name: str, artist: str, year: str):
    """Обновляет теги всех файлов в папке альбома"""
    
    files = []
    for ext in TagService.SUPPORTED_FORMATS:
        files.extend(folder.glob(f"*{ext}"))
    
    success_count = 0
    for file_path in sorted(files):
        audio_file = TagService.read_tags(file_path)
        if not audio_file:
            continue
        
        # Обновляем общие теги
        audio_file.album = album_name
        audio_file.artist = artist
        audio_file.year = year
        
        # Если нет номера трека, присваиваем по порядку
        if not audio_file.track_number:
            track_num = files.index(file_path) + 1
            audio_file.track_number = str(track_num).zfill(2)
        
        if TagService.write_tags(audio_file):
            success_count += 1
            print(f"✓ {file_path.name}")
        else:
            print(f"✗ {file_path.name}")
    
    print(f"\nОбновлено: {success_count}/{len(files)}")

# Использование
update_album_tags(
    Path("/path/to/album/folder"),
    album_name="Greatest Hits",
    artist="Famous Band",
    year="2024"
)


# Пример 7: Поиск файлов без тегов
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService

def find_untagged_files(folder: Path):
    """Находит файлы с неполными тегами"""
    
    untagged = []
    
    for ext in TagService.SUPPORTED_FORMATS:
        for file_path in folder.rglob(f"*{ext}"):
            audio_file = TagService.read_tags(file_path)
            
            if audio_file:
                # Проверяем наличие основных тегов
                if not audio_file.title or not audio_file.artist or not audio_file.album:
                    untagged.append({
                        'path': file_path,
                        'title': audio_file.title,
                        'artist': audio_file.artist,
                        'album': audio_file.album
                    })
    
    return untagged

# Использование
untagged = find_untagged_files(Path("/path/to/music"))
print(f"Файлов без полных тегов: {len(untagged)}")
for item in untagged[:10]:  # Показываем первые 10
    print(f"  {item['path'].name}")
    print(f"    Title: {item['title'] or 'MISSING'}")
    print(f"    Artist: {item['artist'] or 'MISSING'}")
    print(f"    Album: {item['album'] or 'MISSING'}")


# Пример 8: Статистика библиотеки
# ====================================

from pathlib import Path
from collections import Counter
from music_manager.tag_service import TagService

def library_stats(folder: Path):
    """Собирает статистику по библиотеке"""
    
    audio_files = []
    total_size = 0
    total_duration = 0
    
    artists = Counter()
    albums = Counter()
    years = Counter()
    formats = Counter()
    
    for ext in TagService.SUPPORTED_FORMATS:
        for file_path in folder.rglob(f"*{ext}"):
            audio_file = TagService.read_tags(file_path)
            if not audio_file:
                continue
            
            audio_files.append(audio_file)
            total_size += audio_file.size
            total_duration += audio_file.duration or 0
            
            if audio_file.artist:
                artists[audio_file.artist] += 1
            if audio_file.album:
                albums[audio_file.album] += 1
            if audio_file.year:
                years[audio_file.year] += 1
            if audio_file.format:
                formats[audio_file.format] += 1
    
    print("=== СТАТИСТИКА БИБЛИОТЕКИ ===")
    print(f"Всего файлов: {len(audio_files)}")
    print(f"Общий размер: {total_size / (1024**3):.2f} ГБ")
    print(f"Общая длительность: {total_duration / 3600:.1f} часов")
    print(f"\nУникальных исполнителей: {len(artists)}")
    print(f"Уникальных альбомов: {len(albums)}")
    
    print("\nТоп-5 исполнителей:")
    for artist, count in artists.most_common(5):
        print(f"  {artist}: {count} треков")
    
    print("\nФорматы:")
    for fmt, count in formats.most_common():
        print(f"  {fmt}: {count} файлов")

# Использование
library_stats(Path("/path/to/music"))


# Пример 9: Создание плейлиста M3U
# ====================================

from pathlib import Path
from music_manager.tag_service import TagService

def create_playlist(folder: Path, output_file: Path, relative_paths: bool = True):
    """Создает M3U плейлист из папки"""
    
    audio_files = []
    for ext in TagService.SUPPORTED_FORMATS:
        for file_path in folder.rglob(f"*{ext}"):
            audio_file = TagService.read_tags(file_path)
            if audio_file:
                audio_files.append(audio_file)
    
    # Сортируем по исполнителю, альбому, треку
    audio_files.sort(key=lambda x: (
        x.artist or '',
        x.album or '',
        x.track_number or '00'
    ))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        
        for audio_file in audio_files:
            duration = audio_file.duration or -1
            title = f"{audio_file.artist} - {audio_file.title}" if audio_file.artist and audio_file.title else audio_file.filename
            
            f.write(f"#EXTINF:{duration},{title}\n")
            
            if relative_paths:
                path = audio_file.path.relative_to(output_file.parent)
            else:
                path = audio_file.path
            
            f.write(f"{path}\n")
    
    print(f"Плейлист создан: {output_file}")
    print(f"Треков: {len(audio_files)}")

# Использование
create_playlist(
    Path("/path/to/music"),
    Path("/path/to/playlist.m3u"),
    relative_paths=True
)


# Пример 10: Консольная утилита для быстрого редактирования
# ====================================

import sys
from pathlib import Path
from music_manager.tag_service import TagService

def quick_edit(file_path: str, **tags):
    """Быстрое редактирование тегов из командной строки"""
    
    path = Path(file_path)
    if not path.exists():
        print(f"Файл не найден: {file_path}")
        return False
    
    audio_file = TagService.read_tags(path)
    if not audio_file:
        print(f"Не удалось прочитать файл: {file_path}")
        return False
    
    # Применяем изменения
    for key, value in tags.items():
        if hasattr(audio_file, key):
            setattr(audio_file, key, value)
            print(f"Установлено {key} = {value}")
    
    # Сохраняем
    if TagService.write_tags(audio_file):
        print("✓ Теги успешно сохранены")
        return True
    else:
        print("✗ Ошибка сохранения тегов")
        return False

# Использование из командной строки:
# python examples.py quick_edit song.mp3 --title "New Title" --artist "New Artist"

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick_edit":
        file_path = sys.argv[2]
        tags = {}
        
        for i in range(3, len(sys.argv), 2):
            if sys.argv[i].startswith('--'):
                key = sys.argv[i][2:]
                value = sys.argv[i + 1]
                tags[key] = value
        
        quick_edit(file_path, **tags)
