from configparser import ConfigParser
from os import getcwd, path
from sys import exc_info


class IRCConfig:
    """ Represent the IRC Config file. """
    def __init__(self):
        self.ServerSettings = None
        self.UserSettings = None
        self.NicknameSettings = None
        self._config = ConfigParser()
        self._crow_path = getcwd().split("/bin")[0]
        self._config_path = self._crow_path + "/crow.ini"

    def config_exists(self):
        return path.exists(self._config_path)

    def read_config(self):
        errors = None
        try:
            self._config.read(self._config_path)
            self.ServerSettings = {
                "Port": int(self._config['ServerSettings']['Port']),
                "ServerName": self._config['ServerSettings']['ServerName'],
                "ServerDescription": self._config['ServerSettings']['ServerDescription'],
                "ServerWelcome": self._config['ServerSettings']['ServerWelcome']
            }
            self.UserSettings = {
                "MaxLength": int(self._config['UserSettings']['MaxLength']),
                "MaxClients": int(self._config['UserSettings']['MaxClients']),
                "Operators": dict(x.split(":") for x in self._config['UserSettings']['Operators'].split(','))
            }
            self.NicknameSettings = {
                "MaxLength": int(self._config['NicknameSettings']['MaxLength'])
            }
        except Exception as e:
            errors = "{}: {}".format(exc_info(), str(e))
        return errors

    def create_config(self):
        errors = None
        with open(self._config_path, 'w') as crow_ini:
            self._config.add_section("ServerSettings")
            self._config.set("ServerSettings", "Port", "6667")
            self._config.set("ServerSettings", "ServerName", "Crow IRC")
            self._config.set("ServerSettings", "ServerDescription", "WIP IRC Server implementation w/ Twisted.")
            self._config.set("ServerSettings", "ServerWelcome", "Welcome to Crow IRC")
            self._config.add_section("NicknameSettings")
            self._config.set("NicknameSettings", "MaxLength", "35")
            self._config.add_section("UserSettings")
            self._config.set("UserSettings", "MaxLength", "35")
            self._config.set("UserSettings", "MaxClients", "5")
            self._config.set("UserSettings", "Operators", "Admin:Password,Admin2:Password")  # ToDo: No plaintext
            try:
                self._config.write(crow_ini)
            except Exception as e:
                errors = str(e)
        return errors
