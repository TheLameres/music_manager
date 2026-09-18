# Music Manager - Установка и Деплой

## Требования

- Python 3.10 или выше
- Poetry (менеджер зависимостей)
- ОС: Windows, Linux, или macOS

## Установка Poetry

### Windows
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

### Linux/macOS
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Добавьте Poetry в PATH согласно инструкциям установщика.

## Установка приложения

### Вариант 1: Для разработки

```bash
# Клонируйте или скопируйте проект
cd music_manager

# Установите зависимости
poetry install

# Запустите приложение
poetry run music-manager
```

### Вариант 2: Быстрый запуск без установки

```bash
cd music_manager

# Установите зависимости
poetry install

# Запустите напрямую
python run.py
```

### Вариант 3: Установка в систему

```bash
cd music_manager

# Соберите wheel-пакет
poetry build

# Установите пакет
pip install dist/music_manager-1.0.0-py3-none-any.whl

# Теперь можно запускать из любого места
music-manager
```

## Ручная установка зависимостей (без Poetry)

Если по какой-то причине вы не можете использовать Poetry:

```bash
pip install PySide6>=6.6.0 mutagen>=1.47.0 pathvalidate>=3.2.0
python run.py
```

## Проверка установки

После установки запустите приложение:

```bash
poetry run music-manager
```

Должно открыться главное окно с тремя вкладками:
- Библиотека
- Организация
- Синхронизация

## Сборка исполняемого файла (опционально)

Для создания standalone .exe/.app файла используйте PyInstaller:

### Установка PyInstaller

```bash
poetry add --group dev pyinstaller
```

### Windows

```bash
poetry run pyinstaller --name="MusicManager" \
    --windowed \
    --onefile \
    --icon=icon.ico \
    music_manager/main.py
```

### Linux

```bash
poetry run pyinstaller --name="MusicManager" \
    --windowed \
    --onefile \
    music_manager/main.py
```

### macOS

```bash
poetry run pyinstaller --name="MusicManager" \
    --windowed \
    --onefile \
    --osx-bundle-identifier=com.musicmanager.app \
    music_manager/main.py
```

Исполняемый файл будет в папке `dist/`.

## Создание установщика

### Windows (Inno Setup)

1. Установите [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Создайте файл `installer.iss`:

```iss
[Setup]
AppName=Music Manager
AppVersion=1.0.0
DefaultDirName={pf}\MusicManager
DefaultGroupName=Music Manager
OutputDir=output
OutputBaseFilename=MusicManager_Setup

[Files]
Source: "dist\MusicManager.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\Music Manager"; Filename: "{app}\MusicManager.exe"
Name: "{commondesktop}\Music Manager"; Filename: "{app}\MusicManager.exe"
```

3. Скомпилируйте установщик

### Linux (создание .deb пакета)

Создайте структуру:

```
musicmanager_1.0.0/
├── DEBIAN/
│   └── control
└── usr/
    ├── bin/
    │   └── music-manager
    └── share/
        └── applications/
            └── music-manager.desktop
```

Файл `control`:
```
Package: music-manager
Version: 1.0.0
Architecture: all
Maintainer: Your Name <your@email.com>
Depends: python3, python3-pip
Description: Music library manager with tag editing and sync
```

Создайте пакет:
```bash
dpkg-deb --build musicmanager_1.0.0
```

## Обновление

```bash
cd music_manager
git pull  # если используете git
poetry update
```

## Решение проблем

### Ошибка: "mutagen not found"

```bash
poetry install --no-root
poetry install
```

### Ошибка: "Qt platform plugin could not be initialized"

На Linux установите дополнительные зависимости:

```bash
# Ubuntu/Debian
sudo apt-get install libxcb-xinerama0 libxcb-cursor0

# Fedora
sudo dnf install xcb-util-cursor
```

### Ошибка: "Permission denied" при чтении устройства

Запустите с правами администратора или добавьте пользователя в группу:

```bash
# Linux
sudo usermod -a -G plugdev $USER
```

### Проблемы с кодировкой на Windows

Убедитесь, что используете UTF-8:

```python
# В начале файла
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## Тестирование

Запустите тесты:

```bash
poetry run python -m unittest discover tests
```

## Разработка

### Настройка окружения

```bash
# Активируйте виртуальное окружение Poetry
poetry shell

# Установите dev-зависимости (если есть)
poetry install --with dev
```

### Форматирование кода

```bash
# Установите black (опционально)
poetry add --group dev black

# Отформатируйте код
poetry run black music_manager/
```

### Проверка типов

```bash
# Установите mypy (опционально)
poetry add --group dev mypy

# Проверьте типы
poetry run mypy music_manager/
```

## Удаление

### Из Poetry окружения
```bash
cd music_manager
poetry env remove python
```

### Из системы
```bash
pip uninstall music-manager
```

## Системные требования

### Минимальные
- CPU: 1 ГГц
- RAM: 512 МБ
- Место на диске: 100 МБ

### Рекомендуемые
- CPU: 2 ГГц+
- RAM: 2 ГБ+
- Место на диске: 500 МБ+

## Поддержка

При возникновении проблем:
1. Проверьте версию Python: `python --version`
2. Проверьте установку Poetry: `poetry --version`
3. Проверьте логи приложения
4. Создайте issue с описанием проблемы

## Контрибуция

Для внесения изменений:
1. Fork проекта
2. Создайте feature branch
3. Следуйте принципу "один класс - один файл"
4. Добавьте тесты
5. Создайте Pull Request
