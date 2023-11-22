import hashlib

from src.utils import NetworkSocket


def hash_password(password):
    # Simple hashing for demonstration; consider using a more secure hashing method
    return hashlib.sha256(password.encode()).hexdigest()


class ClientAuthenticationError(Exception):

    def __init__(self, message=None):
        super().__init__()
        self.message = message
        print(f"[WARNING] {message}")


class ChatClient:
    def __init__(self, *args):
        # TODO save token in redis with corresponding client address
        self.__session_token = None
        self.__username = None
        self._socket = NetworkSocket(args) if args else NetworkSocket()

    def login(self, username, password):
        """

        :param username:
        :param password:
        :return:
        """
        self._socket.send_data(f"LOGIN:{username}:{hash_password(password)}")
        response = self._socket.receive_data()
        # TODO if not session token found, the unauthenticated
        if response.startswith("SESSION_START"):
            self.__session_token = response.split(':')[1]
        else:
            raise ClientAuthenticationError()

    def send_message(self, message):
        """

        :param message:
        :return:
        """
        if self.__session_token:
            self._socket.send_data(f"MESSAGE:{self.__username}:{self.__session_token}:{message}")
            return self._socket.receive_data()
        return "No active session."

    def logout(self):
        """

        :return:
        """
        if self.__session_token:
            self._socket.send_data(f"LOGOUT:{self.__username}:{self.__session_token}")
            self.__session_token = None

    def start_client(self):
        """
        Starts the chat client session.
        """
        print(f"[INFO] Client chat session on {self._socket.host}:{self._socket.port}")

        while True:
            try:
                # Handle user authentication
                if not self.__session_token:
                    # TODO re-authenticate when server responds with 401
                    self._authenticate_user()
                else:
                    # Send and receive messages
                    self._chat_session()

            except ClientAuthenticationError as e:
                print(f"[ERROR] Authentication failed: {e}. Trying again.")
            except KeyboardInterrupt:
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

    def _chat_session(self):
        """
        Handles the chat session after authentication.
        """
        message = input(f"{self.__username}: ")
        status, response = self.send_message(message).split(":")
        # TODO if auth required
        if status == "INVALID_SESSION":
            self.__session_token = None
            raise ClientAuthenticationError(message=response)

        print(f"{status}: {response}")

    def __enter__(self):
        self._socket.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._socket:
            self.logout()
            self._socket.close()
            print("[WARNING] Connection closed.")


if __name__ == "__main__":
    with ChatClient() as server:
        server.start_client()
