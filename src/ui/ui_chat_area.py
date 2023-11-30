from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, \
    QLabel

from services.client_side import ChatClient


class ChatWindow(QWidget):
    MESSAGE_CMDS = {"active_users": "/u",
                    "message_user": "@%s %s"}

    def __init__(self, chat_client: ChatClient):
        super().__init__()

        self.__current_user = None
        self.usernameLabel = None
        self.rightLayout = None
        self.mainLayout = None
        self.placeholder = None
        self.sendButton = None
        self.userList = QListWidget()
        self.messageInput = None
        self.messageDisplay = QTextEdit()
        self.chatArea = None
        self.setWindowTitle('Chat App')

        self.__chat_client = chat_client

        self.__set_layout_ph()
        self.setup_user_list()
        self.setup_placeholder()

    def __set_layout_ph(self):
        """
        Set main layout and add placeholders
        :return:
        """
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        self.placeholder = QLabel("Messenger Clone", self)
        self.placeholder.setAlignment(Qt.AlignCenter)
        label = QLabel("Online Users")
        self.mainLayout.addWidget(self.placeholder)
        self.mainLayout.addWidget(label)

    def setup_user_list(self):
        """

        :return:
        """
        # Create the label
        # Add the label to the layout
        self.userList.itemClicked.connect(self.on_user_clicked)
        self.mainLayout.addWidget(self.userList)

    def setup_placeholder(self):
        """

        :return:
        """
        # Chat Area (Initially Hidden)
        self.setup_chat_area()
        self.chatArea.hide()

        # Add both to the layout
        self.rightLayout = QVBoxLayout()
        self.rightLayout.addWidget(self.chatArea)
        self.mainLayout.addLayout(self.rightLayout)

    def setup_chat_area(self):
        """

        :return:
        """
        self.chatArea = QWidget()
        chatLayout = QVBoxLayout(self.chatArea)
        # Label for the username
        self.usernameLabel = QLabel("")
        chatLayout.addWidget(self.usernameLabel)

        self.messageDisplay.setReadOnly(True)
        chatLayout.addWidget(self.messageDisplay)

        self.messageInput = QLineEdit()
        chatLayout.addWidget(self.messageInput)

        self.sendButton = QPushButton('Send')
        self.sendButton.clicked.connect(self.on_send_clicked)
        chatLayout.addWidget(self.sendButton)

    def on_user_clicked(self, item):
        # Update the username label with the selected user
        self.messageDisplay.clear()
        self.usernameLabel.setText(f"Selected User: {item.text()}")
        self.__current_user = item.text()
        self.chatArea.show()

    def on_send_clicked(self):
        message = self.messageInput.text()
        if message:
            # Update the chat display
            current_text = self.messageDisplay.toPlainText()
            new_text = f"{current_text}\nMe: {message}" if current_text else f"Me: {message}"

            self.messageDisplay.setText(new_text)
            # TODO send message to a user
            self.__chat_client.send_message(self.MESSAGE_CMDS["message_user"] % (self.__current_user,
                                                                                 message))
            # Clear the input field
            self.messageInput.clear()

    def get_active_users(self):
        self.__chat_client.send_message(self.MESSAGE_CMDS["active_users"])


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    chatWindow = ChatWindow()
    chatWindow.show()
    sys.exit(app.exec_())
