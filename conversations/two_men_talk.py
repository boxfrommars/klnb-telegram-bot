from datetime import datetime
from typing import List

from telegram import Message


class TwoMenTalkConversation:
    conversation: List[Message] = []
    window: int = 6  # check last `window` messages for "two men talk"
    time_window: int = 5 * 60  # max seconds between first and last message in the conversation
    last_talk: datetime = None  # last "two men talk" time
    delay: int = 60 * 60 * 3  # time between two "two men talk"

    members: List[str] = ['mol_chan', 'SelianArtem']

    messages_each: int = 2  # each member should send at least `message_each` messages

    def handle(self, message: Message) -> bool:
        if message.from_user.username in self.members:
            self.conversation.append(message)
            self.filter_actual(message.date)
            if self.enough_messages() and self.proper_time(message.date):
                self.conversation = []
                self.last_talk = message.date
                return True
        else:
            self.conversation = []

        return False

    def filter_actual(self, now: datetime) -> None:
        self.conversation = self.conversation[-self.window:]
        self.conversation = list(filter(
            lambda x: (now - x.date).seconds < self.time_window,
            self.conversation
        ))

    def enough_messages(self) -> bool:
        messages_users = [m.from_user.username for m in self.conversation]

        members_enough_messages = all([
            messages_users.count(u) >= self.messages_each for u in self.members
        ])

        total_enough_messages = len(self.conversation) == self.window

        return members_enough_messages and total_enough_messages

    def proper_time(self, now: datetime) -> bool:
        if not self.last_talk:
            return True

        return (now - self.last_talk).seconds > self.delay
