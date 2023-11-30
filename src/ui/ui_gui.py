import asyncio
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from services.client_side import ClientChatGui
from .ui_login_view import LoginWindow
from .ui_chat_area import ChatWindow
from utils import AsyncioThread


class ChatApp(QApplication):

    def __init__(self, argv):
        # TODO close connection
        # TODO Add logout button
        super().__init__(argv)
        self.__users_list_obj = []
        self.timer = QTimer(self)
        self.__client = ClientChatGui()
        self.__client_chat = self.__client.chat_client
        # Connect to client
        self.__loginWindow = LoginWindow(self.__client_chat)
        self.__chatWindow = ChatWindow(self.__client_chat)
        self.__setup_ui()

        # Connect aboutToQuit signal to a method
        self.aboutToQuit.connect(self.on_about_to_quit)

        # Start the asyncio event loop in a separate thread
        self.loop = asyncio.new_event_loop()
        self.thread = AsyncioThread(self.loop)
        self.thread.start()

    def __setup_ui(self):
        """

        :return:
        """
        try:
            self.__client_chat.connect()
        except ConnectionRefusedError:
            print("[WARNING] Server is unreachable")
            sys.exit(1)
        # Connect the login_successful signal to a slot
        self.__loginWindow.login_successful.connect(self.show_chat_window)
        # Connect the login_successful signal to a slot
        self.__client.message_received.connect(self.chat_message_received)
        self.__loginWindow.show()

    def __get_online_users(self):
        """

        :return:
        """
        self.__chatWindow.get_active_users()

    def chat_message_received(self):
        """

        :return:
        """
        print(f"MESSAGE {self.__client.current_message}")
        try:
            rcv, message = self.__client.current_message.split(":")
        except ValueError:
            return
        if rcv == "ACTIVE_USERS":
            from ast import literal_eval
            users_list_str = message
            try:
                self.__users_list_obj = literal_eval(users_list_str)
                # FIXME no need to update view when same users
                self.__chatWindow.userList.clear()
                self.__chatWindow.userList.addItems(self.__users_list_obj)
            except Exception as err:
                self.__chatWindow.userList.addItem("No available users")
                print(err)
        elif rcv in self.__users_list_obj:
            self.__chatWindow.messageDisplay.append(self.__client.current_message)

    def show_chat_window(self):
        """

        :return:
        """
        self.__loginWindow.hide()
        self.__chatWindow.show()
        # Schedule the reception task
        asyncio.run_coroutine_threadsafe(self.__client.rcv_message(), self.loop)
        # Get the user list before updating
        self.__get_online_users()
        # Connect timeout signal to get_active_users
        self.timer.timeout.connect(self.__get_online_users)
        # Set the interval to 3000 milliseconds (3 seconds)
        self.timer.setInterval(3000)
        # Start the timer
        self.timer.start()

    def on_about_to_quit(self):
        """
        Graceful application shutdown
        :return:
        """
        # Cancel all the current tasks
        self.thread.stop()
        # stop the event loop
        self.loop.call_soon_threadsafe(self.loop.stop)
        # Stop the thread
        self.thread.quit()
        self.thread.wait()
        # Logout a user and close client socket
        self.__client_chat.logout()
        self.__client_chat.close()


if __name__ == "__main__":
    try:
        app = ChatApp(sys.argv)
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
