"""
Module to chat server
"""

import json
import threading
from functools import singledispatchmethod

from src.utils import NetworkSocket, RedisServerManager, ActiveUsersCommand, MessageCommand, SlashMessage, AtMessage, \
    parse_message, generate_session_token


# TODO Accept requests
#      Handle messages and redirect to message to users
#      Handle exceptions


class ChatServer:
    # This is a simple bot command, you can add more if you want
    __CHAT_CODES = {"/u": lambda r: f"active users {ActiveUsersCommand().execute(r)}",
                    "@": lambda sender, receiver, conn_clients, msg: MessageCommand().execute(sender, receiver,
                                                                                              conn_clients, msg)}

    def __init__(self, *args):
        # TODO save token in redis with corresponding client address
        # TODO when internal error, please forward it to client
        self._socket = NetworkSocket(args) if args else NetworkSocket()
        # Initialize Redis client
        self._redis = RedisServerManager()
        # clients register
        self.__clients = {}

    @singledispatchmethod
    def handle_message(self, message_wrapper, client_conn, *args):
        """
        dispatcher according to message type
        :param message_wrapper:
        :param client_conn:
        :param args:
        :return:
        """
        raise NotImplementedError

    @handle_message.register
    def _(self, message_wrapper: SlashMessage, client_conn, *args):
        # Handling SlashMessage
        result = message_wrapper.get_command()
        self._socket.send_data(f'REQUEST_PROCESSED:\n{result.execute(self._redis) if result else "Nothing to do !"}',
                               client_conn)

    @handle_message.register
    def _(self, message_wrapper: AtMessage, client_conn, username, *args):
        # Handling AtMessage
        recipient, message = parse_message(message_wrapper.message)
        if recipient and message:
            message_wrapper.command.execute(username, recipient, self.__clients, message)
        else:
            self._socket.send_data('WRONG_ENTRY:No message to send.', client_conn)

    def __message_request(self, *args):
        """

        :param args:
        :return:
        """
        client_conn, username, user_token, message = args
        hashed_password = self._redis.get_data(username)
        # Check if valid user token
        if hashed_password and hashed_password.get('session_token') == user_token:
            # TODO process message if starts with /, means get all active users or send a message to a user
            if message.startswith('/'):
                message_wrapper = SlashMessage(message)
            elif message.startswith('@'):
                message_wrapper = AtMessage(message)
            else:
                # Default handler if no specific type matches
                self._socket.send_data('UNKNOWN_ENTRY:Unknown message type.', client_conn)
                return
            self.handle_message(message_wrapper, client_conn, username)
        else:
            self._socket.send_data('INVALID_SESSION:Token expired', client_conn)

    def __login(self, *args):

        client_conn, username, password_hash = args
        if not self._redis.login(username, password_hash):
            self._socket.send_data(f'AUTH_FAILED:{username}', client_conn)
            return False
        print(f'[DEBUG] All active users : {self._redis.get_active_users()}')

        return True

    def __login_request(self, *args):
        """

        :param args:
        :return:
        """
        client_conn, username, _ = args
        if not self.__login(*args):
            return False
        # check if user session in active_users
        session_token = generate_session_token()
        # 30 minutes expiry
        self._redis.set_data(username, json.dumps({'session_token': session_token}), expiry=1800)
        # TODO send data to specific client address
        self._socket.send_data(f'SESSION_START:{session_token}', client_conn)
        # TODO make user available to other users using redis
        self.__clients[username] = client_conn

    def __logout_request(self, *args):
        """

        :param args:
        :return:
        """
        # FIXME improve logout using client address and username
        client_conn, username, _ = args
        print(f"[INFO] Logging out client {username}: {client_conn}")
        # Remove user session token
        self._redis.delete_data(username)
        # Logout from active sessions
        self._redis.logout(username)
        # Remove current user server session
        del self.__clients[username]
        # FIXME: is logout SESSION_END necessary
        self._socket.send_data('SESSION_END', client_conn)
        print(f"[DEBUG] User {username} logged out")

    def handle_client(self, client_conn):
        try:
            while True:
                data: str = self._socket.receive_data(client_conn)
                if not data:
                    print(f"[WARNING] Closing client connection: {client_conn}")
                    break

                command, *args = data.split(':')
                # FIXME: getattr not cool, if refactoring, the code needs to be maintained
                request_method = getattr(self, f"_{self.__class__.__name__}__{command.lower()}_request")
                # Call appropriate method
                if request_method:
                    request_method(client_conn, *args)
        except ConnectionAbortedError:
            print("Client forcibly closed the connection.")
        except Exception as e:
            # TODO send internal error to user
            print(f"[ERROR] Error happened when trying to handle client requests. REASON {e}")
            # logout current client session
            self.__logout_request(client_conn)
        finally:

            # Close current user session
            self._socket.close(client_conn)
            print(f'[DEBUG] All active users : {self._redis.get_active_users()}')

    def start_server(self):
        """

        :return:
        """
        try:

            while True:
                # TODO consider taking into account the client address too, in redis for
                #      robust authentication and data persistence
                print("[INFO] Server is listening on port 5000")
                client_conn, addr = self._socket.accept_connection()
                print(f"[INFO] connection from {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(client_conn,))
                client_thread.start()
        except Exception as e:
            # TODO make specific errors
            print()

    def __enter__(self):
        """
        When entering, start socket connection
        :return:
        """

        print("[INFO] Starting server, Binding and listening ....")
        self._socket.bind_and_listen()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        when exiting, close socket connection
        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        print("[WARNING] Closing connection ...")
        self._socket.close()


if __name__ == "__main__":
    with ChatServer() as server:
        server.start_server()
