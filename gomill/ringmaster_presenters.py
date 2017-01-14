"""Live display for ringmasters."""

import os
import subprocess
import sys
from cStringIO import StringIO


class Presenter(object):
    """Abstract base class for presenters.

    This accepts messages on four _channels_, with codes
      warnings
      status
      screen_report
      results

    Warnings are always displayed immediately.

    Some presenters will delay display of other channels until refresh() is
    called; some will display them immediately.

    """

    # If this is true, ringmaster needn't bother doing the work to prepare most
    # of the display.
    shows_warnings_only = False

    def clear(self, channel):
        """Clear the contents of the specified channel."""
        raise NotImplementedError

    def say(self, channel, s):
        """Add a message to the specified channel.

        channel -- channel code
        s       -- string to display (no trailing newline)

        """
        raise NotImplementedError

    def refresh(self):
        """Re-render the current screen.

        This typically displays the full status and screen_report, and the most
        recent warnings and results.

        """
        raise NotImplementedError

    def get_stream(self, channel):
        """Return a file-like object wired up to the specified channel.

        When the object is closed, the text written it is sent to the channel
        (except that any trailing newline is removed).

        """
        return _Channel_writer(self, channel)

class _Channel_writer(object):
    """Support for get_stream() implementation."""
    def __init__(self, parent, channel):
        self.parent = parent
        self.channel = channel
        self.stringio = StringIO()

    def write(self, s):
        self.stringio.write(s)

    def close(self):
        s = self.stringio.getvalue()
        if s.endswith("\n"):
            s = s[:-1]
        self.parent.say(self.channel, s)
        self.stringio.close()


class Quiet_presenter(Presenter):
    """Presenter which shows only warnings.

    Warnings go to stderr.

    """
    shows_warnings_only = True

    def clear(self, channel):
        pass

    def say(self, channel, s):
        if channel == 'warnings':
            print >>sys.stderr, s

    def refresh(self):
        pass


class Box(object):
    """Description of screen layout for the clearing presenter."""
    def __init__(self, name, heading, limit):
        self.name = name
        self.heading = heading
        self.limit = limit
        self.contents = []

    def layout(self):
        return "\n".join(self.contents[-self.limit:])

class Clearing_presenter(Presenter):
    """Low-tech full-screen presenter.

    This shows all channels.

    """
    shows_warnings_only = False

    # warnings has to be last, so we can add to it immediately
    box_specs = (
        ('status', None, 999),
        ('screen_report', None, 999),
        ('results', "Results", 6),
        ('warnings', "Warnings", 4),
        )

    def __init__(self):
        self.boxes = {}
        self.box_list = []
        for t in self.box_specs:
            box = Box(*t)
            self.boxes[box.name] = box
            self.box_list.append(box)
        self.clear_method = None

    def clear(self, channel):
        self.boxes[channel].contents = []

    def say(self, channel, s):
        self.boxes[channel].contents.append(s)
        # 'warnings' box heading might be missing, but never mind.
        if channel == 'warnings':
            print s

    def refresh(self):
        self.clear_screen()
        for box in self.box_list:
            if not box.contents:
                continue
            if box.heading:
                print "= %s = " % box.heading
            print box.layout()
            if box.name != 'warnings':
                print

    def screen_height(self):
        """Return the current terminal height, or best guess."""
        return os.environ.get("LINES", 80)

    def clear_screen(self):
        """Try to clear the terminal screen (if stdout is a terminal)."""
        if self.clear_method is None:
            try:
                isatty = os.isatty(sys.stdout.fileno())
            except Exception:
                isatty = False
            if isatty:
                self.clear_method = "clear"
            else:
                self.clear_method = "delimiter"

        if self.clear_method == "clear":
            try:
                retcode = subprocess.call("clear")
            except Exception:
                retcode = 1
            if retcode != 0:
                self.clear_method = "newlines"
        if self.clear_method == "newlines":
            print "\n" * (self.screen_height()+1)
        elif self.clear_method == "delimiter":
            print 78 * "-"

