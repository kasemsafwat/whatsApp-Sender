import sys
import random
import time
import webbrowser
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QListWidget, QPushButton, 
                            QLineEdit, QMessageBox, QLabel, QComboBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pyautogui
import keyboard

# Dictionary of country codes
COUNTRY_CODES = {
    "Saudi Arabia 🇸🇦": "+966",
    "Egypt 🇪🇬": "+20",
    "UAE 🇦🇪": "+971",
    "Kuwait 🇰🇼": "+965",
    "Bahrain 🇧🇭": "+973",
    "Qatar 🇶🇦": "+974",
    "Oman 🇴🇲": "+968",
    "Jordan 🇯🇴": "+962",
    "Lebanon 🇱🇧": "+961",
    "Iraq 🇮🇶": "+964",
    "Yemen 🇾🇪": "+967",
    "Palestine 🇵🇸": "+970",
    "USA 🇺🇸": "+1",
    "UK 🇬🇧": "+44",
    "India 🇮🇳": "+91",
    "Pakistan 🇵🇰": "+92",
}

class WhatsAppSender(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, numbers, message):
        super().__init__()
        self.numbers = numbers
        self.message = message

    def send_message(self, message):
        # Type the message line by line
        lines = message.split('\n')
        for line in lines:
            keyboard.write(line)
            pyautogui.hotkey('shift', 'enter')
            time.sleep(0.5)
        
        # Send the message
        keyboard.press_and_release('enter')
        time.sleep(1)

    def run(self):
        try:
            # Open WhatsApp Desktop
            whatsapp_path = os.path.join(os.getenv('LOCALAPPDATA'), 'WhatsApp', 'WhatsApp.exe')
            if os.path.exists(whatsapp_path):
                os.startfile(whatsapp_path)
            else:
                webbrowser.open('https://web.whatsapp.com')
            
            time.sleep(10)
            
            for number in self.numbers:
                try:
                    # Add country code if not present
                    if not any(code.strip('+') in number for code in COUNTRY_CODES.values()):
                        self.error.emit(f"Skipping {number}: No valid country code")
                        continue
                    
                    # Open chat with number
                    webbrowser.open(f'whatsapp://send?phone={number.replace("+", "")}')
                    time.sleep(3)
                    
                    # Send the message with proper line breaks
                    self.send_message(self.message)
                    
                    self.progress.emit(f"Message sent to {number}")
                    
                    delay = random.randint(1, 10)
                    time.sleep(delay)
                
                except Exception as e:
                    self.error.emit(f"Error sending to {number}: {str(e)}")
                    continue
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class WhatsAppApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Message Sender")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Message input
        message_label = QLabel("Message to Send:")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter your message here...")
        self.message_input.setMinimumHeight(200)
        
        # Numbers input section
        numbers_section = QWidget()
        numbers_layout = QVBoxLayout(numbers_section)
        
        numbers_label = QLabel("Phone Numbers:")
        self.numbers_list = QListWidget()
        
        # Country code selection
        country_layout = QHBoxLayout()
        self.country_combo = QComboBox()
        self.country_combo.addItems(sorted(COUNTRY_CODES.keys()))
        country_layout.addWidget(QLabel("Select Country:"))
        country_layout.addWidget(self.country_combo)
        
        # Multiple numbers input
        self.number_input = QTextEdit()
        self.number_input.setPlaceholderText("Enter phone numbers (one per line, with or without country code)")
        self.number_input.setMaximumHeight(100)
        
        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Numbers")
        add_button.clicked.connect(self.add_numbers)
        
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_number)
        
        delete_all_button = QPushButton("Delete All")
        delete_all_button.clicked.connect(self.delete_all_numbers)
        
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(delete_all_button)
        
        # Add components to numbers section
        numbers_layout.addWidget(numbers_label)
        numbers_layout.addLayout(country_layout)
        numbers_layout.addWidget(self.number_input)
        numbers_layout.addLayout(button_layout)
        numbers_layout.addWidget(self.numbers_list)
        
        # Main buttons
        main_button_layout = QHBoxLayout()
        send_button = QPushButton("Start Sending")
        send_button.clicked.connect(self.start_sending)
        
        reset_button = QPushButton("Reset All")
        reset_button.clicked.connect(self.reset_data)
        
        main_button_layout.addWidget(send_button)
        main_button_layout.addWidget(reset_button)
        
        # Add all sections to main layout
        layout.addWidget(message_label)
        layout.addWidget(self.message_input)
        layout.addWidget(numbers_section)
        layout.addLayout(main_button_layout)
        
        # Initialize sender thread
        self.sender_thread = None
        
        # Status bar
        self.statusBar().showMessage("Ready")

    def format_number(self, number):
        """Format the phone number with proper country code"""
        number = number.strip().replace(" ", "").replace("-", "")
        
        # Check if number already has a country code
        for code in COUNTRY_CODES.values():
            if number.startswith(code):
                return number
            elif number.startswith(code.strip("+")):
                return "+" + number
        
        # Add selected country code if no code present
        selected_country = self.country_combo.currentText()
        country_code = COUNTRY_CODES[selected_country]
        return f"{country_code}{number}"

    def add_numbers(self):
        numbers_text = self.number_input.toPlainText().strip()
        if not numbers_text:
            return
            
        numbers = numbers_text.split('\n')
        added_count = 0
        
        for number in numbers:
            number = number.strip()
            if number:
                formatted_number = self.format_number(number)
                # Check if number already exists
                exists = False
                for i in range(self.numbers_list.count()):
                    if self.numbers_list.item(i).text() == formatted_number:
                        exists = True
                        break
                
                if not exists:
                    self.numbers_list.addItem(formatted_number)
                    added_count += 1
        
        self.number_input.clear()
        self.statusBar().showMessage(f"Added {added_count} new numbers")

    def delete_number(self):
        for item in self.numbers_list.selectedItems():
            self.numbers_list.takeItem(self.numbers_list.row(item))

    def delete_all_numbers(self):
        self.numbers_list.clear()
        self.statusBar().showMessage("All numbers cleared")

    def start_sending(self):
        if not self.message_input.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Please enter a message to send.")
            return
        
        if self.numbers_list.count() == 0:
            QMessageBox.warning(self, "Error", "Please add at least one phone number.")
            return
        
        # Show instructions
        QMessageBox.information(self, "Instructions", 
            "1. Make sure WhatsApp Desktop is installed\n"
            "2. The application will open WhatsApp automatically\n"
            "3. Please wait for WhatsApp to load completely\n"
            "4. Do not move your mouse or keyboard during sending\n"
            "5. The process will take some time depending on the number of contacts")
        
        numbers = [self.numbers_list.item(i).text() for i in range(self.numbers_list.count())]
        message = self.message_input.toPlainText()
        
        self.sender_thread = WhatsAppSender(numbers, message)
        self.sender_thread.finished.connect(self.sending_finished)
        self.sender_thread.error.connect(self.sending_error)
        self.sender_thread.progress.connect(self.update_progress)
        self.sender_thread.start()

    def sending_finished(self):
        QMessageBox.information(self, "Success", "All messages have been sent successfully!")
        self.statusBar().showMessage("All messages sent successfully")

    def sending_error(self, error_message):
        self.statusBar().showMessage(f"Error: {error_message}")

    def update_progress(self, message):
        self.statusBar().showMessage(message)

    def reset_data(self):
        self.message_input.clear()
        self.number_input.clear()
        self.numbers_list.clear()
        self.statusBar().showMessage("All data reset")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WhatsAppApp()
    window.show()
    sys.exit(app.exec_()) 