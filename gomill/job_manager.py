"""Job system supporting multiprocessing."""

import sys

from gomill import compact_tracebacks

multiprocessing = None

NoJobAvailable = object()

class JobFailed(StandardError):
    """Error reported by a job."""

class JobSourceError(StandardError):
    """Error from a job source object."""

class JobError(object):
    """Error from a job."""
    def __init__(self, job, msg):
        self.job = job
        self.msg = msg

def _initialise_multiprocessing():
    global multiprocessing
    if multiprocessing is not None:
        return
    try:
        import multiprocessing
    except ImportError:
        multiprocessing = None

class Worker_finish_signal(object):
    pass
worker_finish_signal = Worker_finish_signal()

def worker_run_jobs(job_queue, response_queue, worker_id):
    try:
        #pid = os.getpid()
        #sys.stderr.write("worker %d starting\n" % pid)
        while True:
            job = job_queue.get()
            #sys.stderr.write("worker %d: %s\n" % (pid, repr(job)))
            if isinstance(job, Worker_finish_signal):
                break
            try:
                response = job.run(worker_id)
            except JobFailed, e:
                response = JobError(job, str(e))
                sys.exc_clear()
                del e
            except Exception:
                response = JobError(
                    job, compact_tracebacks.format_traceback(skip=1))
                sys.exc_clear()
            response_queue.put(response)
        #sys.stderr.write("worker %d finishing\n" % pid)
        response_queue.cancel_join_thread()
    # Unfortunately, there will be places in the child that this doesn't cover.
    # But it will avoid the ugly traceback in most cases.
    except KeyboardInterrupt:
        sys.exit(3)

class Job_manager(object):
    def __init__(self):
        self.passed_exceptions = []

    def pass_exception(self, cls):
        self.passed_exceptions.append(cls)

class Multiprocessing_job_manager(Job_manager):
    def __init__(self, number_of_workers):
        Job_manager.__init__(self)
        _initialise_multiprocessing()
        if multiprocessing is None:
            raise StandardError("multiprocessing not available")
        if not 1 <= number_of_workers < 1024:
            raise ValueError
        self.number_of_workers = number_of_workers

    def start_workers(self):
        self.job_queue = multiprocessing.Queue()
        self.response_queue = multiprocessing.Queue()
        self.workers = []
        for i in range(self.number_of_workers):
            worker = multiprocessing.Process(
                target=worker_run_jobs,
                args=(self.job_queue, self.response_queue, i))
            self.workers.append(worker)
        for worker in self.workers:
            worker.start()

    def run_jobs(self, job_source):
        active_jobs = 0
        while True:
            if active_jobs < self.number_of_workers:
                try:
                    job = job_source.get_job()
                except Exception, e:
                    for cls in self.passed_exceptions:
                        if isinstance(e, cls):
                            raise
                    raise JobSourceError(
                        "error from get_job()\n%s" %
                        compact_tracebacks.format_traceback(skip=1))
                if job is not NoJobAvailable:
                    #sys.stderr.write("MGR: sending %s\n" % repr(job))
                    self.job_queue.put(job)
                    active_jobs += 1
                    continue
            if active_jobs == 0:
                break

            response = self.response_queue.get()
            if isinstance(response, JobError):
                try:
                    job_source.process_error_response(
                        response.job, response.msg)
                except Exception, e:
                    for cls in self.passed_exceptions:
                        if isinstance(e, cls):
                            raise
                    raise JobSourceError(
                        "error from process_error_response()\n%s" %
                        compact_tracebacks.format_traceback(skip=1))
            else:
                try:
                    job_source.process_response(response)
                except Exception, e:
                    for cls in self.passed_exceptions:
                        if isinstance(e, cls):
                            raise
                    raise JobSourceError(
                        "error from process_response()\n%s" %
                        compact_tracebacks.format_traceback(skip=1))
            active_jobs -= 1
            #sys.stderr.write("MGR: received response %s\n" % repr(response))

    def finish(self):
        for _ in range(self.number_of_workers):
            self.job_queue.put(worker_finish_signal)
        for worker in self.workers:
            worker.join()
        self.job_queue = None
        self.response_queue = None

class In_process_job_manager(Job_manager):
    def start_workers(self):
        pass

    def run_jobs(self, job_source):
        while True:
            try:
                job = job_source.get_job()
            except Exception, e:
                for cls in self.passed_exceptions:
                    if isinstance(e, cls):
                        raise
                raise JobSourceError(
                    "error from get_job()\n%s" %
                    compact_tracebacks.format_traceback(skip=1))
            if job is NoJobAvailable:
                break
            try:
                response = job.run(None)
            except Exception, e:
                if isinstance(e, JobFailed):
                    msg = str(e)
                else:
                    msg = compact_tracebacks.format_traceback(skip=1)
                try:
                    job_source.process_error_response(job, msg)
                except Exception, e:
                    for cls in self.passed_exceptions:
                        if isinstance(e, cls):
                            raise
                    raise JobSourceError(
                        "error from process_error_response()\n%s" %
                        compact_tracebacks.format_traceback(skip=1))
            else:
                try:
                    job_source.process_response(response)
                except Exception, e:
                    for cls in self.passed_exceptions:
                        if isinstance(e, cls):
                            raise
                    raise JobSourceError(
                        "error from process_response()\n%s" %
                        compact_tracebacks.format_traceback(skip=1))

    def finish(self):
        pass

def run_jobs(job_source, max_workers=None, allow_mp=True,
             passed_exceptions=None):
    if allow_mp:
        _initialise_multiprocessing()
        if multiprocessing is None:
            allow_mp = False
    if allow_mp:
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        job_manager = Multiprocessing_job_manager(max_workers)
    else:
        job_manager = In_process_job_manager()
    if passed_exceptions:
        for cls in passed_exceptions:
            job_manager.pass_exception(cls)
    job_manager.start_workers()
    try:
        job_manager.run_jobs(job_source)
    except Exception:
        try:
            job_manager.finish()
        except Exception, e2:
            print >>sys.stderr, "Error closing down workers:\n%s" % e2
        raise
    job_manager.finish()

