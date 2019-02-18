from base64 import b64encode
from io import StringIO
from os import remove
from tempfile import NamedTemporaryFile
from threading import Event, Thread, currentThread
from time import sleep

import requests
from lxml import etree
from PIL import Image

from helpers.ntust.code import recognize

from .base import AbstractSchool


class GrabThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, course_id, listen=True, delay=1000):
        super().__init__()
        self._stop_event = Event()
        self.course_id = course_id
        self.listen = listen
        self.delay = delay

    def delay(self):
        self._stop_event.wait(self.delay)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Course(object):
    pass
    # status


class NTUST(AbstractSchool):

    PREFIX_URL = 'https://stuinfo8.ntust.edu.tw/ntust_stu/'
    CODE_URL = f'{PREFIX_URL}VCode.aspx'
    LOGIN_URL = f'{PREFIX_URL}stu.aspx'
    MENU_URL = f'{PREFIX_URL}stu_menu.aspx'
    SEARCH_URL = f'{PREFIX_URL}query_course.aspx'
    CHOOSE_URL = f'{PREFIX_URL}choice_course.aspx'
    CHECK_URL = f'{PREFIX_URL}ChooseDoc.aspx'
    ERROR_URL = f'{PREFIX_URL}hacker_page.aspx'

    VIEW_STATE = b64encode(' '.encode()).decode()

    task_list = list()

    def __init__(self):
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'DES-CBC3-SHA'
        self.session = requests.Session()
        self.session.headers = AbstractSchool.HEADERS

    def status(self):
        return super().status()

    @property
    def verification_code(self):
        res = self.session.get(NTUST.CODE_URL)
        fp = f'{hash(self.session)}.png'
        # FIXME: windows 不能 NamedTemporaryFile 真爛
        with open(fp, 'wb') as file:
            file.write(res.content)
            file.flush()
            text = recognize(fp)
        remove(fp)
        return text

    def login(self, data):
        data["code_box"] = self.verification_code
        data["Button1"] = "登入系統"
        data["__VIEWSTATE"] = NTUST.VIEW_STATE

        res = self.session.post(
            'https://stuinfo8.ntust.edu.tw/ntust_stu/stu.aspx', data=data)

        assert res.url == NTUST.MENU_URL

    def logout(self):
        return super().logout()

    def is_availiabe(self, course_id):
        data = {'courseno': course_id,
                'Button1': '查詢',
                '__VIEWSTATE': NTUST.VIEW_STATE,
                'rand_box': self.verification_code}
        res = self.session.post(NTUST.SEARCH_URL, data=data)

        html = etree.parse(StringIO(res.text), etree.HTMLParser())

        def get_value(text):
            return int(text.replace('人', '').strip())
        restrict = get_value(html.xpath('//*[@id="restrict2"]/font/text()')[0])
        now = get_value(html.xpath('//*[@id="now_peop"]/font/text()')[0])
        return restrict > now

    def verify_to_choose(self):
        self.session.post(
            NTUST.MENU_URL, {'Button1': '選課系統(一般電腦選課)', '__VIEWSTATE': NTUST.VIEW_STATE})
        self.session.post(
            NTUST.CHECK_URL, data={'Button1': '我已了解上述提醒! 進入選課系統', '__VIEWSTATE':  NTUST.VIEW_STATE})

    def choose(self, course_id):
        """
        :course_id 課程代碼
        :return 是否選到課
        """
        print(f'{course_id} 選課中...')

        res = self.session.post(NTUST.CHOOSE_URL, data={
            'courseno': course_id, 'B_add': '加選', '__VIEWSTATE': NTUST.VIEW_STATE})
        if res.url == NTUST.ERROR_URL:
            self.verify_to_choose()
            res = self.session.post(NTUST.CHOOSE_URL, data={
                'courseno': course_id, 'B_add': '加選', '__VIEWSTATE': NTUST.VIEW_STATE})
            if res.url == NTUST.ERROR_URL:
                raise AssertionError

        html = etree.parse(StringIO(res.text), etree.HTMLParser())
        if len(html.xpath('//script')) == 0:
            return True

        msg = html.xpath(
            '//span[@id="err_msg"]/font/text()')[0]

        if any(tag in msg for tag in ('及格', '衝堂')):
            return True

        return False

    def grab(self, course_id, listen=True, delay=1):
        """
        :listen 是否先行查看人數
        :delay 兩次請求之間的時間間格
        :用 Thread 實現
        """

        def _thread(arg):
            while True:
                if arg["listen"]:
                    if arg["cls"].is_availiabe(arg["course_id"]):
                        if arg["cls"].choose(course_id):
                            break
                else:
                    if arg["cls"].choose(course_id):
                        break

                sleep(arg["delay"])

        task = Thread(target=_thread, args=({'cls': self, 'course_id': course_id,
                                            'listen': listen, 'delay': delay}, ))
        self.task_list.append(task)
        task.start()

        # if listen:
        #     if self.is_availiabe(course_id):
        #         self.choose(course_id)
        # else:
        #     self.choose(course_id)

        # sleep(delay)
