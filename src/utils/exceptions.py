class ClientAuthenticationError(Exception):

    def __init__(self, message=None):
        super().__init__()
        self.message = message if message else "Auth Failed"
        print(f"[WARNING] {self.message}")


class RedisConnectionError(Exception):
    def __init__(self, message=None):
        super().__init__()
        self.message = message
