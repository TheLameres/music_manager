"""
Вкладка для синхронизации с устройствами
"""
from pathlib import Path
from typing import List

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTableWidget, QTableWidgetItem, QFileDialog,
                              QHeaderView, QLabel, QGroupBox, QComboBox,
                              QMessageBox, QProgressDialog, QCheckBox,
                              QTextEdit)
from PySide6.QtCore import Signal, Qt

from .audio_file import AudioFile
from .sync_service import SyncService


class SyncTab(QWidget):
    """Вкладка для синхронизации с устройствами (аналог Sync в Windows Media Player)"""
    
    def __init__(self):
        super().__init__()
        self.audio_files: List[AudioFile] = []
        self.selected_device: Path = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Инициализирует UI"""
        layout = QVBoxLayout(self)
        
        # Информация
        info_label = QLabel(
            "Синхронизация музыкальной библиотеки с съемными носителями"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Выбор устройства
        device_group = QGroupBox("Устройство")
        device_layout = QVBoxLayout()
        
        device_select_layout = QHBoxLayout()
        device_select_layout.addWidget(QLabel("Устройство:"))
        
        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self._on_device_selected)
        device_select_layout.addWidget(self.device_combo, stretch=1)
        
        self.refresh_devices_btn = QPushButton("Обновить")
        self.refresh_devices_btn.clicked.connect(self._refresh_devices)
        device_select_layout.addWidget(self.refresh_devices_btn)
        
        self.select_folder_btn = QPushButton("Выбрать папку...")
        self.select_folder_btn.clicked.connect(self._select_custom_folder)
        device_select_layout.addWidget(self.select_folder_btn)
        
        device_layout.addLayout(device_select_layout)
        
        # Информация об устройстве
        self.device_info_label = QLabel("Устройство не выбрано")
        device_layout.addWidget(self.device_info_label)
        
        device_group.setLayout(device_layout)
        layout.addWidget(device_group)
        
        # Опции синхронизации
        options_group = QGroupBox("Опции синхронизации")
        options_layout = QVBoxLayout()
        
        self.organize_check = QCheckBox("Организовать файлы в иерархию")
        self.organize_check.setChecked(True)
        self.organize_check.setToolTip(
            "Создать структуру: {Исполнитель}/{Год} - {Альбом}/{Номер} - {Название}"
        )
        options_layout.addWidget(self.organize_check)
        
        self.delete_extra_check = QCheckBox("Удалить лишние файлы с устройства")
        self.delete_extra_check.setToolTip(
            "Удалить файлы, которых нет в исходной библиотеке"
        )
        options_layout.addWidget(self.delete_extra_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Кнопки действий
        action_layout = QHBoxLayout()
        
        self.preview_sync_btn = QPushButton("Предпросмотр синхронизации")
        self.preview_sync_btn.clicked.connect(self._preview_sync)
        self.preview_sync_btn.setEnabled(False)
        action_layout.addWidget(self.preview_sync_btn)
        
        self.sync_btn = QPushButton("Синхронизировать")
        self.sync_btn.clicked.connect(self._sync_to_device)
        self.sync_btn.setEnabled(False)
        action_layout.addWidget(self.sync_btn)
        
        action_layout.addStretch()
        
        self.status_label = QLabel("Файлов в библиотеке: 0")
        action_layout.addWidget(self.status_label)
        
        layout.addLayout(action_layout)
        
        # Область предпросмотра
        preview_group = QGroupBox("План синхронизации")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Загружаем список устройств
        self._refresh_devices()
    
    def set_files(self, audio_files: List[AudioFile]):
        """Устанавливает список файлов для синхронизации"""
        self.audio_files = audio_files
        self.status_label.setText(f"Файлов в библиотеке: {len(self.audio_files)}")
        self._update_buttons_state()
    
    def _refresh_devices(self):
        """Обновляет список доступных устройств"""
        self.device_combo.clear()
        
        drives = SyncService.get_available_drives()
        
        if not drives:
            self.device_combo.addItem("Нет доступных устройств", None)
        else:
            for drive in drives:
                info = SyncService.get_device_info(drive)
                display_text = f"{info['name']} ({drive}) - {info['free_space'] / (1024**3):.1f} ГБ свободно"
                self.device_combo.addItem(display_text, drive)
    
    def _select_custom_folder(self):
        """Выбор пользовательской папки"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку для синхронизации"
        )
        
        if folder:
            self.selected_device = Path(folder)
            self.device_combo.setCurrentIndex(-1)
            self._update_device_info()
            self._update_buttons_state()
    
    def _on_device_selected(self, index: int):
        """Обработка выбора устройства"""
        if index >= 0:
            self.selected_device = self.device_combo.itemData(index)
            self._update_device_info()
            self._update_buttons_state()
    
    def _update_device_info(self):
        """Обновляет информацию об устройстве"""
        if not self.selected_device:
            self.device_info_label.setText("Устройство не выбрано")
            return
        
        info = SyncService.get_device_info(self.selected_device)
        
        total_gb = info['total_space'] / (1024**3)
        free_gb = info['free_space'] / (1024**3)
        used_gb = info['used_space'] / (1024**3)
        
        self.device_info_label.setText(
            f"Путь: {info['path']}\n"
            f"Всего: {total_gb:.1f} ГБ | Занято: {used_gb:.1f} ГБ | Свободно: {free_gb:.1f} ГБ"
        )
    
    def _update_buttons_state(self):
        """Обновляет состояние кнопок"""
        enabled = len(self.audio_files) > 0 and self.selected_device is not None
        self.preview_sync_btn.setEnabled(enabled)
        self.sync_btn.setEnabled(enabled)
    
    def _preview_sync(self):
        """Показывает предпросмотр синхронизации"""
        if not self.selected_device or not self.audio_files:
            return
        
        progress = QProgressDialog("Анализ устройства...", "Отмена", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        organize = self.organize_check.isChecked()
        plan = SyncService.calculate_sync_plan(self.audio_files, self.selected_device, organize)
        
        progress.close()
        
        # Формируем текст предпросмотра
        preview_text = []
        preview_text.append("=== ПЛАН СИНХРОНИЗАЦИИ ===\n")
        preview_text.append(f"Файлов для копирования: {len(plan['to_copy'])}")
        preview_text.append(f"Размер: {plan['total_size'] / (1024**2):.1f} МБ")
        preview_text.append(f"Существующих файлов: {len(plan['existing_files'])}")
        preview_text.append(f"Файлов для удаления: {len(plan['to_delete'])}")
        preview_text.append("")
        
        if plan['to_copy']:
            preview_text.append("--- Файлы для копирования ---")
            for audio_file, target_path in plan['to_copy'][:20]:  # Показываем первые 20
                preview_text.append(f"  {audio_file.filename} → {target_path.name}")
            if len(plan['to_copy']) > 20:
                preview_text.append(f"  ... и еще {len(plan['to_copy']) - 20} файлов")
            preview_text.append("")
        
        if plan['to_delete']:
            preview_text.append("--- Файлы для удаления ---")
            for file_path in plan['to_delete'][:20]:  # Показываем первые 20
                preview_text.append(f"  {file_path.name}")
            if len(plan['to_delete']) > 20:
                preview_text.append(f"  ... и еще {len(plan['to_delete']) - 20} файлов")
        
        self.preview_text.setPlainText("\n".join(preview_text))
        
        # Проверяем свободное место
        device_info = SyncService.get_device_info(self.selected_device)
        if plan['total_size'] > device_info['free_space']:
            QMessageBox.warning(
                self,
                "Недостаточно места",
                f"Требуется: {plan['total_size'] / (1024**3):.2f} ГБ\n"
                f"Доступно: {device_info['free_space'] / (1024**3):.2f} ГБ"
            )
    
    def _sync_to_device(self):
        """Выполняет синхронизацию с устройством"""
        if not self.selected_device or not self.audio_files:
            return
        
        organize = self.organize_check.isChecked()
        delete_extra = self.delete_extra_check.isChecked()
        
        # Предупреждение об удалении
        warning_text = f"Синхронизировать {len(self.audio_files)} файлов с устройством?"
        if delete_extra:
            warning_text += "\n\nВНИМАНИЕ: Лишние файлы будут удалены с устройства!"
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            warning_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Создаем диалог прогресса
        progress = QProgressDialog("Синхронизация...", "Отмена", 0, len(self.audio_files), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        
        def progress_callback(message: str, current: int, total: int):
            if progress.wasCanceled():
                return
            progress.setValue(current)
            progress.setLabelText(message)
        
        # Выполняем синхронизацию
        results = SyncService.sync_to_device(
            self.audio_files,
            self.selected_device,
            organize=organize,
            delete_extra=delete_extra,
            progress_callback=progress_callback
        )
        
        progress.close()
        
        # Показываем результаты
        result_text = (
            f"Синхронизация завершена!\n\n"
            f"Скопировано: {results['copied']}\n"
            f"Удалено: {results['deleted']}\n"
            f"Пропущено: {results['skipped']}\n"
            f"Ошибок: {results['failed']}"
        )
        
        QMessageBox.information(self, "Результаты", result_text)
        
        # Обновляем информацию об устройстве
        self._update_device_info()
