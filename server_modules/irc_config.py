from configparser import ConfigParser
from os import getcwd, path


class IRCConfig:
    def __init__(self):
        self.ServerSettings = self.__ServerSettings()
        self.MaintenanceSettings = self.__MaintenanceSettings()
        self.UserSettings = self.__UserSettings()
        self.__CrowConfigParser = self.__CrowConfigParsingUtils(
            [self.ServerSettings, self.MaintenanceSettings, self.UserSettings]
        )

    class __ServerSettings:
        def __init__(self):
            self.Port = 6667
            self.Interface = "127.0.0.1"
            self.PingInterval = 3
            self.ServerName = "Crow IRC"
            self.ServerDescription = "WIP IRC Server implementation w/ Twisted."
            self.ServerWelcome = "Welcome to Crow IRC"

    class __MaintenanceSettings:
        def __init__(self):
            self.RateLimitClearInterval = 5
            self.FlushInterval = 1
            self.ChannelScanInterval = 1
            self.ChannelUltimatum = 7

    class __UserSettings:
        def __init__(self):
            self.MaxUsernameLength = 35
            self.MaxNicknameLength = 35
            self.MaxClients = 5
            self.Operators = {"Admin": "Password", "Admin2": "Password2"}

    class __CrowConfigParsingUtils:
        def __init__(self, settings_classes):
            self.config = ConfigParser()
            self.crow_path = getcwd().split("/bin")[0]
            self.config_path = self.crow_path + "/crow.ini"
            self.settings_classes = settings_classes
            self.section_names = [type(x).__name__.split("__")[1] for x in self.settings_classes]
            self.section_associations = {x: y for x, y in zip(self.section_names, self.settings_classes)}
            self.section_mappings = {
                x: {z: getattr(y, z) for z in y.__dict__.keys()}
                for x, y in zip(self.section_names, self.settings_classes)
            }
            self.read_config()

        def config_exists(self):
            return path.exists(self.config_path)

        def read_config(self):
            error_message_entry = "****Error in config: Invalid entry: {}." \
                                  "\nReason: {}" \
                                  "\nUsing default value for this entry instead.****"

            error_message_section_missing = "****Error in config: Missing section: {}." \
                                            "\nUsing default values for this section instead.****"

            error_message_entry_missing = "****Error in config: Missing entry: {}." \
                                          "\nUsing default value for this entry instead.\n****"

            # Thank god these loops are only run once lol
            self.config.read(self.config_path)
            for section, section_options in self.section_mappings.items():
                for option_name, option_value in self.section_mappings[section].items():
                    if section not in self.config.keys():
                        print("1")
                        #print(error_message_section_missing.format(section))
                    else:
                        if option_name not in self.config[section]:
                            print("2")
                            #print(error_message_entry_missing.format(option_name))
                        else:
                            user_defined_option = self.config[section][option_name]
                            option_type = type(option_value)
                            try:
                                if option_type is dict:
                                    user_defined_option = dict(x.split(":") for x in user_defined_option.split(','))
                                if option_type is list:
                                    user_defined_option = [x.split(" ") for x in user_defined_option.split(',')]
                                user_defined_option = option_type(user_defined_option)
                                setattr(self.section_associations[section], option_name, user_defined_option)
                            except ValueError:
                                print("3")
                                #print(error_message_entry.format(
                                #    option_name, "Option is of an invalid type. Should be: {}".format(option_type)
                                #))

        def flush_config(self):
            with open(self.config_path, "w") as crow_ini:
                for section in self.section_names:
                    self.config.add_section(section)
                    for option_name, option_value in self.section_mappings[section].items():
                        if type(option_value) is dict:
                            new_value = ""
                            for key, value in option_value.items():
                                new_value += "{}:{},".format(key, value)
                            option_value = new_value[:-1]  # remove trailing comma. could just use rstrip but with the
                        if type(option_value) is list:     # way this is written, there always will be a leading comma.
                            new_value = ""
                            for value in option_value:
                                new_value += "{},".format(value)
                            option_value = new_value[:-1]
                        self.config.set(section, option_name, str(option_value))
                self.config.write(crow_ini)
