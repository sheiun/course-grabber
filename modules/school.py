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

    QUERY_URL = 'https://querycourse.ntust.edu.tw/QueryCourse/QueryCourseInfo'

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
        self.login_data = data
        data["code_box"] = self.verification_code
        data["Button1"] = "登入系統"
        data["__VIEWSTATE"] = NTUST.VIEW_STATE

        res = self.session.post(
            'https://stuinfo8.ntust.edu.tw/ntust_stu/stu.aspx', data=data)

        assert res.url == NTUST.MENU_URL

    def logout(self):
        return super().logout()

    def is_available(self, course_id):
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

    @staticmethod
    def is_available_by_query(course_id):
        data = requests.post(NTUST.QUERY_URL, data={'semester': '1072',
                                                    'course_no': course_id,
                                                    'course_name': '',
                                                    'course_teacher': '',
                                                    'nodes': 'M1,M2,M3,M4,M5,M6,M7,M8,M9,M=,MA,MB,MC,MD,T1,T2,T3,T4,T5,T6,T7,T8,T9,T=,TA,TB,TC,TD,W1,W2,W3,W4,W5,W6,W7,W8,W9,W=,WA,WB,WC,WD,R1,R2,R3,R4,R5,R6,R7,R8,R9,R=,RA,RB,RC,RD,F1,F2,F3,F4,F5,F6,F7,F8,F9,F=,FA,FB,FC,FD,S1,S2,S3,S4,S5,S6,S7,S8,S9,S=,SA,SB,SC,SD,U1,U2,U3,U4,U5,U6,U7,U8,U9,U=,UA,UB,UC,UD',
                                                    'dimension': '',
                                                    'course_notes': '',
                                                    'only_general': '0',
                                                    'only_ntust': '0'}).json()[0]
        return data["Restrict2"] > data["ChooseStudent"]

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
                print(f'{arg["course_id"]} is running...')
                if arg["listen"]:
                    if arg["cls"].is_available_by_query(arg["course_id"]):
                        self.login(self.login_data)
                        if arg["cls"].choose(arg["course_id"]):
                            break
                else:
                    if arg["cls"].choose(arg["course_id"]):
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
