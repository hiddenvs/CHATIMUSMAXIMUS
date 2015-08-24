from plugins import IPlugin
from utils import Messager

import communication_protocols

class TwitchPlugin(IPlugin):
    def __init__(self, settings):
        """
        This class is a convince/internal api wrapper around another plugin
        """
        super(TwitchPlugin, self).__init__(platform='twitch')
        irc_client = communication_protocols.create_irc_bot(
                settings['nick'],                                     
                settings['oauth_token'],
                'irc.twitch.tv',
                channel=settings['channel'])

        irc_client.create_connection()
        irc_client.add_signal_handlers()
        irc_chat_plugin = irc_client.get_plugin(
                communication_protocols.EchoToMessage)
        
        # duck typing our `_messager` instance's `recieve_chat_data` onto plugin
        irc_chat_plugin.recieve_chat_data = self.recieve_chat_data
