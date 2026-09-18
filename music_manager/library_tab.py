"""
Вкладка для работы с библиотекой и редактирования тегов
"""
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QFileDialog,
                              QHeaderView, QLabel, QLineEdit, QFormLayout,
                              QGroupBox, QMessageBox, QProgressDialog)
from PySide6.QtCore import Signal, Qt, QThread

from .audio_file import AudioFile
from .tag_service import TagService


class LibraryTab(QWidget):
    """Вкладка библиотеки для просмотра и редактирования тегов"""
    
    files_loaded = Signal(list)  # Сигнал при загрузке файлов
    
    def __init__(self):
        super().__init__()
        self.audio_files: List[AudioFile] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Инициализирует UI"""
        layout = QVBoxLayout(self)
        
        # Панель инструментов
        toolbar = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Добавить файлы")
        self.add_files_btn.clicked.connect(self._add_files)
        toolbar.addWidget(self.add_files_btn)
        
        self.add_folder_btn = QPushButton("Добавить папку")
        self.add_folder_btn.clicked.connect(self._add_folder)
        toolbar.addWidget(self.add_folder_btn)
        
        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self._clear_library)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        self.files_count_label = QLabel("Файлов: 0")
        toolbar.addWidget(self.files_count_label)
        
        layout.addLayout(toolbar)
        
        # Таблица файлов
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Файл", "Название", "Исполнитель", "Альбом", 
            "Год", "Трек", "Жанр", "Формат", "Размер"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Устанавливаем ширину колонок
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 50)
        self.table.setColumnWidth(6, 100)
        self.table.setColumnWidth(7, 80)
        self.table.setColumnWidth(8, 80)
        
        layout.addWidget(self.table, stretch=3)
        
        # Панель редактирования тегов
        edit_group = QGroupBox("Редактирование тегов")
        edit_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.artist_edit = QLineEdit()
        self.album_edit = QLineEdit()
        self.year_edit = QLineEdit()
        self.track_edit = QLineEdit()
        self.genre_edit = QLineEdit()
        
        edit_layout.addRow("Название:", self.title_edit)
        edit_layout.addRow("Исполнитель:", self.artist_edit)
        edit_layout.addRow("Альбом:", self.album_edit)
        edit_layout.addRow("Год:", self.year_edit)
        edit_layout.addRow("Номер трека:", self.track_edit)
        edit_layout.addRow("Жанр:", self.genre_edit)
        
        edit_buttons = QHBoxLayout()
        self.save_tags_btn = QPushButton("Сохранить теги")
        self.save_tags_btn.clicked.connect(self._save_tags)
        self.save_tags_btn.setEnabled(False)
        edit_buttons.addWidget(self.save_tags_btn)
        
        self.apply_to_all_btn = QPushButton("Применить ко всем")
        self.apply_to_all_btn.clicked.connect(self._apply_to_all)
        self.apply_to_all_btn.setEnabled(False)
        edit_buttons.addWidget(self.apply_to_all_btn)
        
        edit_buttons.addStretch()
        edit_layout.addRow(edit_buttons)
        
        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group, stretch=1)
    
    def _add_files(self):
        """Добавляет файлы в библиотеку"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите аудиофайлы",
            "",
            "Audio Files (*.mp3 *.flac *.ogg *.m4a *.wma *.opus *.ape);;All Files (*.*)"
        )
        
        if files:
            self._load_files([Path(f) for f in files])
    
    def _add_folder(self):
        """Добавляет папку с файлами"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с музыкой"
        )
        
        if folder:
            folder_path = Path(folder)
            files = []
            
            progress = QProgressDialog("Сканирование папки...", "Отмена", 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            for ext in TagService.SUPPORTED_FORMATS:
                files.extend(folder_path.rglob(f"*{ext}"))
                if progress.wasCanceled():
                    return
            
            progress.close()
            
            if files:
                self._load_files(files)
            else:
                QMessageBox.information(self, "Информация", "В выбранной папке не найдено аудиофайлов")
    
    def _load_files(self, file_paths: List[Path]):
        """Загружает файлы и их метаданные"""
        progress = QProgressDialog("Загрузка файлов...", "Отмена", 0, len(file_paths), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        loaded_count = 0
        for idx, file_path in enumerate(file_paths):
            if progress.wasCanceled():
                break
            
            progress.setValue(idx)
            progress.setLabelText(f"Загрузка: {file_path.name}")
            
            # Проверяем, не добавлен ли уже этот файл
            if any(af.path == file_path for af in self.audio_files):
                continue
            
            audio_file = TagService.read_tags(file_path)
            if audio_file:
                self.audio_files.append(audio_file)
                loaded_count += 1
        
        progress.close()
        
        self._refresh_table()
        self.files_loaded.emit(self.audio_files)
        
        QMessageBox.information(self, "Успех", f"Загружено файлов: {loaded_count}")
    
    def _refresh_table(self):
        """Обновляет таблицу файлов"""
        self.table.setRowCount(len(self.audio_files))
        
        for row, audio_file in enumerate(self.audio_files):
            self.table.setItem(row, 0, QTableWidgetItem(audio_file.filename))
            self.table.setItem(row, 1, QTableWidgetItem(audio_file.title or ""))
            self.table.setItem(row, 2, QTableWidgetItem(audio_file.artist or ""))
            self.table.setItem(row, 3, QTableWidgetItem(audio_file.album or ""))
            self.table.setItem(row, 4, QTableWidgetItem(audio_file.year or ""))
            self.table.setItem(row, 5, QTableWidgetItem(audio_file.track_number or ""))
            self.table.setItem(row, 6, QTableWidgetItem(audio_file.genre or ""))
            self.table.setItem(row, 7, QTableWidgetItem(audio_file.format or ""))
            self.table.setItem(row, 8, QTableWidgetItem(f"{audio_file.size_mb:.1f} MB"))
        
        self.files_count_label.setText(f"Файлов: {len(self.audio_files)}")
    
    def _clear_library(self):
        """Очищает библиотеку"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Очистить библиотеку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.audio_files.clear()
            self._refresh_table()
            self._clear_edit_fields()
            self.files_loaded.emit(self.audio_files)
    
    def _on_selection_changed(self):
        """Обработка изменения выбора в таблице"""
        selected_rows = self.table.selectionModel().selectedRows()
        
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            audio_file = self.audio_files[row]
            
            self.title_edit.setText(audio_file.title or "")
            self.artist_edit.setText(audio_file.artist or "")
            self.album_edit.setText(audio_file.album or "")
            self.year_edit.setText(audio_file.year or "")
            self.track_edit.setText(audio_file.track_number or "")
            self.genre_edit.setText(audio_file.genre or "")
            
            self.save_tags_btn.setEnabled(True)
            self.apply_to_all_btn.setEnabled(True)
        elif len(selected_rows) > 1:
            self._clear_edit_fields()
            self.save_tags_btn.setEnabled(False)
            self.apply_to_all_btn.setEnabled(True)
        else:
            self._clear_edit_fields()
            self.save_tags_btn.setEnabled(False)
            self.apply_to_all_btn.setEnabled(False)
    
    def _clear_edit_fields(self):
        """Очищает поля редактирования"""
        self.title_edit.clear()
        self.artist_edit.clear()
        self.album_edit.clear()
        self.year_edit.clear()
        self.track_edit.clear()
        self.genre_edit.clear()
    
    def _save_tags(self):
        """Сохраняет теги выбранного файла"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        audio_file = self.audio_files[row]
        
        # Обновляем теги
        audio_file.title = self.title_edit.text() or None
        audio_file.artist = self.artist_edit.text() or None
        audio_file.album = self.album_edit.text() or None
        audio_file.year = self.year_edit.text() or None
        audio_file.track_number = self.track_edit.text() or None
        audio_file.genre = self.genre_edit.text() or None
        
        # Записываем в файл
        if TagService.write_tags(audio_file):
            self._refresh_table()
            QMessageBox.information(self, "Успех", "Теги успешно сохранены")
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить теги")
    
    def _apply_to_all(self):
        """Применяет текущие значения ко всем выбранным файлам"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Применить теги к {len(selected_rows)} файлам?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        progress = QProgressDialog("Сохранение тегов...", "Отмена", 0, len(selected_rows), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        success_count = 0
        for idx, selected_row in enumerate(selected_rows):
            if progress.wasCanceled():
                break
            
            progress.setValue(idx)
            
            row = selected_row.row()
            audio_file = self.audio_files[row]
            
            # Обновляем только непустые поля
            if self.title_edit.text():
                audio_file.title = self.title_edit.text()
            if self.artist_edit.text():
                audio_file.artist = self.artist_edit.text()
            if self.album_edit.text():
                audio_file.album = self.album_edit.text()
            if self.year_edit.text():
                audio_file.year = self.year_edit.text()
            if self.track_edit.text():
                audio_file.track_number = self.track_edit.text()
            if self.genre_edit.text():
                audio_file.genre = self.genre_edit.text()
            
            if TagService.write_tags(audio_file):
                success_count += 1
        
        progress.close()
        self._refresh_table()
        
        QMessageBox.information(self, "Успех", f"Обновлено файлов: {success_count}")
