import sys
import random
import time
import webbrowser
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTextEdit, QListWidget, QPushButton, 
                            QLineEdit, QMessageBox, QLabel)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import pyautogui
import keyboard

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
            pyautogui.hotkey('shift', 'enter')  # New line without sending
            time.sleep(0.5)
        
        # Send the message
        keyboard.press_and_release('enter')
        time.sleep(1)

    def run(self):
        try:
            # Open WhatsApp Desktop (assuming it's installed in the default location)
            whatsapp_path = os.path.join(os.getenv('LOCALAPPDATA'), 'WhatsApp', 'WhatsApp.exe')
            if os.path.exists(whatsapp_path):
                os.startfile(whatsapp_path)
            else:
                # Fallback to WhatsApp Web
                webbrowser.open('https://web.whatsapp.com')
            
            # Wait for WhatsApp to open
            time.sleep(10)
            
            for number in self.numbers:
                try:
                    # Add country code if not present
                    if not number.startswith('+'):
                        number = '+' + number
                    
                    # Open chat with number
                    webbrowser.open(f'whatsapp://send?phone={number.replace("+", "")}')
                    time.sleep(3)
                    
                    # Send the message with proper line breaks
                    self.send_message(self.message)
                    
                    self.progress.emit(f"Message sent to {number}")
                    
                    # Random delay between 1-10 seconds
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
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Message input
        message_label = QLabel("Message to Send:")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter your message here...")
        self.message_input.setMinimumHeight(200)  # Make text area bigger
        
        # Numbers input
        numbers_label = QLabel("Phone Numbers:")
        self.numbers_list = QListWidget()
        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Enter phone number (with country code, e.g., +1234567890)")
        
        # Buttons
        add_button = QPushButton("Add Number")
        add_button.clicked.connect(self.add_number)
        
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_number)
        
        send_button = QPushButton("Start Sending")
        send_button.clicked.connect(self.start_sending)
        
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_data)
        
        # Layout for number input and buttons
        number_layout = QHBoxLayout()
        number_layout.addWidget(self.number_input)
        number_layout.addWidget(add_button)
        number_layout.addWidget(delete_button)
        
        # Add all widgets to main layout
        layout.addWidget(message_label)
        layout.addWidget(self.message_input)
        layout.addWidget(numbers_label)
        layout.addWidget(self.numbers_list)
        layout.addLayout(number_layout)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(send_button)
        button_layout.addWidget(reset_button)
        layout.addLayout(button_layout)
        
        # Initialize sender thread
        self.sender_thread = None

    def add_number(self):
        number = self.number_input.text().strip()
        if number:
            self.numbers_list.addItem(number)
            self.number_input.clear()

    def delete_number(self):
        current_row = self.numbers_list.currentRow()
        if current_row >= 0:
            self.numbers_list.takeItem(current_row)

    def start_sending(self):
        if not self.message_input.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Please enter a message to send.")
            return
        
        if self.numbers_list.count() == 0:
            QMessageBox.warning(self, "Error", "Please add at least one phone number.")
            return
        
        # Show instructions before starting
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

    def sending_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")

    def update_progress(self, message):
        self.statusBar().showMessage(message)

    def reset_data(self):
        self.message_input.clear()
        self.numbers_list.clear()
        self.number_input.clear()
        self.statusBar().clearMessage()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WhatsAppApp()
    window.show()
    sys.exit(app.exec_()) 