"""Support for implementing proxy GTP engines.

That is, engines which implement some or all of their commands by sending them
on to another engine (the _back end_).

"""

from gomill import gtp_controller
from gomill import gtp_engine
from gomill.gtp_controller import (
    BadGtpResponse, GtpChannelError, GtpChannelClosed)
from gomill.gtp_engine import GtpError, GtpQuit, GtpFatalError


class BackEndError(StandardError):
    """Difficulty communicating with the back end.

    Public attributes:
      cause -- Exception instance of an underlying exception (or None)

    """
    def __init__(self, args, cause=None):
        StandardError.__init__(self, args)
        self.cause = cause

class Gtp_proxy(object):
    """Manager for a GTP proxy engine.

    Public attributes:
      engine     -- Gtp_engine_protocol
      controller -- Gtp_controller

    The 'engine' attribute is the proxy engine. Initially it supports all the
    commands reported by the back end's 'list_commands'. You can add commands to
    it in the usual way; new commands will override any commands with the same
    names in the back end.

    The proxy engine also supports the following commands:
      gomill-passthrough <command> [args] ...
        Run a command on the back end (use this to get at overridden commands,
        or commands which don't appear in list_commands)

    If the proxy subprocess exits, this will be reported (as a transport error)
    when the next command is sent. If you're using handle_command, it will
    apropriately turn this into a fatal error.

    Sample use:
      proxy = gtp_proxy.Gtp_proxy()
      proxy.set_back_end_subprocess([<command>, <arg>, ...])
      proxy.engine.add_command(...)
      try:
          proxy.run()
      except KeyboardInterrupt:
          sys.exit(1)

    The default 'quit' handler passes 'quit' on the back end and raises
    GtpQuit.

    If you add a handler which you expect to cause the back end to exit (eg, by
    sending it 'quit'), you should have call expect_back_end_exit() (and usually
    also raise GtpQuit).

    If you want to hide one of the underlying commands, or don't want one of the
    additional commands, just use engine.remove_command().

    """
    def __init__(self):
        self.controller = None
        self.engine = None

    def _back_end_is_set(self):
        return self.controller is not None

    def _make_back_end_handlers(self):
        result = {}
        for command in self.back_end_commands:
            def handler(args, _command=command):
                return self.handle_command(_command, args)
            result[command] = handler
        return result

    def _make_engine(self):
        self.engine = gtp_engine.Gtp_engine_protocol()
        self.engine.add_commands(self._make_back_end_handlers())
        self.engine.add_protocol_commands()
        self.engine.add_commands({
            'quit'               : self.handle_quit,
            'gomill-passthrough' : self.handle_passthrough,
            })

    def set_back_end_controller(self, controller):
        """Specify the back end using a Gtp_controller.

        controller -- Gtp_controller

        Raises BackEndError if it can't communicate with the back end.

        By convention, the controller's channel name should be "back end".

        """
        if self._back_end_is_set():
            raise StandardError("back end already set")
        self.controller = controller
        try:
            self.back_end_commands = controller.list_commands()
        except (GtpChannelError, BadGtpResponse), e:
            raise BackEndError(str(e), cause=e)
        self._make_engine()

    def set_back_end_subprocess(self, command, **kwargs):
        """Specify the back end as a subprocess.

        command -- list of strings (as for subprocess.Popen)

        Additional keyword arguments are passed to the Subprocess_gtp_channel
        constructor.

        Raises BackEndError if it can't communicate with the back end.

        """
        try:
            channel = gtp_controller.Subprocess_gtp_channel(command, **kwargs)
        except GtpChannelError, e:
            # Probably means exec failure
            raise BackEndError("can't launch back end command\n%s" % e, cause=e)
        controller = gtp_controller.Gtp_controller(channel, "back end")
        self.set_back_end_controller(controller)

    def close(self):
        """Close the channel to the back end.

        It's safe to call this at any time after set_back_end_... (including
        after receiving a BackEndError).

        It's not strictly necessary to call this if you're going to exit from
        the parent process anyway, as that will naturally close the command
        channel. But some engines don't behave well if you don't send 'quit',
        so it's safest to close the proxy explicitly.

        This will send 'quit' if low-level errors have not previously been seen
        on the channel, unless expect_back_end_exit() has been called.

        Errors (including failure responses to 'quit') are reported by raising
        BackEndError.

        """
        if self.controller is None:
            return
        self.controller.safe_close()
        late_errors = self.controller.retrieve_error_messages()
        if late_errors:
            raise BackEndError("\n".join(late_errors))

    def run(self):
        """Run a GTP session on stdin and stdout, using the proxy engine.

        This is provided for convenience; it's also ok to use the proxy engine
        directly.

        Returns either when EOF is seen on stdin, or when a handler (such as the
        default 'quit' handler) raises GtpQuit.

        Closes the channel to the back end before it returns. When it is
        meaningful (eg, for subprocess channels) this waits for the back end to
        exit.

        Propagates ControllerDisconnected if a pipe connected to stdout goes
        away.

        """
        gtp_engine.run_interactive_gtp_session(self.engine)
        self.close()

    def pass_command(self, command, args):
        """Pass a command to the back end, and return its response.

        The response (or failure response) is unchanged, except for whitespace
        normalisation.

        This passes the command to the back end even if it isn't included in the
        back end's list_commands output; the back end will presumably return an
        'unknown command' error.

        Failure responses from the back end are reported by raising
        BadGtpResponse.

        Low-level (ie, transport or protocol) errors are reported by raising
        BackEndError.

        """
        if not self._back_end_is_set():
            raise StandardError("back end isn't set")
        try:
            return self.controller.do_command(command, *args)
        except GtpChannelError, e:
            raise BackEndError(str(e), cause=e)

    def handle_command(self, command, args):
        """Run a command on the back end, from inside a GTP handler.

        This is a variant of pass_command, intended to be used directly in a
        command handler.

        Failure responses from the back end are reported by raising GtpError.

        Low-level (ie, transport or protocol) errors are reported by raising
        GtpFatalError.

        """
        try:
            return self.pass_command(command, args)
        except BadGtpResponse, e:
            raise GtpError(e.gtp_error_message)
        except BackEndError, e:
            raise GtpFatalError(str(e))

    def back_end_has_command(self, command):
        """Say whether the back end supports the specified command.

        This uses known_command, not list_commands. It caches the results.

        Low-level (ie, transport or protocol) errors are reported by raising
        BackEndError.

        """
        if not self._back_end_is_set():
            raise StandardError("back end isn't set")
        try:
            return self.controller.known_command(command)
        except GtpChannelError, e:
            raise BackEndError(str(e), cause=e)

    def expect_back_end_exit(self):
        """Mark that the back end is expected to have exited.

        Call this from any handler which you expect to cause the back end to
        exit (eg, by sending it 'quit').

        """
        self.controller.channel_is_bad = True

    def handle_quit(self, args):
        # Ignores GtpChannelClosed
        try:
            result = self.pass_command("quit", [])
        except BackEndError, e:
            if isinstance(e.cause, GtpChannelClosed):
                result = ""
            else:
                raise GtpFatalError(str(e))
        except BadGtpResponse, e:
            self.expect_back_end_exit()
            raise GtpFatalError(e.gtp_error_message)
        self.expect_back_end_exit()
        raise GtpQuit(result)

    def handle_passthrough(self, args):
        try:
            command = args[0]
        except IndexError:
            gtp_engine.report_bad_arguments()
        return self.handle_command(command, args[1:])
