import contextlib
import os
import subprocess

from python2.client.client import Py2Client


class Python2:
    """
    Object representing a Python 2 session.

    Initializing a `Python2` object spawns a Python 2 subprocess.  To terminate
    the subprocess, use the `Python2.shutdown()` method.  A `Python2` object
    may be used as a context manager to automatically shut down the session
    when the context is exited.
    """

    def __init__(self, executable='python',
                 logging_basic=None, logging_dict=None):
        """
        Initialize a Python2 instance.

        :param executable: Python 2 executable to use (default `'python'`).
        :param logging_basic: Keyword args to pass to `logging.basicConfig()`
            in the Python 2 process.
        :param logging_dict: Dict to pass to `logging.dictConfig()` in the
            Python 2 process.
        """
        if logging_dict is not None:
            logging_args = ['--logging-dict', repr(logging_dict)]
        elif logging_basic is not None:
            logging_args = ['--logging-basic', repr(logging_basic)]
        else:
            logging_args = []

        with contextlib.ExitStack() as stack:
            # Create two pipes for communication with the Python 2 server.
            # We need to close the server end of each pipe after spawning the
            # subprocess.  We only need to close the client end if an
            # exception is raised during initialization.

            cread, swrite = os.pipe()
            stack.callback(os.close, swrite)

            fcread = _try_fdopen(cread, 'rb')
            stack.push(_on_error(fcread.close))

            sread, cwrite = os.pipe()
            stack.callback(os.close, sread)

            fcwrite = _try_fdopen(cwrite, 'wb')
            stack.push(_on_error(fcwrite.close))

            self._proc = subprocess.Popen(
                [executable, '-m', 'python2.server',
                 '--in', str(sread), '--out', str(swrite)] + logging_args,
                pass_fds=(sread, swrite),
                start_new_session=True,  # Avoid signal issues
                universal_newlines=False)

            stack.push(_on_error(_kill, self._proc))

            self._client = Py2Client(fcread, fcwrite)

    def ping(self):
        """ Send a test message to the Python 2 process. """
        return self._client.do_command('ping')

    def project(self, obj):
        """ Project an object into Python 2. """
        return self._client.do_command('project', obj)

    def lift(self, obj):
        """ Lift an object from Python 2 to a native Python 3 object. """
        return self._client.do_command('lift', obj)

    def deeplift(self, obj):
        """ Recursively lift an object from Python 2 to 3. """
        return self._client.do_command('deeplift', obj)

    def exec(self, code, scope={}):
        """ Execute code in Python 2 in the given scope. """
        return self._client.do_command('exec', code, scope)

    def __getattr__(self, name):
        """ Access Python 2 builtins. """
        # True/False/None are keywords in Python 3
        name_ = name[:-1] if name in ('None_', 'True_', 'False_') else name
        result = self._client.do_command('builtin', name_)
        setattr(self, name, result)  # Remember builtins after first lookup
        return result

    def shutdown(self):
        """ Shut down the Python 2 process and end the session. """
        try:
            self._client.close()
        except Exception:
            pass

        try:
            self._proc.wait(timeout=1)
        except Exception:
            _kill(self._proc)

    def __enter__(self):
        """ Enter a Python 2 session context. """
        return self

    def __exit__(self, *exc_info):
        """ Shut down the Python 2 session. """
        self.shutdown()


def _on_error(fn, *args, **kwargs):
    """ Return a context exit function that invokes a callback on error. """
    def __exit__(exc_type, exc_value, traceback):
        if exc_type is not None:
            fn(*args, **kwargs)

    return __exit__


def _try_fdopen(fd, *args, **kwargs):
    """
    Safely attempt to convert a file descriptor to a file object.

    On success, returns a file object wrapping the file descriptor.  On
    failure, closes the file descriptor and raises an exception.
    """
    try:
        return os.fdopen(fd, *args, **kwargs)
    except Exception:
        os.close(fd)
        raise


def _kill(proc):
    """ Force-kill a process and wait for it to exit. """
    try:
        proc.kill()
    finally:
        proc.wait()
