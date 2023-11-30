import sys
from asyncio import CancelledError

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtWidgets import QWidget

from services.client_side import ChatClient
from utils.exceptions import ClientAuthenticationError


class LoginWindow(QWidget):
    login_successful = pyqtSignal()

    def __init__(self, chat_client: ChatClient):
        super().__init__()
        self.errorLabel = None
        self.__client = chat_client
        self.loginButton = None
        self.__password = None
        self.__username = QLineEdit(self)
        self.set_login_layout()

    def set_login_layout(self):
        """

        :return:
        """
        self.setWindowTitle('Login')
        self.setLayout(QVBoxLayout())

        self.__username.setPlaceholderText('Username')
        self.layout().addWidget(self.__username)

        self.__password = QLineEdit(self)
        self.__password.setPlaceholderText('Password')
        self.__password.setEchoMode(QLineEdit.Password)
        self.layout().addWidget(self.__password)

        self.loginButton = QPushButton('Login', self)
        self.layout().addWidget(self.loginButton)
        # Add message error widget
        self.errorLabel = QLabel(self)
        # Set text color to red
        self.errorLabel.setStyleSheet("color: red")
        # Initially hidden
        self.errorLabel.hide()
        self.layout().addWidget(self.errorLabel)
        # Connect button click to a function
        self.loginButton.clicked.connect(self.on_login_clicked)

    def on_login_clicked(self):
        """

        :return:
        """
        # TODO: encrypt data
        # TODO: error message when no username and/or password

        try:
            self.__client.login(self.__username.text(), self.__password.text())
            # Emit the signal
            self.login_successful.emit()
            # Optionally, hide the login window
            self.hide()
        except ClientAuthenticationError as _:
            # TODO print auth failed on the gui
            print(f"[WARNING] Authentication failed, Trying again.")
            self.errorLabel.setText("Authentication failed. Please try again.")
            self.errorLabel.show()
            self.__username.clear()
            self.__password.clear()
        except (KeyboardInterrupt, CancelledError):
            print("[INFO] Shutting down the client.")
            sys.exit(0)
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")
            sys.exit(1)
