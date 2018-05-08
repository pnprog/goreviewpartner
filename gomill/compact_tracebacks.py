"""Compact formatting of tracebacks."""

import sys
import traceback

def log_traceback_from_info(exception_type, value, tb, dst=sys.stderr, skip=0):
    """Log a given exception nicely to 'dst', showing a traceback.

    dst  -- writeable file-like object
    skip -- number of traceback entries to omit from the top of the list

    """
    for line in traceback.format_exception_only(exception_type, value):
        dst.write(line)
    if (not isinstance(exception_type, str) and
        issubclass(exception_type, SyntaxError)):
        return
    print >>dst, 'traceback (most recent call last):'
    text = None
    for filename, lineno, fnname, text in traceback.extract_tb(tb)[skip:]:
        if fnname == "?":
            fn_s = "<global scope>"
        else:
            fn_s = "(%s)" % fnname
        print >>dst, "  %s:%s %s" % (filename, lineno, fn_s)
    if text is not None:
        print >>dst, "failing line:"
        print >>dst, text

def format_traceback_from_info(exception_type, value, tb, skip=0):
    """Return a description of a given exception as a string.

    skip -- number of traceback entries to omit from the top of the list

    """
    from cStringIO import StringIO
    log = StringIO()
    log_traceback_from_info(exception_type, value, tb, log, skip)
    return log.getvalue()

def log_traceback(dst=sys.stderr, skip=0):
    """Log the current exception nicely to 'dst'.

    dst  -- writeable file-like object
    skip -- number of traceback entries to omit from the top of the list

    """
    exception_type, value, tb = sys.exc_info()
    log_traceback_from_info(exception_type, value, tb, dst, skip)

def format_traceback(skip=0):
    """Return a description of the current exception as a string.

    skip -- number of traceback entries to omit from the top of the list

    """
    exception_type, value, tb = sys.exc_info()
    return format_traceback_from_info(exception_type, value, tb, skip)


def log_error_and_line_from_info(exception_type, value, tb, dst=sys.stderr):
    """Log a given exception briefly to 'dst', showing line number."""
    if (not isinstance(exception_type, str) and
        issubclass(exception_type, SyntaxError)):
        for line in traceback.format_exception_only(exception_type, value):
            dst.write(line)
    else:
        try:
            filename, lineno, fnname, text = traceback.extract_tb(tb)[-1]
        except IndexError:
            pass
        else:
            print >>dst, "at line %s:" % lineno
        for line in traceback.format_exception_only(exception_type, value):
            dst.write(line)

def format_error_and_line_from_info(exception_type, value, tb):
    """Return a brief description of a given exception as a string."""
    from cStringIO import StringIO
    log = StringIO()
    log_error_and_line_from_info(exception_type, value, tb, log)
    return log.getvalue()

def log_error_and_line(dst=sys.stderr):
    """Log the current exception briefly to 'dst'.

    dst  -- writeable file-like object

    """
    exception_type, value, tb = sys.exc_info()
    log_error_and_line_from_info(exception_type, value, tb, dst)

def format_error_and_line():
    """Return a brief description of the current exception as a string."""
    exception_type, value, tb = sys.exc_info()
    return format_error_and_line_from_info(exception_type, value, tb)

