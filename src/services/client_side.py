import asyncio
from typing import Callable

from PyQt5.QtCore import pyqtSignal, QObject

from src.utils import NetworkSocket, async_receive_data, ainput, extract_command
from utils import hash_password
from utils.exceptions import ClientAuthenticationError


class ChatClient:
    # FIXME: not good approach, that is how Qt signals are designed, try to find another solution
    #       PROB: the signal is shared with all instances

    def __init__(self, *args):
        self.__session_token = None
        self.__username = None
        self._socket = NetworkSocket(args) if args else NetworkSocket()

    @property
    def username(self):
        return self.__username

    def connect(self):
        """

        :return:
        """
        self._socket.connect()

    def close(self):
        self._socket.close()

    def stop_tasks(self):
        raise NotImplementedError

    def is_auth(self):
        # FIXME: proper verification
        return self.__session_token is None

    def login(self, username: str, password: str):
        """

        :param username:
        :param password:
        :return:
        """
        # TODO for chat gui, use token instead of username
        if not self.is_auth():
            return
        self._socket.send_data(f"LOGIN:{username}:{hash_password(password)}")
        response = self._socket.receive_data()

        # response = await async_receive_data(self._socket)
        # TODO if not session token found, the unauthenticated
        if response.startswith("SESSION_START"):
            self.__session_token = response.split(':')[1]
            if not self.__username:
                self.__username = username
        else:
            raise ClientAuthenticationError()

    def logout(self):
        """

        :return:
        """
        if self.__session_token:
            try:
                self._socket.send_data(f"LOGOUT:{self.__username}:{self.__session_token}")
                self.__session_token = None
            except ConnectionResetError as _:
                print('[WARNING] cannot logout from server, server unreached')

    def process_message(self, response: str):
        """

        :param response:
        :return:
        """
        status, message = response.split(":")
        if status == "INVALID_SESSION":
            self.__session_token = None
            raise ClientAuthenticationError(message=message)
        # TODO Add message queue
        print(f"{status}: {message}")

    async def rcv_message(self, func: Callable[[str], None] = None):
        if self.is_auth():
            raise ClientAuthenticationError()
        try:
            async for response in self.__receive_message():
                if response:
                    self.process_message(response)
                    if func:
                        func(response)

        except asyncio.CancelledError:
            # TODO Handle cancellation gracefully
            print("[WARNING] Got CancelledError for receive_message coroutine")
            raise

    def send_message(self, message: str):
        # TODO for chat gui, use token instead of username

        if self.is_auth():
            raise ClientAuthenticationError()
        self.__send_message(message)

    def __send_message(self, message):
        """

        :param message:
        :return:
        """
        # TODO for chat gui, use token instead of username

        self._socket.send_data(data=f"MESSAGE:{self.__username}:{self.__session_token}:{message}")

    async def __receive_message(self):
        while True:
            yield await async_receive_data(self._socket)


class ChatClientContext(ChatClient):
    def __init__(self):
        super().__init__()
        # F
        self.__task = set()
        self.__loop = asyncio.get_event_loop()

    async def start_client(self):
        """
        Starts the chat client session.
        """
        print(f"[INFO] Client chat session on {self._socket.host}:{self._socket.port}")

        while True:
            try:
                # Handle user authentication
                if self.is_auth():
                    self._authenticate_user()
                else:
                    # Send and receive messages
                    await self._chat_session()

            except ClientAuthenticationError as e:
                print(f"[ERROR] Authentication failed: {e}. Trying again.")

            except (KeyboardInterrupt, asyncio.CancelledError):
                print("[INFO] Shutting down the client.")
                break
            except Exception as e:
                print(f"[ERROR] An unexpected error occurred: {e}")
                break

    def _authenticate_user(self):
        """
        Handles user authentication.
        """
        print("[INFO] Please authenticate to continue.")
        username = input("Username: ")
        self.__username = username
        password = input("Password: ")
        self.login(username, password)
        print("[INFO] Authentication successful.")

    async def _chat_session(self):
        """
        Create coroutines to read and display messages
        :return:
        """
        # self._loop = asyncio.new_event_loop()
        self.__task.add(asyncio.create_task(self.send_input_messages()))
        self.__task.add(asyncio.create_task(self.rcv_message()))
        await asyncio.gather(*self.__task)

    async def send_input_messages(self):
        # TODO handle the async cancelError
        while True:
            try:
                message = await ainput()
            except asyncio.CancelledError:
                # TODO Handle cancellation gracefully
                print("[WARNING] Got CancelledError for send_message coroutine")
                raise
            # FIXME LOGOUT request doesn't work properly
            cmd = extract_command(message)
            if cmd:
                try:
                    getattr(self, cmd)()
                except AttributeError:
                    pass
            self.send_message(message)

    async def stop_tasks(self):
        """

        :return:
        """
        # Cancel all running asyncio tasks
        print("[WARNING] Stopping current task and stopping event loop !")
        for task in self.__task:
            print(f"[DEBUG] Cancelling task: {task}")
            task.cancel()
        await asyncio.gather(*self.__task, return_exceptions=True)
        self.__task.clear()

    async def __aenter__(self):
        self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._socket:
            self.logout()
            self.close()
            print("[WARNING] Connection closed.")
            await self.stop_tasks()


class ClientChatGui(QObject):
    message_received = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__chat_client = ChatClient()
        self.current_message: str = ''

    async def rcv_message(self):
        """

        :return:
        """
        await self.__chat_client.rcv_message(self.__send_message_signal)

    @property
    def chat_client(self):
        return self.__chat_client

    def __send_message_signal(self, message: str):
        """

        :param message:s
        :return:
        """
        print("[DEBUG] Message received")
        self.current_message = message
        # FIXME, why save current message, sned it with the signal
        self.message_received.emit()
        print("[DEBUG] Signal transferred !")


if __name__ == "__main__":
    async def main():
        try:
            async with ChatClientContext() as server:
                await server.start_client()
        except ConnectionRefusedError:
            print("[WARNING] Server is unreachable")


    # TODO Stop properly, ERROR encountered:
    #   Traceback (most recent call last):
    #   File "C:\Users\aissa\MFI_depends\chat_room\src\services\client_side.py", line 235, in <module>
    #     asyncio.run(main())
    #   File "C:\ProgramData\Anaconda3\envs\chat_room\Lib\asyncio\runners.py", line 190, in run
    #     return runner.run(main)
    asyncio.run(main())
