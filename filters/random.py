import random

from telegram import Message
from telegram.ext import BaseFilter


class RandomFilter(BaseFilter):
    prob: float

    def __init__(self, prob: float = 0.5):
        self.prob = prob

    def filter(self, message: Message):
        return random.random() < self.prob
