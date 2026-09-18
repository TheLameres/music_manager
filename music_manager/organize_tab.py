"""
Вкладка для организации файлов в иерархическую структуру
"""
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QFileDialog,
                              QHeaderView, QLabel, QGroupBox, QRadioButton,
                              QMessageBox, QProgressDialog, QTextEdit)
from PySide6.QtCore import Signal, Qt

from .audio_file import AudioFile
from .organize_service import OrganizeService


class OrganizeTab(QWidget):
    """Вкладка для организации файлов"""
    
    def __init__(self):
        super().__init__()
        self.audio_files: List[AudioFile] = []
        self.target_dir: Path = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Инициализирует UI"""
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            "Организация файлов в структуру: {Исполнитель}/{Год} - {Альбом}/{Номер} - {Название}"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Выбор целевой папки
        folder_group = QGroupBox("Целевая папка")
        folder_layout = QHBoxLayout()
        
        self.target_folder_label = QLabel("Не выбрана")
        folder_layout.addWidget(self.target_folder_label, stretch=1)
        
        self.select_folder_btn = QPushButton("Выбрать папку")
        self.select_folder_btn.clicked.connect(self._select_target_folder)
        folder_layout.addWidget(self.select_folder_btn)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Опции
        options_group = QGroupBox("Опции")
        options_layout = QVBoxLayout()
        
        self.copy_radio = QRadioButton("Копировать файлы")
        self.copy_radio.setChecked(True)
        options_layout.addWidget(self.copy_radio)
        
        self.move_radio = QRadioButton("Переместить файлы")
        options_layout.addWidget(self.move_radio)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Кнопки действий
        action_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Предпросмотр")
        self.preview_btn.clicked.connect(self._preview_organization)
        self.preview_btn.setEnabled(False)
        action_layout.addWidget(self.preview_btn)
        
        self.organize_btn = QPushButton("Организовать")
        self.organize_btn.clicked.connect(self._organize_files)
        self.organize_btn.setEnabled(False)
        action_layout.addWidget(self.organize_btn)
        
        action_layout.addStretch()
        
        self.status_label = QLabel("Файлов для организации: 0")
        action_layout.addWidget(self.status_label)
        
        layout.addLayout(action_layout)
        
        # Таблица предпросмотра
        preview_group = QGroupBox("Предпросмотр изменений")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Текущий путь", "Новый путь"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
    
    def set_files(self, audio_files: List[AudioFile]):
        """Устанавливает список файлов для организации"""
        self.audio_files = audio_files
        self.status_label.setText(f"Файлов для организации: {len(self.audio_files)}")
        self._update_buttons_state()
    
    def _select_target_folder(self):
        """Выбор целевой папки"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите целевую папку"
        )
        
        if folder:
            self.target_dir = Path(folder)
            self.target_folder_label.setText(str(self.target_dir))
            self._update_buttons_state()
    
    def _update_buttons_state(self):
        """Обновляет состояние кнопок"""
        enabled = len(self.audio_files) > 0 and self.target_dir is not None
        self.preview_btn.setEnabled(enabled)
        self.organize_btn.setEnabled(enabled)
    
    def _preview_organization(self):
        """Показывает предпросмотр организации"""
        if not self.target_dir:
            return
        
        preview = OrganizeService.preview_organization(self.audio_files, self.target_dir)
        
        self.preview_table.setRowCount(len(preview))
        
        for row, (old_path, new_path) in enumerate(preview):
            self.preview_table.setItem(row, 0, QTableWidgetItem(str(old_path)))
            self.preview_table.setItem(row, 1, QTableWidgetItem(str(new_path)))
        
        QMessageBox.information(
            self,
            "Предпросмотр",
            f"Будет обработано файлов: {len(preview)}"
        )
    
    def _organize_files(self):
        """Организует файлы"""
        if not self.target_dir or not self.audio_files:
            return
        
        copy_mode = self.copy_radio.isChecked()
        action_text = "скопировано" if copy_mode else "перемещено"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Организовать {len(self.audio_files)} файлов?\n"
            f"Файлы будут {action_text} в:\n{self.target_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Создаем диалог прогресса
        progress = QProgressDialog("Организация файлов...", "Отмена", 0, len(self.audio_files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        def progress_callback(message: str, current: int, total: int):
            if progress.wasCanceled():
                return
            progress.setValue(current)
            progress.setLabelText(message)
        
        # Выполняем организацию
        results = OrganizeService.organize_files(
            self.audio_files,
            self.target_dir,
            copy=copy_mode,
            progress_callback=progress_callback
        )
        
        progress.close()
        
        # Показываем результаты
        QMessageBox.information(
            self,
            "Результаты",
            f"Успешно обработано: {results['success']}\n"
            f"Ошибок: {results['failed']}\n"
            f"Пропущено: {results['skipped']}"
        )
        
        # Очищаем предпросмотр
        self.preview_table.setRowCount(0)
