import os
import re
from abc import ABC

from .network_socket import NetworkSocket
from .redis_manager import RedisServerManager


def generate_session_token():
    # FIXME: security issue
    return os.urandom(16).hex()


def parse_message(input_message):
    """

    :param input_message:
    :return:
    """
    pattern = r"^@(\S+)\s+(.+)"
    match = re.match(pattern, input_message)
    if match:
        return match.groups()
    else:
        return None, None


class Command(ABC):
    def execute(self, *args):
        raise NotImplementedError

    @staticmethod
    def _socket_sendall(conn, message: str):
        conn.sendall(message.encode())


class MessageCommand(Command):
    def execute(self, sender: str, receiver: str, conn_clients: dict, msg: str):
        conn_receiver = conn_clients.get(receiver)
        if conn_receiver:
            self._socket_sendall(conn_receiver, f"From {sender}: {msg}")
        else:
            self._socket_sendall(conn_clients.get(sender), f"NOT_FOUND: No user found !")


class ActiveUsersCommand(Command):
    def execute(self, redis_client: RedisServerManager, *args):
        return redis_client.get_active_users()


class SlashMessage:
    __COMMANDS = {'/u': ActiveUsersCommand()}

    def __init__(self, message):
        self.cmd = message

    def get_command(self):
        return self.__COMMANDS.get(self.cmd)


class AtMessage:
    def __init__(self, message):
        self.message = message
        self.command = MessageCommand()
