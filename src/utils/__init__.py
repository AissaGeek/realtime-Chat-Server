import asyncio
import os
import re
import sys
from abc import ABC

from PyQt5.QtCore import QThread

from .network_socket import NetworkSocket
from .redis_manager import RedisServerManager, hash_password


class AsyncioThread(QThread):
    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        for task in asyncio.all_tasks(self.loop):
            task.cancel()


async def __async_func(conn_type, **kwargs):
    loop = asyncio.get_running_loop()
    data = kwargs.get("data")
    return await loop.run_in_executor(None, conn_type, data)


async def async_send_data(conn, **kwargs):
    await __async_func(conn.send_data, **kwargs)


async def async_receive_data(conn, **kwargs):
    return await __async_func(conn.receive_data, **kwargs)


async def ainput() -> str:
    return (await asyncio.to_thread(sys.stdin.readline)).rstrip('\n')


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


def extract_command(text):
    pattern = r"^\/(\w+)$"
    match = re.match(pattern, text)
    if match:
        # Extracting the first capturing group
        return match.group(1)
    else:
        return None


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
            self._socket_sendall(conn_receiver, f"{sender}: {msg}")
        else:
            self._socket_sendall(conn_clients.get(sender), f"NOT_FOUND: No user found !")


class ActiveUsersCommand(Command):
    def execute(self, **kwargs) -> str:
        redis_client = kwargs.get("redis")
        return f"ACTIVE_USERS:{list(map(lambda x: x.decode(), redis_client.get_active_users()))}"


class UserLogOut(Command):
    def execute(self, **kwargs):
        self_socket_obj = kwargs.get("server_chat_obj")
        return getattr(self_socket_obj, f"_{self_socket_obj.__class__.__name__}__logout_request")


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
