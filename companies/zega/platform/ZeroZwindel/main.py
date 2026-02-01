import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QStackedWidget, 
                             QFrame, QScrollArea, QGridLayout, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

# ZEGA Core Logic
from core.library import LibraryManager
from core.store import ZegaCloudManager

class ZeroZwindelPlatform(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Identity & Branding
        self.brand_color = "#58f01b"
        self.bg_dark = "#121212"
        self.card_bg = "#1e1e1e"
        
        # Initialize Managers
        self.library = LibraryManager()
        # Ensure you add your Netlify Token/Site ID in core/cloud.py or here
        self.cloud = ZegaCloudManager()
        
        self.setWindowTitle("ZeroZwindel (ZZ) | ZEGA Executive Platform")
        self.setMinimumSize(1100, 750)
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet(f"background-color: {self.bg_dark}; color: white;")
        self.setCentralWidget(self.central_widget)
        self.root_layout = QVBoxLayout(self.central_widget)
        
        # --- EXECUTIVE NAVIGATION HEADER ---
        self.nav_frame = QFrame()
        self.nav_frame.setFixedHeight(80)
        self.nav_frame.setStyleSheet("background: #181818; border-bottom: 1px solid #333;")
        nav_layout = QHBoxLayout(self.nav_frame)
        
        # ZZ Logo
        logo = QLabel("ZZ")
        logo.setFont(QFont("Impact", 36))
        logo.setStyleSheet(f"color: {self.brand_color}; margin-right: 40px; margin-left: 20px;")
        nav_layout.addWidget(logo)

        # View Selectors
        self.btn_lib = self._create_nav_btn("MY LIBRARY", 0)
        self.btn_store = self._create_nav_btn("ZEGA STORE", 1)
        nav_layout.addWidget(self.btn_lib)
        nav_layout.addWidget(self.btn_store)
        
        nav_layout.addStretch()

        # --- NEW: OWNER UPLOAD BUTTON ---
        self.btn_upload = QPushButton("UPLOAD TO ZZ CLOUD")
        self.btn_upload.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_upload.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.btn_upload.setStyleSheet(f"""
            QPushButton {{
                color: {self.brand_color};
                border: 1px solid {self.brand_color};
                border-radius: 4px;
                padding: 8px 15px;
                margin-right: 20px;
            }}
            QPushButton:hover {{
                background: {self.brand_color};
                color: black;
            }}
        """)
        self.btn_upload.clicked.connect(self.handle_owner_upload)
        nav_layout.addWidget(self.btn_upload)
        
        self.root_layout.addWidget(self.nav_frame)

        # --- VIEW ROUTING ---
        self.router = QStackedWidget()
        self.lib_view = self._create_view_grid(is_store=False)
        self.store_view = self._create_view_grid(is_store=True)
        self.router.addWidget(self.lib_view)
        self.router.addWidget(self.store_view)
        
        self.root_layout.addWidget(self.router)
        self.switch_view(0)

    def _create_nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn.setFixedHeight(50)
        btn.clicked.connect(lambda: self.switch_view(index))
        return btn

    def _create_view_grid(self, is_store):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(25)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(container)
        
        if is_store: self.store_grid = grid
        else: self.lib_grid = grid
        return scroll

    def switch_view(self, index):
        self.router.setCurrentIndex(index)
        active = f"color: {self.brand_color}; background: transparent; border-bottom: 3px solid {self.brand_color}; padding: 0 20px; margin-top: 10px;"
        inactive = "color: #888; background: transparent; border: none; padding: 0 20px; margin-top: 10px;"
        
        self.btn_lib.setStyleSheet(active if index == 0 else inactive)
        self.btn_store.setStyleSheet(active if index == 1 else inactive)
        
        if index == 0: self.refresh_library()
        else: self.refresh_store()

    def handle_owner_upload(self):
        """Opens a folder selector to push a new project to Netlify."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select ZEGA Project Folder to Upload")
        if folder_path:
            # Check for manifest before uploading
            if not os.path.exists(os.path.join(folder_path, "manifest.json")):
                QMessageBox.warning(self, "ZZ Error", "No manifest.json found in this project.")
                return
                
            QMessageBox.information(self, "ZZ Cloud", "Deployment Initialized. Syncing assets...")
            if self.cloud.deploy_new_game(folder_path):
                QMessageBox.information(self, "ZZ Cloud", "Success! Project is live on Netlify.")
                self.refresh_store()

    def refresh_library(self):
        self._clear_grid(self.lib_grid)
        installed = self.library.get_installed_games()
        for i, g in enumerate(installed):
            card = self._create_card(g['name'], "Ready to Play", False, g['id'])
            self.lib_grid.addWidget(card, i // 4, i % 4)

    def refresh_store(self):
        self._clear_grid(self.store_grid)
        items = self.cloud.get_cloud_catalog()
        for i, item in enumerate(items):
            card = self._create_card(item['name'], "Cloud Available", True, item['id'])
            self.store_grid.addWidget(card, i // 4, i % 4)

    def _create_card(self, title, status, is_store, g_id):
        card = QFrame()
        card.setFixedSize(220, 270)
        card.setStyleSheet(f"background: {self.card_bg}; border-radius: 12px; border: 1px solid #333;")
        l = QVBoxLayout(card)
        
        banner = QLabel(); banner.setFixedSize(200, 110); banner.setStyleSheet("background: #000; border-radius: 6px;")
        l.addWidget(banner)
        
        name = QLabel(title); name.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        l.addWidget(name)
        
        btn = QPushButton("DOWNLOAD" if is_store else "PLAY")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"background: {self.brand_color}; color: black; font-weight: bold; border-radius: 6px; padding: 10px;")
        
        if is_store: btn.clicked.connect(lambda: self.handle_download(g_id))
        else: btn.clicked.connect(lambda: self.library.launch_game(g_id))
        
        l.addWidget(btn)
        return card

    def handle_download(self, g_id):
        if self.cloud.download_game(g_id):
            QMessageBox.information(self, "ZZ Platform", f"Downloaded {g_id}.")
            self.switch_view(0)

    def _clear_grid(self, grid):
        while grid.count():
            item = grid.takeAt(0); 
            if item.widget(): item.widget().deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ZeroZwindelPlatform()
    window.show()
    sys.exit(app.exec())