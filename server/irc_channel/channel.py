# ToDo: ChannelOwner required, ChannelOperator required decorators (although it might be unneeded)
from .decorators import *
from utils.irc_quitreason_enum import QuitReason
from time import time
from secrets import token_urlsafe


class IRCChannel:
    """ Represent channels on the server and implement methods for handling them and participants. """
    # ToDo: A lot of these can be combined into one property I think.
    def __init__(self, name, channelmanager):
        self.channel_name = name
        self.channel_owner = None
        self.last_owner_login = None
        self.scheduled_for_deletion = False
        self.deleted = False
        self.users = []

        """
        Op_Accounts = {
            Account_Name: {
                    "Current_User": User, - this is like channel_owner being set to the current logged user instance
                    "Password": Password,
                    "Permissions": Permissions,
                }
            }
        """
        self.op_accounts = {}
        self.op_default_perms = ["ban", "kick", "mute"]
        self.valid_perms = ["ban", "kick", "mute", "topic", "motd"]  # bad, but will do for now.

        self.channel_modes = []
        self.channel_owner_account = []
        self.channel_manager = channelmanager

    def __str__(self):
        host_list = [x.hostmask for x in self.users]
        return "ChannelOwner: {}\nChannelOperators: {}\nChannelName: {}\nHostMaskList: {}\nNickList: {}\n".format(
            self.channel_owner, None, self.channel_name, host_list, self.get_nicknames()
        )  # ToDo: ChannelOperators in __str__

    def add_user(self, user):
        """ Map a user to the channel, send a JOIN notice to everyone currently in it. """

        if self.deleted:
            return "The channel is being deleted. \nWait a moment and try again to create a new channel with its name."

        if user in self.users:
            return

        user.protocol.join(user.hostmask, self.channel_name)
        user.channels.append(self)
        self.users.append(user)
        join_rpl = ":{} JOIN :{}".format(user.hostmask, self.channel_name)
        [x.protocol.sendLine(join_rpl) for x in self.users if x is not user]
        self.send_names(user)

    def remove_user(self, user, leave_message, reason=QuitReason.UNSPECIFIED, timeout_seconds=None):
        """ Unmap a user instance from the channel and broadcast the reason. """
        if reason.value == QuitReason.LEFT.value:
            if leave_message is None:
                leave_message = "{} :User Left Channel.".format(self.channel_name)
            else:
                leave_message = "{} :{}".format(self.channel_name, leave_message)
        elif reason.value == QuitReason.DISCONNECTED.value:
            if leave_message is None:
                leave_message = "User Quit Network."
        elif reason.value == QuitReason.TIMEOUT.value and timeout_seconds is not None:
            leave_message = timeout_seconds
        else:
            leave_message = "Unspecified Reason."
        if user is self.channel_owner:
            self.channel_owner = None
            self.last_owner_login = time()  # So it won't be deleted if the owner logged in 7 days ago and never
            # logged out, thus never resetting the last owner login time to something that would prevent deletion.

        self.users.remove(user)
        self.broadcast_line(reason.value.format(user.hostmask, leave_message))
        user.channels.remove(self)

    def get_nicknames(self):
        """ Get all the nicknames of the currently participating users in the channel. """
        return [x.nickname for x in self.users]

    @authorization_required(requires_channel_owner=True)
    def get_operator(self, caller, name=None):
        """  If name is none, list all operator names in channel. otherwise, attempt to list all details which pertain
        to an operator with the given name. """
        if self.op_accounts:
            if name is None:
                return "Get Account: (Channel: {} - listing all account names: {})".format(self.channel_name, str([i for i in self.op_accounts.keys()]))
            account_details = next((x for x in self.op_accounts if x == name), None)
            if account_details is not None:
                return "Get Account: (Channel: {} - Username: {} - results: {})".format(self.channel_name, name, self.op_accounts.get(name))
            return "Get Account: (Channel: {} - Username: {} - An account with that name does not exist.)".format(self.channel_name, name)
        return "Get Account: (Channel: {} - There are no operator accounts for this channel.)".format(self.channel_name)

    @authorization_required(requires_channel_owner=True)
    def add_operator(self, caller, name):
        """ Add a new operator account using the given name. """
        if name in self.op_accounts:
            return "Add Account: (Channel: {} - Username: {} - That name is already in use.)".format(self.channel_name, name)
        elif name is None:
            return "Add Account: (Channel: {} - Username: None - Name cannot be None.)".format(self.channel_name)
        account_password = token_urlsafe(32)
        self.op_accounts[name] = {
            "current_user": None,
            "password": account_password,
            "permissions": []
        }
        return "Add Account: (Channel: {} - Username: {} - Password: {} - Account added.)".format(self.channel_name, name, account_password)

    @authorization_required(requires_channel_owner=True)
    def delete_operator(self, caller, name):
        """ Delete an operator account using the given name. """
        if name not in self.op_accounts:
            return "Delete Account: (Channel: {} - Username: {} - Account with that name does not exist.)".format(self.channel_name, name)
        elif name is None:
            return "Delete Account: (Channel: {} - Username: None - Name cannot be None.)".format(self.channel_name)
        logged_user = self.op_accounts[name]["current_user"]
        if logged_user is not None:
            logged_user.protocol.send_msg(logged_user.nickname, "{}: The account you were logged into has been deleted.".format(self.channel_name))
        del self.op_accounts[name]
        return "Delete Account: (Channel: {} - Username: {} - Account was Deleted.)".format(self.channel_name, name)

    @authorization_required(requires_channel_owner=True)
    def set_operator_name(self, caller, name, new_name):
        """ Set an existing operator account's name to the specified new one. """
        if name not in self.op_accounts:
            return "Set Account Name: (Channel: {} - Username: {} - Account with that name does not exist.)".format(self.channel_name, name)
        elif name is None or new_name is None:
            return "Set Account Name: (Channel: {} - You must supply all parameters (name, new usernamename)".format(self.channel_name)
        logged_user = self.op_accounts[name]["current_user"]
        if logged_user is not None:
            logged_user.protocol.send_msg(logged_user.nickname, "{}: The name of the account you were logged into has been changed to '{}'".format(self.channel_name, new_name))
        self.op_accounts[new_name] = self.op_accounts.pop(name)
        return "Set Account Name: (Channel: {} - Username: {} - Account name changed.)".format(self.channel_name, name)

    @authorization_required(requires_channel_owner=True)
    def set_operator_password(self, caller, name, new_password):
        """ Set an existing operator account's password to the specified new one. """
        if name not in self.op_accounts:
            return "Set Account Password: (Channel: {} - Username: {} - Account with that name does not exist.)".format(self.channel_name, name)
        elif name is None or new_password is None:
            return "Set Account Name: (Channel: {} - You must supply all parameters (usernamename, new password)".format(self.channel_name)
        logged_user = self.op_accounts[name]["current_user"]
        if logged_user is not None:
            logged_user.protocol.send_msg(logged_user.nickname, "{}: The name of the account you were logged into has been changed to '{}'".format(self.channel_name, new_password))
        self.op_accounts[name]["password"] = new_password
        return "Set Account Password: (Channel: {} - Username: {} - Account Password changed.)".format(self.channel_name, name)

    def who(self, user, server_host):
        """ Return information about the channel to the caller. Used for WHO commands. """
        if user.nickname not in self.get_nicknames():
            return user.rplhelper.err_notonchannel("You must be on the channel to perform a /who")
        return [tuple([x.username, x.hostmask, server_host, x.nickname, x.status, 0, x.realname]) for x in self.users]

    def login_owner(self, name, password, user):
        """
        Attempt to map a user as an owner. If the channel currently has someone set as an owner/the person
        issuing the command isn't in the channel, return error.
        """
        if user.nickname not in self.get_nicknames():
            return user.rplhelper.err_noprivileges("You must be on the channel to login as the owner.")
        elif name != self.channel_owner_account[0] or password != self.channel_owner_account[1]:
            return user.rplhelper.err_passwordmismatch()
        elif self.channel_owner is not None:
            return user.rplhelper.err_noprivileges("Channel already has an acting owner.")
        else:
            self.channel_owner = user
            self.last_owner_login = int(time())
            if self.scheduled_for_deletion:
                pass  # ToDo: Tell everyone channel will not be deleted.
            self.scheduled_for_deletion = False
            return "You have logged in as the channel owner of {}".format(self.channel_name)

    def send_names(self, user):
        """ Sends the nicknames of users currently participating in the channel to the target user. """
        user.protocol.names(user.nickname, self.channel_name, self.get_nicknames())

    def rename_user(self, user, new_nick):
        """ When a user is renamed, update the names list and send a notice to everyone in the channel. """
        for user_ in self.users:
            if user_.protocol is not user:
                user_.protocol.sendLine(":{} NICK {}".format(user.hostmask, new_nick))

    def get_modes(self):
        return "getting channel modes not implemented"  # ToDo

    def set_mode(self):
        return "setting channel modes not implemented"  # ToDo

    def delete_channel(self):
        self.channel_manager.delete_channel(self)

    def broadcast_message(self, message, sender):
        for user in self.users:
            if user.hostmask != sender:
                user.protocol.privmsg(sender, self.channel_name, message)

    def broadcast_line(self, line):
        for user in self.users:
            user.protocol.sendLine(line)

    def broadcast_notice(self, notice):
        for user in self.users:
            notice_line = ":{} NOTICE {} :{}".format(user.hostmask, self.channel_name, notice)
            user.protocol.sendLine(notice_line)

