import os
import sys
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QLabel, QSpinBox, QPushButton, QMessageBox, QMainWindow, QSystemTrayIcon, QMenu)
from PySide6.QtCore import QTimer, Qt, QDateTime
from PySide6.QtGui import QIcon

class CustomMessageBox(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Przerwa")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)

        # Layout i elementy okna
        layout = QVBoxLayout(self)
        message_label = QLabel("Czas na przerwę! Odejdź od komputera i popatrz w dal. \nKliknij OK jak już wrócisz.")
        layout.addWidget(message_label)

        self.ok_button = QPushButton("OK")
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        # Timer do aktywacji przycisku OK
        self.ok_button_timer = QTimer(self)
        self.ok_button_timer.timeout.connect(self.enable_ok_button)
        self.ok_button_timer.start(1000)
        self.seconds_until_enable = 5

    def enable_ok_button(self):
        if self.seconds_until_enable <= 0:
            self.ok_button.setText("OK")
            self.ok_button.setEnabled(True)
            self.ok_button_timer.stop()
        else:
            self.ok_button.setText(f"OK ({self.seconds_until_enable})")
            self.seconds_until_enable -= 1

class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Konfiguracja Przypomnienia')
        self.layout = QVBoxLayout(self)

        self.info_label = QLabel('Wybierz co ile minut chcesz otrzymywać przypomnienia:')
        self.layout.addWidget(self.info_label)

        self.time_spin_box = QSpinBox()
        self.time_spin_box.setRange(1, 120)
        self.time_spin_box.setValue(20)
        self.layout.addWidget(self.time_spin_box)

        self.start_button = QPushButton('Zastosuj')
        self.start_button.clicked.connect(self.accept)
        self.layout.addWidget(self.start_button)

    def get_interval(self):
        return self.time_spin_box.value() * 60000


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.init_ui()
        self.remaining_time = 0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_remaining_time)
        self.update_timer.start(1000)

    def init_ui(self):
        if getattr(sys, 'frozen', False):
            # Aplikacja jest skompilowana
            base_path = sys._MEIPASS
        else:
            # Aplikacja jest uruchomiona w środowisku developerskim
            base_path = os.path.dirname(__file__)
        
        icon_path = os.path.join(base_path, "icon.png")

        if not os.path.exists(icon_path):
            QMessageBox.critical(self, "Błąd", "Brak pliku ikony. Aplikacja zostanie zamknięta.")
            sys.exit(1)
        
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self)
        self.tray_icon.setToolTip("Przypomnienie o przerwie")
        
        tray_menu = QMenu()
        
        # Timer
        self.remaining_time_action = tray_menu.addAction("Pozostały czas: 00:00")
        self.remaining_time_action.setEnabled(False)
        self.next_notification_time = QDateTime.currentDateTime()

        # Settings
        settings_action = tray_menu.addAction("Ustawienia")
        settings_action.triggered.connect(self.show_config_dialog)
        
        # Exit
        exit_action = tray_menu.addAction("Wyjście")
        exit_action.triggered.connect(sys.exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.show_config_dialog()

    def show_config_dialog(self):
        self.config_dialog = ConfigDialog(self)
        if self.config_dialog.exec():
            self.interval = self.config_dialog.get_interval()
            self.next_notification_time = QDateTime.currentDateTime().addMSecs(self.interval)
            self.timer.stop()
            self.timer.timeout.connect(self.show_message)
            self.timer.start(self.interval)

    def show_message(self):
        custom_msg_box = CustomMessageBox(self)
        custom_msg_box.exec_()
        self.next_notification_time = QDateTime.currentDateTime().addMSecs(self.interval)

    def update_ok_button_text(self, ok_button, ok_button_timer):
        if self.seconds_until_enable <= 0:
            ok_button.setText("OK")
            ok_button.setEnabled(True)
            ok_button_timer.stop()
        else:
            ok_button.setText(f"OK ({self.seconds_until_enable})")
            self.seconds_until_enable -= 1

    def update_remaining_time(self):
        if self.timer.isActive():
            current_time = QDateTime.currentDateTime()
            remaining_time = current_time.msecsTo(self.next_notification_time)
            if remaining_time < 0: 
                remaining_time = 0
            mins, secs = divmod(remaining_time // 1000, 60)
            self.remaining_time_action.setText(f"Pozostały czas: {mins:02d}:{secs:02d}")
        else:
            self.remaining_time_action.setText("Pozostały czas: 00:00")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
