"""
Module to init socket
"""
import socket


class NetworkSocket:
    def __init__(self, host='localhost', port=12345, socket_type=socket.SOCK_STREAM):
        self.host = host
        self.port = port
        self._socket = socket.socket(socket.AF_INET, socket_type)

    def bind_and_listen(self):
        self._socket.bind((self.host, self.port))
        self._socket.listen()

    def accept_connection(self):
        print("[INFO] Waiting for connection ... ")
        connection, address = self._socket.accept()
        return connection, address

    def connect(self):
        self._socket.connect((self.host, self.port))

    def send_data(self, data, conn=None):
        if conn:
            conn.sendall(data.encode())
        else:
            self._socket.sendall(data.encode())

    def receive_data(self, conn=None, buffer_size=1024):
        if conn:
            return conn.recv(buffer_size).decode()
        else:
            return self._socket.recv(buffer_size).decode()

    def close(self, conn=None):
        if conn:
            conn.close()
        else:
            self._socket.close()


