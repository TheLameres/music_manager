#!/usr/bin/env python3
"""
Скрипт для быстрого запуска приложения без установки
"""
import sys
from pathlib import Path

# Добавляем корневую директорию в path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from music_manager.main import main

if __name__ == "__main__":
    main()
