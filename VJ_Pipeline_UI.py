import sys
import os
import glob
import configparser
import subprocess
import threading
import csv
import json
from PySide6.QtWidgets import (QLayout, QGraphicsScale, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QListWidgetItem, QGridLayout, QTabWidget, QTableWidget, 
                               QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QGroupBox ,QFormLayout,
                               QSizePolicy, QApplication, QWidget,QSplitter,QVBoxLayout,QPushButton, QLabel, 
                               QFileDialog, QTextEdit, QStackedWidget, QHBoxLayout, QListWidget, QComboBox,
                               QCheckBox, QSplashScreen, QMainWindow, )
from PySide6.QtGui import QFont, QIcon, QPixmap, QTransform
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt, QEvent, QRect

CONFIG_FILE = "settings.ini"

# CHECKING IF RUNNING
if getattr(sys, 'frozen', False):
    s_dir = sys._MEIPASS 
else:
    s_dir = os.path.dirname(os.path.abspath(__file__))

EXTRACT_SCRIPT = os.path.join(s_dir, "extract_filecaches.py")

# TESTING W DUMMY DATA
SHOWS = {
    "Project Alpha": ["Shot 001", "Shot 002", "Shot 003"],
    "Project Beta": ["Shot 101", "Shot 102"],
    "Project Gamma": ["Shot 201", "Shot 202", "Shot 203", "Shot 204"]
}

SHOTS = {
    "Shot 001": ["Layer A", "Layer B"],
    "Shot 002": ["Layer C", "Layer D", "Layer E"],
    "Shot 101": ["Layer X", "Layer Y"]
}

def resource_path(relative_path):
        """Get the absolute path for resources, whether running as script or .exe."""
        if getattr(sys, 'frozen', False):
            # .EXE RUNNING
            base_path = sys._MEIPASS
        else:
            # .PY RUNNING
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

class SplashScreen(QSplashScreen):
    def __init__(self):
        super().__init__(QPixmap(resource_path("icons/splash.png")))  #SPLASH SCREEN
        self.show()
        QTimer.singleShot(2000, self.close)
