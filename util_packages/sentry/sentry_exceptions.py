#  is this bad practice?
class MissingSectionError(Exception):
    def __init__(self, config_class, section):
        message = "The configuration class '{}' does not have the section class '{}'.".format(config_class, section)
        super().__init__(message)


class MissingOptionError(Exception):
    def __init__(self, section, option):
        message = "Section class '{}' has no option named '{}'".format(section, option)
        super().__init__(message)


class CriteriaDescriptionError(Exception):
    def __init__(self, option):
        message = "{}: an option can not have criteria to meet without describing what that criteria is.".format(option)
        super().__init__(message)


class CriteriaNotMetError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class NoDefaultGivenError(Exception):
    def __init__(self, section, option):
        message = "Option '{}' in section class '{}' has not been set and does not have a default value.".format(section, option)
        super().__init__(message)
