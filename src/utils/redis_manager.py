import hashlib
import json

import redis

from utils.exceptions import RedisConnectionError


def hash_password(password):
    """

    :param password:
    :return:
    """
    # Implement a more secure hashing mechanism
    return hashlib.sha256(password.encode()).hexdigest()


class RedisManager:
    def __init__(self, host='localhost', port=6379, db=0):
        self.__redis_client = redis.Redis(host=host, port=port, db=db)
        # check redis connection
        self.check_connection()

    def check_connection(self):
        """
        Check if a connection can be established to Redis.
        """
        try:
            self.__redis_client.ping()
            print("Successfully connected to Redis.")
        except (redis.exceptions.ConnectionError, redis.exceptions.BusyLoadingError) as e:
            print(f"Failed to connect to Redis: {e}")
            raise RedisConnectionError()

    def set_data(self, key, data, expiry=None):
        """
        Store data in Redis. If expiry is provided, the key will expire after 'expiry' seconds.
        Data is stored in JSON format.
        """
        json_data = json.dumps(data)
        self.__redis_client.set(key, json_data, ex=expiry)

    def get_data(self, key):
        """
        Retrieve data from Redis. Data is returned in Python dictionary format.
        """
        data = self.__redis_client.get(key)
        return json.loads(json.loads(data)) if data else None

    def delete_data(self, key):
        """
        Delete data associated with a key in Redis.
        """
        self.__redis_client.delete(key)

    def update_expiry(self, key, expiry):
        """
        Update the expiry time of a key in Redis.
        """
        self.__redis_client.expire(key, expiry)

    def get_all_keys(self):
        print(self.__redis_client.keys('*'))


class RedisServerManager(RedisManager):
    def __init__(self, host='localhost', port=6379, db=0):
        super().__init__(host, port, db)

    def add_user(self, *args):
        """

        :param args:
        :return:
        """
        username, password = args
        self.__save_user(username, password)

    def delete_user(self, username):
        """

        :param username:
        :return:
        """
        self.__delete_user(username)

    def login(self, *args, hashed=True):
        """
        check auth and add user to active users
        :param hashed:
        :param args:
        :return:
        """
        username, password = args
        if self.__authenticate_user(username, password, hashed):
            print(f"[INFO] Auth success for user {username}!")
            self.__add_active_user(username)
            return True
        print(f"[WARNING] tentative auth for {username}, wrong username or password !")
        return False

    def logout(self, username):
        """

        :param username:
        :return:
        """
        self.__remove_active_user(username)

    def get_active_users(self) -> set:
        """

        :return:
        """
        return self.__redis_client.smembers("active_users")

    def get_all_user(self, username):
        """

        :param username:
        :return:
        """
        return self.__redis_client.hgetall(f"user:{username}")

    def __save_user(self, username, password):
        # TODO what if user already exists
        password_hash = hash_password(password)
        self.__redis_client.hset(f"user:{username}", mapping={"password_hash": password_hash})

    def __delete_user(self, username):
        self.__redis_client.delete(f"user:{username}")

    def __authenticate_user(self, username, password, hashed=True):
        stored_password = self.__redis_client.hget(f"user:{username}", "password_hash")
        if not stored_password:
            return False

        match hashed:
            case True:
                return stored_password.decode() == password
            case False:
                return stored_password.decode() == hash_password(password)

    def __add_active_user(self, username):
        if username not in self.get_active_users():
            self.__redis_client.sadd("active_users", username)
            print(f"[INFO] User {username} added to active users !")

    def __remove_active_user(self, username):
        self.__redis_client.srem("active_users", username)


if __name__ == "__main__":
    test_redis = RedisServerManager()
    print("Active users: ", test_redis.get_active_users())
    print("All users: ", test_redis.get_all_user("aissa"))

    if not test_redis.login("aissa", "test", hashed=False):
        test_redis.add_user("aissa", "test")
    print("Active users: ", test_redis.get_active_users())
    print("Login out user aissa")
    test_redis.logout("aissa")
    test_redis.logout("jon")
    print("Active users: ", test_redis.get_active_users())
    print("All users: ", test_redis.get_all_user("aissa"))
    print("Delete aissa")
    test_redis.delete_user("aissa")
    print("All users: ", test_redis.get_all_user("aissa"))
    test_redis.add_user("aissa", "test")
    test_redis.add_user("jon", "test")
    test_redis.add_user("sofiane", "test")
    print("All users: ", test_redis.get_all_user("aissa"))
    print(f"all user session data ", test_redis.get_data("aissa"))