class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.sidebar_visible = True  
        self.dark_mode = True
        self.csv_path = None 
        self.initUI()
        self.load_settings()
        self.apply_styles()
        self.setup_animations()

    def initUI(self):
        self.setWindowTitle("VJ VFX PIPELINE MANAGER")
        self.setGeometry(100, 100, 900, 600) 
        
        # Main Layout
        self.splitter = QSplitter(self)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.sidebar_container = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_container)
        self.sidebar_container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.toggle_button = QPushButton("☰")
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.toggle_button, alignment=Qt.AlignTop)
        self.toggle_button.setStyleSheet("font-size: 18px; padding: 5px; color: white; background: none; border: none;")
        
        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)


        dashboard_item = QTreeWidgetItem(["🏠 Dashboard"])
        houdini_item = QTreeWidgetItem(["🔷 Houdini"])
        batch_caching_item = QTreeWidgetItem(["Batch Caching"])
        settings_item = QTreeWidgetItem(["⚙️ Settings"])
        render_manager_item = QTreeWidgetItem(["🎬 Render Manager"])
        houdini_item.addChild(batch_caching_item)

        self.nav_tree.addTopLevelItem(dashboard_item)
        self.nav_tree.addTopLevelItem(render_manager_item)
        self.nav_tree.addTopLevelItem(houdini_item)
        self.nav_tree.addTopLevelItem(settings_item)
        
        self.nav_tree.itemClicked.connect(self.switch_page)
        
        self.sidebar_layout.addWidget(self.toggle_button, alignment=Qt.AlignTop)
        self.sidebar_layout.addWidget(self.nav_tree)
        self.sidebar_container.setLayout(self.sidebar_layout)

        self.stackedWidget = QStackedWidget()
        self.stackedWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # DASHBOARD PAGE
        self.dashboard_page = QWidget()
        self.initDashboard()
        self.stackedWidget.addWidget(self.dashboard_page)
        
        # RENDER MANAGER PAGE
        self.render_manager_page = QWidget()
        self.initRenderManager()
        self.stackedWidget.addWidget(self.render_manager_page)

        # BATCH CACHING PAGE
        self.batch_caching_page = QWidget()
        self.initBatchCaching()
        self.stackedWidget.addWidget(self.batch_caching_page)

        # SETTINGS PAGE
        self.settings_page = QWidget()
        self.initSettings()
        self.stackedWidget.addWidget(self.settings_page)
        
        self.splitter.addWidget(self.sidebar_container)
        self.splitter.addWidget(self.stackedWidget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

        QTimer.singleShot(100, self.force_layout_update)


    def load_settings(self):
        """Loads settings from settings.ini"""

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        
        if config.has_section("Settings"):
            houdini_path = config.get("Settings", "houdini_path", fallback="")
            self.houdini_version_dropdown.setCurrentText(houdini_path)


    def save_settings(self):
        """Saves user settings to settings.ini"""

        config = configparser.ConfigParser()
        
        if not config.has_section("Settings"):
            config.add_section("Settings")
        
        selected_houdini = os.path.join(self.houdini_version_dropdown.currentText(), "bin", "hython.exe")
        config.set("Settings", "houdini_path", selected_houdini)

        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)


    def count_cache_sequences(self, csv_path):
        """Reads CSV file and counts how many file cache nodes need to be processed."""
        try:
            with open(csv_path, "r") as file:
                reader = csv.reader(file)
                total_caches = 0
                total_caches = sum(len(row) - 2 for row in reader if len(row) > 2)
                return total_caches
        except Exception as e:
            self.output_console.append(f"❌ Error reading CSV file: {e}")
            return 0


    def run_caching(self):
        """Runs Houdini caching in a separate thread to keep the UI responsive."""
        if not self.csv_path:
            self.status_label.setText("❌ Please select a CSV file!")
            self.status_label.setStyleSheet("color: red;")
            return
        
        total_caches = self.count_cache_sequences(self.csv_path)

        if total_caches == 0:
            self.status_label.setText("❌ No caches found in CSV!")
            self.status_label.setStyleSheet("color: red;")
            return

        self.status_label.setText(f"🚀 Preparing to cache {total_caches} sequences...")
        self.status_label.setStyleSheet("color: orange;")

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        houdini_path = config.get("Settings", "houdini_path", fallback="")

        self.output_console.append(f"📂 Houdini Path: {houdini_path}")      #PRINTING 4 DEBUGGING
        self.output_console.append(f"📄 CSV File Path: {self.csv_path}")

        if not houdini_path or not os.path.exists(houdini_path):
            self.status_label.setText("❌ Houdini path not set! Open Settings.")
            self.status_label.setStyleSheet("color: red;")
            return
        
        if getattr(sys, 'frozen', False):
            script_dir = sys._MEIPASS
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        script_path = os.path.join(script_dir, "batch_cache_from_csv_v002.py")

        cache_thread = threading.Thread(target=self.run_caching_thread, args=(houdini_path, script_path))
        cache_thread.start()




    def run_caching_thread(self, houdini_path, script_path):
        """Runs Houdini batch caching process without blocking the UI."""
        try:
            
            process = subprocess.Popen(
                [houdini_path, script_path, self.csv_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in process.stdout:
                self.output_console.append(line.strip())
                QApplication.processEvents()
            process.wait()

            if process.returncode == 0:
                self.status_label.setText("✅ All caches completed successfully!")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText("❌ Error during caching. Check logs.")
                self.status_label.setStyleSheet("color: red;")

        except Exception as e:
            self.status_label.setText(f"❌ Exception: {str(e)}")
            self.status_label.setStyleSheet("color: red;")


    def detect_houdini_versions(self):
        """Detect installed Houdini versions and populate dropdown."""
        houdini_versions = glob.glob(r"C:\Program Files\Side Effects Software\Houdini *")
        self.houdini_version_dropdown.clear()

        if not houdini_versions:
            self.houdini_version_dropdown.addItem("❌ No Houdini found")
            return

        for path in houdini_versions:
            self.houdini_version_dropdown.addItem(path)

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        saved_path = config.get("Settings", "houdini_path", fallback="")
        
        if saved_path in houdini_versions:
            self.houdini_version_dropdown.setCurrentText(saved_path)


    def toggle_sidebar(self):
        """Show/Hide Sidebar Without Hiding the Toggle Button"""
        if self.sidebar_visible:
            self.nav_tree.hide()
            self.sidebar_container.setFixedWidth(50)
            self.toggle_button.setText("☰ ▶")
        else:
            self.nav_tree.show()
            self.sidebar_container.setFixedWidth(200)
            self.toggle_button.setText("☰ ◀")
        self.sidebar_visible = not self.sidebar_visible


    def force_layout_update(self):
        """Force a layout recalculation to fix initial sizing issue."""
        self.splitter.setSizes([250, 650])

    def initDashboard(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Welcome to the VFX Pipeline Manager!"))
        self.dashboard_page.setLayout(layout)

    def initBatchCaching(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # CSV File Creation Tab
        self.csv_creation_tab = QWidget()
        csv_layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        select_layout = QHBoxLayout()
        deselect_layout = QHBoxLayout()

        self.btn_select_hip = QPushButton("Browse Houdini File")
        self.btn_select_hip.clicked.connect(self.load_hip_file)

        self.detected_table = QTableWidget(0, 3)
        self.detected_table.setHorizontalHeaderLabels(["Select", "Houdini File", "File Cache Path"])
        
        self.selected_table = QTableWidget(0, 4)
        self.selected_table.setHorizontalHeaderLabels(["Select", "Houdini File", "File Cache Path", "Rendering Mode"])
        
        self.selected_table.setDragDropMode(QTableWidget.InternalMove)
        self.selected_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.selected_table.setDragEnabled(True)
        self.selected_table.setAcceptDrops(True)
        self.selected_table.viewport().setAcceptDrops(True)
        self.selected_table.setDropIndicatorShown(True)
        self.selected_table.setDefaultDropAction(Qt.MoveAction)

        self.selected_table.dropEvent = self.dropEvent

        self.btn_add = QPushButton("Add →")
        self.btn_add.clicked.connect(self.add_selected)
        self.btn_remove = QPushButton("← Remove")
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.clicked.connect(self.clear_all)

        self.label_select_all = QLabel("Select All:")
        self.btn_select_all_detected = QPushButton("✔")
        self.btn_select_all_detected.clicked.connect(lambda: self.select_all(self.detected_table))
        select_layout.addWidget(self.label_select_all)
        select_layout.addWidget(self.btn_select_all_detected)

        self.label_deselect_all = QLabel("Deselect All:")
        self.btn_deselect_all_detected = QPushButton("✖")
        self.btn_deselect_all_detected.clicked.connect(lambda: self.deselect_all(self.detected_table))
        deselect_layout.addWidget(self.label_deselect_all)
        deselect_layout.addWidget(self.btn_deselect_all_detected)

        button_layout.addLayout(select_layout)
        button_layout.addLayout(deselect_layout)
        button_layout.addStretch()

        self.btn_save_csv = QPushButton("Save CSV")
        self.btn_save_csv.clicked.connect(self.save_csv)


        csv_layout.addWidget(self.btn_select_hip)

        csv_layout.addWidget(QLabel("Detected File Caches"))
        csv_layout.addLayout(button_layout)
        csv_layout.addWidget(self.detected_table)

        csv_layout.addWidget(self.btn_add)

        csv_layout.addWidget(QLabel("Selected File Caches"))
        csv_layout.addWidget(self.selected_table)

        csv_layout.addWidget(self.btn_remove)
        csv_layout.addWidget(self.btn_clear)
        csv_layout.addWidget(self.btn_save_csv)

        self.csv_creation_tab.setLayout(csv_layout)


        # Batch Caching Execution Tab
        self.batch_caching_tab = QWidget()
        batch_layout = QVBoxLayout()
        self.status_label = QLabel("Waiting for user input...")
        self.status_label.setFont(QFont("Circular", 14))
        
        self.btn_select_csv = QPushButton("Browse CSV File")
        self.btn_select_csv.setIcon(QIcon(resource_path("icons/folder.png")))
        self.btn_select_csv.clicked.connect(self.load_csv)

        self.btn_run = QPushButton("Run Caching")
        self.btn_run.setIcon(QIcon(resource_path("icons/play.png")))
        self.btn_run.clicked.connect(self.run_caching)
        
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setPlaceholderText("Logs will appear here...")

        batch_layout.addWidget(self.status_label)
        batch_layout.addWidget(self.btn_select_csv)
        batch_layout.addWidget(self.btn_run)
        batch_layout.addWidget(self.output_console)

        self.batch_caching_tab.setLayout(batch_layout)

        self.tabs.addTab(self.csv_creation_tab, "Create CSV")
        self.tabs.addTab(self.batch_caching_tab, "Run Batch Caching")

        layout.addWidget(self.tabs)
        self.batch_caching_page.setLayout(layout)

    def dropEvent(self, event):
        """Ensure drag-and-drop properly updates the table when rows are moved."""
        event.accept()
        
        selected_items = self.selected_table.selectedItems()
        if not selected_items:
            return

        selected_row = self.selected_table.currentRow()
        drop_position = self.selected_table.indexAt(event.position().toPoint()).row()

        if drop_position == -1:
            drop_position = self.selected_table.rowCount() - 1
        
        row_data = []
        for col in range(self.selected_table.columnCount()):
            widget = self.selected_table.cellWidget(selected_row, col)
            item = self.selected_table.item(selected_row, col)

            if isinstance(widget, QComboBox):
                row_data.append(("dropdown", widget.currentText()))
            elif isinstance(widget, QCheckBox):
                row_data.append(("checkbox", widget.isChecked()))
            elif item:
                row_data.append(("text", item.text()))
            else:
                row_data.append(("text", ""))

        self.selected_table.removeRow(selected_row)

        self.selected_table.insertRow(drop_position)

        for col in range(len(row_data)):
            data_type, data_value = row_data[col]
            if data_type == "dropdown":
                mode_dropdown = QComboBox()
                mode_dropdown.addItems(["Sequential", "Parallel"])
                mode_dropdown.setCurrentText(data_value)
                self.selected_table.setCellWidget(drop_position, col, mode_dropdown)
            elif data_type == "checkbox":
                checkbox = QCheckBox()
                checkbox.setChecked(data_value)
                self.selected_table.setCellWidget(drop_position, col, checkbox)
            else:
                self.selected_table.setItem(drop_position, col, QTableWidgetItem(data_value))

    def initSettings(self):
        """Improved Settings Panel Layout"""
        settings_layout = QVBoxLayout()
        
        general_group = QGroupBox("General Settings")
        general_layout = QFormLayout()
        
        self.theme_toggle = QCheckBox("Enable Light Mode")
        self.theme_toggle.stateChanged.connect(self.toggle_light_dark_mode)
        general_layout.addRow("Theme:", self.theme_toggle)
        
        general_group.setLayout(general_layout)
        
        houdini_group = QGroupBox("Houdini Settings")
        houdini_layout = QFormLayout()
        
        self.houdini_version_dropdown = QComboBox()
        self.detect_houdini_versions()
        houdini_layout.addRow("Houdini Version:", self.houdini_version_dropdown)
        
        houdini_group.setLayout(houdini_layout)
        
        self.btn_save_settings = QPushButton("💾 Save Settings")
        self.btn_save_settings.setStyleSheet("padding: 10px; font-weight: bold;")
        self.btn_save_settings.clicked.connect(self.save_settings)

        settings_layout.addWidget(general_group)
        settings_layout.addWidget(houdini_group)
        settings_layout.addWidget(self.btn_save_settings)
        settings_layout.addStretch()
        
        self.settings_page.setLayout(settings_layout)

    def load_hip_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Houdini .hip File", "", "Houdini Files (*.hip *.hipnc)")
        if file_path:
            self.hip_file = file_path
            self.run_extract_script()

    def run_extract_script(self):

        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        houdini_path = config.get("Settings", "houdini_path", fallback="")

        if not houdini_path or not os.path.exists(houdini_path):
            self.status_label.setText("❌ Houdini path not set! Open Settings.")
            self.status_label.setStyleSheet("color: red;")
            return

        if not self.hip_file:
            return
        
        process = subprocess.Popen([houdini_path, EXTRACT_SCRIPT, self.hip_file],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        
        stdout, stderr = process.communicate()

        if stdout:
            try :
                filecache_nodes = json.loads(stdout)

                self.detected_table.setRowCount(0)  # Clear previous entries

                for path in filecache_nodes:
                    row_position = self.detected_table.rowCount()
                    self.detected_table.insertRow(row_position)

                    checkbox = QCheckBox()
                    self.detected_table.setCellWidget(row_position, 0, checkbox)

                    self.detected_table.setItem(row_position, 1, QTableWidgetItem(self.hip_file))
                    self.detected_table.setItem(row_position, 2, QTableWidgetItem(path))

            except json.JSONDecodeError as e:
                print("❌ JSON Error:", str(e))  # DEBUGGING PRINT STATEMENT



    def add_selected(self):

        """Move checked rows from detected_table to selected_table."""
        for row in range(self.detected_table.rowCount()):
            checkbox = self.detected_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                houdini_file = self.detected_table.item(row, 1).text()
                file_cache = self.detected_table.item(row, 2).text()

                duplicate = False
                for i in range(self.selected_table.rowCount()):
                    if (self.selected_table.item(i, 1).text() == houdini_file and
                        self.selected_table.item(i, 2).text() == file_cache):
                        duplicate = True
                        break
                    
                if not duplicate:
                    row_position = self.selected_table.rowCount()
                    self.selected_table.insertRow(row_position)

                    selected_checkbox = QCheckBox()
                    self.selected_table.setCellWidget(row_position, 0, selected_checkbox)

                    self.selected_table.setItem(row_position, 1, QTableWidgetItem(houdini_file))
                    self.selected_table.setItem(row_position, 2, QTableWidgetItem(file_cache))

                    mode_dropdown = QComboBox()
                    mode_dropdown.addItems(["Sequential", "Parallel"])
                    self.selected_table.setCellWidget(row_position, 3, mode_dropdown)


    def remove_selected(self):
        """Remove checked rows from selected_table."""
        for row in reversed(range(self.selected_table.rowCount())):
            checkbox = self.selected_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                self.selected_table.removeRow(row)


    def clear_all(self):
        """Clear all rows from selected_table."""
        self.selected_table.setRowCount(0)


    def select_all(self, table):
        """Select all checkboxes in the given table."""
        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)


    def deselect_all(self, table):
        """Deselect all checkboxes in the given table."""
        for row in range(table.rowCount()):
            checkbox = table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)


    def save_csv(self):
        """Save selected file caches and their rendering modes to a CSV file."""
        if self.selected_table.rowCount() == 0:
            print("❌ No file caches selected. Cannot save CSV.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return

        data = {}
        for row in range(self.selected_table.rowCount()):
            houdini_file = self.selected_table.item(row, 1).text()
            file_cache = self.selected_table.item(row, 2).text()
            mode_dropdown = self.selected_table.cellWidget(row, 3)
            rendering_mode = mode_dropdown.currentText() if mode_dropdown else "Sequential"

            key = (houdini_file, rendering_mode)
            if key not in data:
                data[key] = []
            data[key].append(file_cache)

        with open(file_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            
            for (houdini_file, mode), file_caches in data.items():
                writer.writerow([houdini_file, mode.lower(), *file_caches])

    
    
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.csv_path = file_path
            self.status_label.setText(f"Selected: {file_path}")
            self.status_label.setText("✅ CSV file selected. Ready to cache.")
            self.status_label.setStyleSheet("color: blue;")
    
    def switch_page(self, item):
        if item.text(0) == "🏠 Dashboard":
            self.stackedWidget.setCurrentWidget(self.dashboard_page)
        elif item.text(0) == "Batch Caching":
            self.stackedWidget.setCurrentWidget(self.batch_caching_page)
        elif item.text(0) == "⚙️ Settings":
            self.stackedWidget.setCurrentWidget(self.settings_page)
        elif item.text(0) == "🎬 Render Manager":
            self.stackedWidget.setCurrentWidget(self.render_manager_page)

    def toggle_light_dark_mode(self):
        """Toggles between light and dark mode"""
        self.dark_mode = not self.dark_mode
        self.apply_styles()

    def setup_animations(self):
        """Setup UI animations"""
        self.animation = QPropertyAnimation(self.stackedWidget, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)


    def apply_styles(self):
        """Apply QSS Styles to the UI"""
        if self.dark_mode:
            self.setStyleSheet("""
                QWidget {
                    background-color: #121212; /* Darker for premium feel */
                    color: #ffffff;
                    font-family: 'Circular', Arial, sans-serif;
                }
                QListWidget {
                    background-color: rgba(18, 18, 18, 0.85); /* Semi-transparent */
                    border: none;
                    padding: 10px;
                    font-size: 16px;
                    border-radius: 12px;
                }
                QListWidget::item:selected {
                    background-color: #1DB954;
                    color: white;
                    border-radius: 5px;
                }
                QListWidget::item:hover {
                    background-color: #333333;
                    border-radius: 8px;
                }
                QPushButton {
                    background-color: linear-gradient(to right, #1DB954, #1ED760);
                    color: white;
                    border-radius: 20px; /* More rounded */
                    padding: 14px;
                    font-size: 16px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1AAE48;
                    transform: scale(1.05); /* Slight enlarge */
                }
                QTextEdit {
                    background-color: #202020;
                    border: 1px solid #444;
                    padding: 12px;
                    border-radius: 10px;
                    font-family: Consolas, monospace;
                    color: #ffffff;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    color: #222222;
                    font-family: 'Circular', Arial, sans-serif;
                }
                QListWidget {
                    background-color: rgba(255, 255, 255, 0.9); /* Semi-transparent */
                    border: none;
                    padding: 10px;
                    font-size: 16px;
                    border-radius: 12px;
                }
                QListWidget::item:selected {
                    background-color: #1DB954;
                    color: white;
                    border-radius: 5px;
                }
                QListWidget::item:hover {
                    background-color: #dddddd;
                    border-radius: 8px;
                }
                QPushButton {
                    background-color: linear-gradient(to right, #1DB954, #1ED760);
                    color: #ffffff;
                    border-radius: 20px;
                    padding: 14px;
                    font-size: 16px;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1ED760;
                    transform: scale(1.05);
                }
                QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    padding: 12px;
                    border-radius: 10px;
                    font-family: Consolas, monospace;
                    color: #222222;
                }
            """)

    def initRenderManager(self):
        """Initialize the Render Manager with hierarchical navigation."""
        self.render_manager_page = QWidget()
        layout = QVBoxLayout(self.render_manager_page)

        self.render_stack = QStackedWidget()
        layout.addWidget(self.render_stack)

        self.show_selection_view = self.createShowSelectionView()
        self.render_stack.addWidget(self.show_selection_view)

        self.shot_selection_view = QWidget()
        self.render_stack.addWidget(self.shot_selection_view)

        self.render_layer_view = QWidget()
        self.render_stack.addWidget(self.render_layer_view)

        self.render_manager_page.setLayout(layout)



    def createShowSelectionView(self):
        """Creates the initial Show Selection View"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title_label = QLabel("Select Show / Project")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; padding: 10px;")
        layout.addWidget(title_label)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(50, 50, 50, 50)

        shows = ["Mickey 17", "The Brutalist", "Twisters"]
        thumbnails = ["images/Mickey 17.jpg", "images/The Brutalist.jpg", "images/Twisters.jpg"]
        metadatas = ["Created: Jan 2024 | 10 Shots", "Created: Feb 2024 | 8 Shots", "Created: Mar 2024 | 15 Shots"]

        self.show_labels = {}

        for index, (show, thumbnail, metadata) in enumerate(zip(shows, thumbnails, metadatas)):
            show_widget = QWidget()
            show_layout = QVBoxLayout(show_widget)
            show_layout.setSpacing(5)
            show_layout.setAlignment(Qt.AlignCenter)

            original_pixmap = QPixmap(resource_path(thumbnail)).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled_pixmap = original_pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            if scaled_pixmap.isNull():
                print(f"Error: Image scaling failed for {thumbnail}")

            label = QLabel()
            label.setPixmap(scaled_pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setCursor(Qt.PointingHandCursor)
            label.mousePressEvent = lambda event, s=show: self.openShots(s)

            text_label = QLabel(f"<b>{show}</b>")
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setStyleSheet("font-size: 14px; color: white; font-weight: bold;")

            metadata_label = QLabel(metadata)
            metadata_label.setAlignment(Qt.AlignCenter)
            metadata_label.setStyleSheet("font-size: 12px; color: gray;")
            metadata_label.setFixedHeight(20)
            metadata_label.setVisible(False)

            self.show_labels[label] = {"original": original_pixmap,
                                       "metadata": metadata_label}

            show_layout.addWidget(label)
            show_layout.addWidget(text_label)
            show_layout.addWidget(metadata_label)

            grid_layout.addWidget(show_widget, index // 3, index % 3)

        layout.addLayout(grid_layout)
        widget.setLayout(layout)
        return widget
    

    def openShots(self, show_name):
        """Switch to Shot Selection for the clicked Show"""
        self.shot_selection_view = QWidget()
        layout = QVBoxLayout(self.shot_selection_view)

        label = QLabel(f"Shots for {show_name}")
        layout.addWidget(label)

        shots_list = QListWidget()
        shots = ["Shot 001", "Shot 002", "Shot 003"]
        for shot in shots:
            shot_item = QPushButton(shot)
            shot_item.clicked.connect(lambda _, s=shot: self.openRenderLayers(s))
            layout.addWidget(shot_item)

        back_btn = QPushButton("Back to Shows")
        back_btn.clicked.connect(lambda: self.render_stack.setCurrentIndex(0))
        layout.addWidget(back_btn)

        self.shot_selection_view.setLayout(layout)

        self.render_stack.insertWidget(1, self.shot_selection_view)
        self.render_stack.setCurrentIndex(1)


    def openRenderLayers(self, shot_name):
        """Switch to Render Layer Selection for the clicked Shot"""
        self.render_layer_view = QWidget()
        layout = QVBoxLayout(self.render_layer_view)

        label = QLabel(f"Render Layers for {shot_name}")
        layout.addWidget(label)

        layers = ["Layer C", "Layer D", "Layer E"]
        for layer in layers:
            layout.addWidget(QLabel(layer))

        back_btn = QPushButton("Back to Shots")
        back_btn.clicked.connect(lambda: self.render_stack.setCurrentIndex(1))
        layout.addWidget(back_btn)

        self.render_layer_view.setLayout(layout)
        self.render_stack.insertWidget(2, self.render_layer_view)
        self.render_stack.setCurrentIndex(2)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    window = MainUI()
    window.show()
    sys.exit(app.exec())
