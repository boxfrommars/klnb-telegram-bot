import logging

from telegram import Message

logger = logging.getLogger(__name__)


class SpamPreventer:
    group_last_message: dict = {}
    group_settings: dict = {}

    default_settings: dict = {
        'delay': 15 * 60
    }

    is_enabled: bool = True

    def __init__(self, settings: dict = None) -> None:
        if settings is not None:
            self.group_settings = settings

    def is_spam(self, message: Message, group: str = 'default') -> bool:

        if group not in self.group_settings.keys():
            settings = self.default_settings
        else:
            settings = self.group_settings[group]

        if group not in self.group_last_message.keys():
            last_msg_dt = None
            is_spam = False
        else:
            last_msg_dt = self.group_last_message[group]
            is_spam = (message.date - last_msg_dt).seconds < settings['delay']

        is_spam = is_spam and self.is_enabled

        logger.info('spam checker: %s %s %s', group, is_spam, last_msg_dt)

        if not is_spam:
            self.group_last_message[group] = message.date

        return is_spam

    def enable(self) -> None:
        self.is_enabled = True

    def disable(self) -> None:
        self.is_enabled = False


