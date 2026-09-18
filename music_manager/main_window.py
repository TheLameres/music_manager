"""
Главное окно приложения
"""
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

from .library_tab import LibraryTab
from .organize_tab import OrganizeTab
from .sync_tab import SyncTab


class MainWindow(QMainWindow):
    """Главное окно приложения Music Manager"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Music Manager")
        self.setMinimumSize(1200, 700)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Инициализирует пользовательский интерфейс"""
        # Центральный виджет с вкладками
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Вкладка библиотеки
        self.library_tab = LibraryTab()
        self.tabs.addTab(self.library_tab, "Библиотека")
        
        # Вкладка организации
        self.organize_tab = OrganizeTab()
        self.tabs.addTab(self.organize_tab, "Организация")
        
        # Вкладка синхронизации
        self.sync_tab = SyncTab()
        self.tabs.addTab(self.sync_tab, "Синхронизация")
        
        # Связываем вкладки
        self.library_tab.files_loaded.connect(self.organize_tab.set_files)
        self.library_tab.files_loaded.connect(self.sync_tab.set_files)
