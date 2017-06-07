import os
import sys
import time
import Queue
import traceback
import threading

from labmanager.rlms.caches import CacheDisabler

DEBUG = (os.environ.get('G4L_DEBUG') or '').lower() == 'true'

def dbg(msg):
    if DEBUG:
        print(msg)

class _QueueTaskProcessor(threading.Thread):
    def __init__(self, number, queue):
        threading.Thread.__init__(self)
        self.number = number
        self.setName("QueueProcessor-%s" % number)
        self.queue = queue
        self._current = None

    def run(self):
        cache_disabler = CacheDisabler()
        cache_disabler.disable()
        try:
            while True:
                try:
                    t = self.queue.get_nowait()
                except Queue.Empty:
                    break
                else:
                    self._current = t
                    try:
                        t.run()
                    except:
                        print("Error in task: %s" % t)
                        traceback.print_exc()
        finally:
            cache_disabler.reenable()
        self._current = None

        dbg("%s: finished" % self.name)

    def __repr__(self):
        return "_QueueTaskProcessor(number=%r, current=%r; alive=%r)" % (self.number, self._current, self.isAlive())

NUM_THREADS = 32
if os.environ.get('G4L_THREADS'):
    NUM_THREADS = int(os.environ['G4L_THREADS'])

def run_tasks(tasks, threads = NUM_THREADS):
    queue = Queue.Queue()
    for task in tasks:
        queue.put(task)
    
    task_processors = []
    for task_processor_number in range(threads):
        task_processor = _QueueTaskProcessor(task_processor_number, queue)
        task_processor.start()
        task_processors.append(task_processor)

    any_alive = True
    count = 0
    while any_alive:
        alive_threads = []
        for task_processor in task_processors:
            if task_processor.isAlive():
                alive_threads.append(task_processor)

        any_alive = len(alive_threads) > 0

        if any_alive:
            count = count + 1
            if count % 60 == 0:
                if len(alive_threads) > 5:
                    dbg("%s live processors" % len(alive_threads))
                    print("[%s] %s live processors" % (time.asctime(), len(alive_threads)))
                else:
                    dbg("%s live processors: %s" % (len(alive_threads), ', '.join([ repr(t) for t in alive_threads ])))
                    print("[%s] %s live processors: %s" % (time.asctime(), len(alive_threads), ', '.join([ repr(t) for t in alive_threads ])))
                sys.stdout.flush()

        try:
            time.sleep(1)
        except:
            # If there is an exception (such as keyboardinterrupt, or kill process..)
            for task in tasks:
                task.stop()

            # Delete everything in the queue (so the task stops) and re-raise the exception
            while True:
                try:
                    queue.get_nowait()
                except Queue.Empty:
                    break
            raise

    dbg("All processes are over")


class QueueTask(object):
    RLMS_CLASS = None # TO BE OVERRIDED
    RLMS_CONFIG = "{}"
    USERNAME = 'tester'

    def __init__(self, laboratory_id, language = 'en'):
        self.laboratory_id = laboratory_id
        self.language = language
        self.stopping = False

    def __repr__(self):
        return '_QueueTask(laboratory_id=%r, language=%r, stopping=%r)' % (self.laboratory_id, self.language, self.stopping)

    def stop(self):
        self.stopping = True

    def run(self):
        if self.stopping:
            return

        rlms = self.RLMS_CLASS(self.RLMS_CONFIG)
        dbg(' - %s: %s lang: %s' % (threading.current_thread().name, self.laboratory_id, self.language))
        rlms.reserve(self.laboratory_id, self.USERNAME, 'foo', '', '', '', '', locale = self.language)

