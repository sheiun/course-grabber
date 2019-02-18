from abc import ABCMeta, abstractmethod
from enum import Enum


class StatusType(Enum):
    NOT_LOGGED_IN = '未登入'
    LOGGED_IN = '已登入'
    LOGGED_OUT = '已登出'


class AbstractSchool(metaclass=ABCMeta):

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}

    @property
    @abstractmethod
    def status(self):
        raise NotImplementedError

    @abstractmethod
    def login(self, data):
        raise NotImplementedError

    @abstractmethod
    def logout(self):
        raise NotImplementedError

    @abstractmethod
    def grab(self, course):
        raise NotImplementedError
