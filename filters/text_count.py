import operator
from typing import Callable

from telegram import Message
from telegram.ext import BaseFilter


class TextCountFilter(BaseFilter):

    cnt: int
    op: Callable

    def __init__(self, cnt: int, op: Callable = operator.gt):
        self.cnt = cnt
        self.op = op

    def filter(self, message: Message):

        return self.op(len(message.text.split()), self.cnt)
