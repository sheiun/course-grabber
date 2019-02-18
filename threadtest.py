from threading import Thread, Event


class GrabThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, course_id, listen=True, delay=1000):
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


t1 = GrabThread('M1')

t2 = GrabThread('M2')

t1.stop()
