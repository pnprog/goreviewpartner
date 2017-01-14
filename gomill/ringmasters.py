"""Run competitions using GTP."""

from __future__ import division, with_statement

import cPickle as pickle
import datetime
import errno
import os
import re
import shutil
import sys

try:
    import fcntl
except ImportError:
    fcntl = None

from gomill import compact_tracebacks
from gomill import game_jobs
from gomill import job_manager
from gomill import ringmaster_presenters
from gomill import terminal_input
from gomill.settings import *
from gomill.competitions import (
    NoGameAvailable, CompetitionError, ControlFileError)

def interpret_python(source, provided_globals, display_filename):
    """Interpret Python code from a unicode string.

    source           -- unicode object
    provided_globals -- dict
    display_filename -- filename to use in exceptions

    The string is executed with a copy of provided_globals as the global and
    local namespace. Returns that namespace.

    The source string must not have an encoding declaration (SyntaxError will be
    raised if it does).

    Propagates exceptions.

    """
    result = provided_globals.copy()
    code = compile(source, display_filename, 'exec',
                   division.compiler_flag, True)
    exec code in result
    return result

class RingmasterError(StandardError):
    """Error reported by a Ringmaster."""

class RingmasterInternalError(StandardError):
    """Error reported by a Ringmaster which indicates a bug."""


class Ringmaster(object):
    """Manage a competition as described by a control file.

    Most methods can raise RingmasterError.

    Instantiate with the pathname of the control file. The control file is read
    and interpreted at instantiation time (and errors are reported at that
    point).

    Ringmaster objects are used as a job source for the job manager.

    """
    # Can bump this to prevent people loading incompatible .status files.
    status_format_version = 0

    # For --version command
    public_version = "gomill ringmaster v0.7.4"

    def __init__(self, control_pathname):
        """Instantiate and initialise a Ringmaster.

        Reads the control file.

        Creates the Competition and initialises it from the control file.

        """
        self.display_mode = 'clearing'
        self.worker_count = None
        self.max_games_this_run = None
        self.presenter = None
        self.terminal_reader = None
        self.stopping = False
        self.stopping_reason = None
        # Map game_id -> int
        self.game_error_counts = {}
        self.write_gtp_logs = False

        self.control_pathname = control_pathname
        self.base_directory, control_filename = os.path.split(control_pathname)
        self.competition_code, ext = os.path.splitext(control_filename)
        if ext in (".log", ".status", ".cmd", ".hist",
                   ".report", ".games", ".void", ".gtplogs"):
            raise RingmasterError("forbidden control file extension: %s" % ext)
        stem = os.path.join(self.base_directory, self.competition_code)
        self.log_pathname = stem + ".log"
        self.status_pathname = stem + ".status"
        self.command_pathname = stem + ".cmd"
        self.history_pathname = stem + ".hist"
        self.report_pathname = stem + ".report"
        self.sgf_dir_pathname = stem + ".games"
        self.void_dir_pathname = stem + ".void"
        self.gtplog_dir_pathname = stem + ".gtplogs"

        self.status_is_loaded = False
        try:
            self._load_control_file()
        except ControlFileError, e:
            raise RingmasterError("error in control file:\n%s" % e)


    def _read_control_file(self):
        """Return the contents of the control file as an 8-bit string."""
        try:
            with open(self.control_pathname) as f:
                return f.read()
        except EnvironmentError, e:
            raise RingmasterError("failed to read control file:\n%s" % e)

    def _load_control_file(self):
        """Main implementation for __init__."""

        control_s = self._read_control_file()

        try:
            self.competition_type = self._parse_competition_type(control_s)
        except ValueError, e:
            raise ControlFileError("can't find competition_type")

        try:
            competition_class = self._get_competition_class(
                self.competition_type)
        except ValueError:
            raise ControlFileError(
                "unknown competition type: %s" % self.competition_type)
        self.competition = competition_class(self.competition_code)
        self.competition.set_base_directory(self.base_directory)

        try:
            control_u = control_s.decode("utf-8")
        except UnicodeDecodeError:
            raise ControlFileError("file is not encoded in utf-8")

        try:
            config = interpret_python(
                control_u, self.competition.control_file_globals(),
                display_filename=self.control_pathname)
        except KeyboardInterrupt:
            raise
        except ControlFileError, e:
            raise
        except:
            raise ControlFileError(compact_tracebacks.format_error_and_line())

        if config.get("competition_type") != self.competition_type:
            raise ControlFileError("competition_type improperly specified")

        try:
            self._initialise_from_control_file(config)
        except ControlFileError:
            raise
        except Exception, e:
            raise RingmasterError("unhandled error in control file:\n%s" %
                                  compact_tracebacks.format_traceback(skip=1))

        try:
            self.competition.initialise_from_control_file(config)
        except ControlFileError:
            raise
        except Exception, e:
            raise RingmasterError("unhandled error in control file:\n%s" %
                                  compact_tracebacks.format_traceback(skip=1))

    @staticmethod
    def _parse_competition_type(source):
        """Find the compitition_type definition in the control file.

        source -- string

        Requires the competition_type line to be the first non-comment line, and
        to be a simple assignment of a string literal.

        Raises ValueError if it can't find the competition_type line, or if the
        value isn't 'identifier-like'.

        """
        for line in source.split("\n"):
            s = line.lstrip()
            if not s or s.startswith("#"):
                continue
            break
        else:
            raise ValueError
        # May propagate ValueError
        m = re.match(r"competition_type\s*=\s*(['\"])([_a-zA-Z0-9]+)(['\"])$",
                     line)
        if not m:
            raise ValueError
        if m.group(1) != m.group(3):
            raise ValueError
        return m.group(2)


    @staticmethod
    def _get_competition_class(competition_type):
        """Find the competition class.

        competition_type -- string

        Returns a Competition subclass.

        Raises ValueError if the competition type is unknown.

        """
        if competition_type == "playoff":
            from gomill import playoffs
            return playoffs.Playoff
        elif competition_type == "allplayall":
            from gomill import allplayalls
            return allplayalls.Allplayall
        elif competition_type == "ce_tuner":
            from gomill import cem_tuners
            return cem_tuners.Cem_tuner
        elif competition_type == "mc_tuner":
            from gomill import mcts_tuners
            return mcts_tuners.Mcts_tuner
        else:
            raise ValueError

    def _open_files(self):
        """Open the log files and ensure that output directories exist.

        If flock is available, this takes out an exclusive lock on the log file.
        If this lock is unavailable, it raises RingmasterError.

        Also removes the command file if it exists.

        """
        try:
            self.logfile = open(self.log_pathname, "a")
        except EnvironmentError, e:
            raise RingmasterError("failed to open log file:\n%s" % e)

        if fcntl is not None:
            try:
                fcntl.flock(self.logfile, fcntl.LOCK_EX|fcntl.LOCK_NB)
            except IOError, e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    raise RingmasterError("competition is already running")
            except Exception:
                pass

        try:
            if os.path.exists(self.command_pathname):
                os.remove(self.command_pathname)
        except EnvironmentError, e:
            raise RingmasterError("error removing existing .cmd file:\n%s" % e)

        try:
            self.historyfile = open(self.history_pathname, "a")
        except EnvironmentError, e:
            raise RingmasterError("failed to open history file:\n%s" % e)

        if self.record_games:
            try:
                if not os.path.exists(self.sgf_dir_pathname):
                    os.mkdir(self.sgf_dir_pathname)
            except EnvironmentError:
                raise RingmasterError("failed to create SGF directory:\n%s" % e)

        if self.write_gtp_logs:
            try:
                if not os.path.exists(self.gtplog_dir_pathname):
                    os.mkdir(self.gtplog_dir_pathname)
            except EnvironmentError:
                raise RingmasterError(
                    "failed to create GTP log directory:\n%s" % e)

    def _close_files(self):
        """Close the log files."""
        try:
            self.logfile.close()
        except EnvironmentError, e:
            raise RingmasterError("error closing log file:\n%s" % e)
        try:
            self.historyfile.close()
        except EnvironmentError, e:
            raise RingmasterError("error closing history file:\n%s" % e)

    ringmaster_settings = [
        Setting('record_games', interpret_bool, True),
        Setting('stderr_to_log', interpret_bool, True),
        ]

    def _initialise_from_control_file(self, config):
        """Interpret the parts of the control file which belong to Ringmaster.

        Sets attributes from ringmaster_settings.

        """
        try:
            to_set = load_settings(self.ringmaster_settings, config)
        except ValueError, e:
            raise ControlFileError(str(e))
        for name, value in to_set.items():
            setattr(self, name, value)

    def enable_gtp_logging(self, b=True):
        self.write_gtp_logs = b

    def set_parallel_worker_count(self, n):
        self.worker_count = n

    def log(self, s):
        print >>self.logfile, s
        self.logfile.flush()

    def warn(self, s):
        """Log a message and say it on the 'warnings' channel."""
        self.log(s)
        self.presenter.say('warnings', s)

    def say(self, channel, s):
        """Say a message on the specified channel."""
        self.presenter.say(channel, s)

    def log_history(self, s):
        print >>self.historyfile, s
        self.historyfile.flush()

    _presenter_classes = {
        'clearing' : ringmaster_presenters.Clearing_presenter,
        'quiet'    : ringmaster_presenters.Quiet_presenter,
        }

    def set_display_mode(self, presenter_code):
        """Specify the presenter to use during run()."""
        if presenter_code not in self._presenter_classes:
            raise RingmasterError("unknown presenter type: %s" % presenter_code)
        self.display_mode = presenter_code

    def _initialise_presenter(self):
        self.presenter = self._presenter_classes[self.display_mode]()

    def _initialise_terminal_reader(self):
        self.terminal_reader = terminal_input.Terminal_reader()
        self.terminal_reader.initialise()

    def get_sgf_filename(self, game_id):
        """Return the sgf filename given a game id."""
        return "%s.sgf" % game_id

    def get_sgf_pathname(self, game_id):
        """Return the sgf pathname given a game id."""
        return os.path.join(self.sgf_dir_pathname,
                            self.get_sgf_filename(game_id))


    # State attributes (*: in persistent state):
    #  * void_game_count   -- int
    #  * comp              -- from Competition.get_status()
    #    games_in_progress -- dict game_id -> Game_job
    #    games_to_replay   -- dict game_id -> Game_job

    def _write_status(self, value):
        """Write the pickled contents of the persistent state file."""
        f = open(self.status_pathname + ".new", "wb")
        pickle.dump(value, f, protocol=-1)
        f.close()
        os.rename(self.status_pathname + ".new", self.status_pathname)

    def write_status(self):
        """Write the persistent state file."""
        competition_status = self.competition.get_status()
        status = {
            'void_game_count' : self.void_game_count,
            'comp_vn'         : self.competition.status_format_version,
            'comp'            : competition_status,
            }
        try:
            self._write_status((self.status_format_version, status))
        except EnvironmentError, e:
            raise RingmasterError("error writing persistent state:\n%s" % e)

    def _load_status(self):
        """Return the unpickled contents of the persistent state file."""
        with open(self.status_pathname, "rb") as f:
            return pickle.load(f)

    def load_status(self):
        """Read the persistent state file and load the state it contains."""
        try:
            status_format_version, status = self._load_status()
            if (status_format_version != self.status_format_version or
                status['comp_vn'] != self.competition.status_format_version):
                raise StandardError
            self.void_game_count = status['void_game_count']
            self.games_in_progress = {}
            self.games_to_replay = {}
            competition_status = status['comp']
        except pickle.UnpicklingError:
            raise RingmasterError("corrupt status file")
        except EnvironmentError, e:
            raise RingmasterError("error loading status file:\n%s" % e)
        except KeyError, e:
            raise RingmasterError("incompatible status file: missing %s" % e)
        except Exception, e:
            # Probably an exception from __setstate__ somewhere
            raise RingmasterError("incompatible status file")
        try:
            self.competition.set_status(competition_status)
        except CompetitionError, e:
            raise RingmasterError("error loading competition state: %s" % e)
        except KeyError, e:
            raise RingmasterError(
                "error loading competition state: missing %s" % e)
        except Exception, e:
            raise RingmasterError("error loading competition state:\n%s" %
                                  compact_tracebacks.format_traceback(skip=1))
        self.status_is_loaded = True

    def set_clean_status(self):
        """Reset persistent state to the initial values."""
        self.void_game_count = 0
        self.games_in_progress = {}
        self.games_to_replay = {}
        try:
            self.competition.set_clean_status()
        except CompetitionError, e:
            raise RingmasterError(e)
        self.status_is_loaded = True

    def status_file_exists(self):
        """Check whether the persistent state file exists."""
        return os.path.exists(self.status_pathname)

    def print_status(self):
        """Print the contents of the persistent state file, for debugging."""
        from pprint import pprint
        status_format_version, status = self._load_status()
        print "status_format_version:", status_format_version
        pprint(status)

    def write_command(self, command):
        """Write a command to the command file.

        command -- short string

        Overwrites the command file if it already exists.

        """
        # Short enough that I think we can get aw
        try:
            f = open(self.command_pathname, "w")
            f.write(command)
            f.close()
        except EnvironmentError, e:
            raise RingmasterError("error writing command file:\n%s" % e)

    def get_tournament_results(self):
        """Provide access to the tournament's results.

        Returns a Tournament_results object.

        Raises RingmasterError if the competition state isn't loaded, or if the
        competition isn't a tournament.

        """
        if not self.status_is_loaded:
            raise RingmasterError("status is not loaded")
        try:
            return self.competition.get_tournament_results()
        except NotImplementedError:
            raise RingmasterError("competition is not a tournament")

    def report(self):
        """Write the full competition report to the report file."""
        f = open(self.report_pathname, "w")
        self.competition.write_full_report(f)
        f.close()

    def print_status_report(self):
        """Write current competition status to standard output.

        This is for the 'show' command.

        """
        self.competition.write_short_report(sys.stdout)

    def _halt_competition(self, reason):
        """Make the competition stop submitting new games.

        reason -- message for the log and the status box.

        """
        self.stopping = True
        self.stopping_reason = reason
        self.log("halting competition: %s" % reason)

    def _update_display(self):
        """Redisplay the 'live' competition description.

        Does nothing in quiet mode.

        """
        if self.presenter.shows_warnings_only:
            return
        def p(s):
            self.say('status', s)
        self.presenter.clear('status')
        if self.stopping:
            if self.worker_count is None or not self.games_in_progress:
                p("halting: %s" % self.stopping_reason)
            else:
                p("waiting for workers to finish: %s" %
                  self.stopping_reason)
        if self.games_in_progress:
            if self.worker_count is None:
                gms = "game"
            else:
                gms = "%d games" % len(self.games_in_progress)
            p("%s in progress: %s" %
              (gms, " ".join(sorted(self.games_in_progress))))
        if not self.stopping:
            if self.max_games_this_run is not None:
                p("will start at most %d more games in this run" %
                  self.max_games_this_run)
            if self.terminal_reader.is_enabled():
                p("(Ctrl-X to halt gracefully)")

        self.presenter.clear('screen_report')
        sr = self.presenter.get_stream('screen_report')
        if self.void_game_count > 0:
            print >>sr, "%d void games; see log file." % self.void_game_count
        self.competition.write_screen_report(sr)
        sr.close()

        self.presenter.refresh()

    def _prepare_job(self, job):
        """Finish off a Game_job provided by the Competition.

        job -- incomplete Game_job, as returned by Competition.get_game()

        """
        job.sgf_game_name = "%s %s" % (self.competition_code, job.game_id)
        if self.record_games:
            job.sgf_filename = self.get_sgf_filename(job.game_id)
            job.sgf_dirname = self.sgf_dir_pathname
            job.void_sgf_dirname = self.void_dir_pathname
        if self.write_gtp_logs:
            job.gtp_log_pathname = os.path.join(
                    self.gtplog_dir_pathname, "%s.log" % job.game_id)
        if self.stderr_to_log:
            job.stderr_pathname = self.log_pathname

    def get_job(self):
        """Job supply function for the job manager."""
        job = self._get_job()
        self._update_display()
        return job

    def _get_job(self):
        """Main implementation of get_job()."""

        if self.stopping:
            return job_manager.NoJobAvailable

        if self.terminal_reader.stop_was_requested():
            self._halt_competition("stop instruction received from terminal")
            if self.presenter.shows_warnings_only:
                self.terminal_reader.acknowledge()
            return job_manager.NoJobAvailable

        try:
            if os.path.exists(self.command_pathname):
                command = open(self.command_pathname).read()
                if command == "stop":
                    self._halt_competition("stop command received")
                    try:
                        os.remove(self.command_pathname)
                    except EnvironmentError, e:
                        self.warn("error removing .cmd file:\n%s" % e)
                    return job_manager.NoJobAvailable
        except EnvironmentError, e:
            self.warn("error reading .cmd file:\n%s" % e)
        if self.max_games_this_run is not None:
            if self.max_games_this_run == 0:
                self._halt_competition("max-games reached for this run")
                return job_manager.NoJobAvailable
            self.max_games_this_run -= 1

        if self.games_to_replay:
            _, job = self.games_to_replay.popitem()
        else:
            job = self.competition.get_game()
            if job is NoGameAvailable:
                return job_manager.NoJobAvailable
            if job.game_id in self.games_in_progress:
                raise RingmasterInternalError(
                    "duplicate game id: %s" % job.game_id)
            self._prepare_job(job)
        self.games_in_progress[job.game_id] = job
        start_msg = "starting game %s: %s (b) vs %s (w)" % (
            job.game_id, job.player_b.code, job.player_w.code)
        self.log(start_msg)

        return job

    def process_response(self, response):
        """Job response function for the job manager."""
        # We log before processing the result, in case there's an error from the
        # competition code.
        self.log("response from game %s" % response.game_id)
        for warning in response.warnings:
            self.warn(warning)
        for log_entry in response.log_entries:
            self.log(log_entry)
        result_description = self.competition.process_game_result(response)
        del self.games_in_progress[response.game_id]
        self.write_status()
        if result_description is None:
            result_description = response.game_result.describe()
        self.say('results', "game %s: %s" % (
            response.game_id, result_description))

    def process_error_response(self, job, message):
        """Job error response function for the job manager."""
        self.warn("game %s -- %s" % (
            job.game_id, message))
        self.void_game_count += 1
        previous_error_count = self.game_error_counts.get(job.game_id, 0)
        stop_competition, retry_game = \
            self.competition.process_game_error(job, previous_error_count)
        if retry_game and not stop_competition:
            self.games_to_replay[job.game_id] = \
                self.games_in_progress.pop(job.game_id)
            self.game_error_counts[job.game_id] = previous_error_count + 1
        else:
            del self.games_in_progress[job.game_id]
            if previous_error_count != 0:
                del self.game_error_counts[job.game_id]
        self.write_status()
        if stop_competition and not self.stopping:
            # No need to log: _halt competition will do so
            self.say('warnings', "halting run due to void games")
            self._halt_competition("too many void games")

    def run(self, max_games=None):
        """Run the competition.

        max_games -- int or None (maximum games to start in this run)

        Returns when max_games have been played in this run, when the
        Competition is over, or when a 'stop' command is received via the
        command file.

        """
        def now():
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        def log_games_in_progress():
            try:
                msg = "games in progress were: %s" % (
                    " ".join(sorted(self.games_in_progress)))
            except Exception:
                pass
            self.log(msg)

        self._open_files()
        self.competition.set_event_logger(self.log)
        self.competition.set_history_logger(self.log_history)

        self._initialise_presenter()
        self._initialise_terminal_reader()

        allow_mp = (self.worker_count is not None)
        self.log("run started at %s with max_games %s" % (now(), max_games))
        if allow_mp:
            self.log("using %d worker processes" % self.worker_count)
        self.max_games_this_run = max_games
        self._update_display()
        try:
            job_manager.run_jobs(
                job_source=self,
                allow_mp=allow_mp, max_workers=self.worker_count,
                passed_exceptions=[RingmasterError, CompetitionError,
                                   RingmasterInternalError])
        except KeyboardInterrupt:
            self.log("run interrupted at %s" % now())
            log_games_in_progress()
            raise
        except (RingmasterError, CompetitionError), e:
            self.log("run finished with error at %s\n%s" % (now(), e))
            log_games_in_progress()
            raise RingmasterError(e)
        except (job_manager.JobSourceError, RingmasterInternalError), e:
            self.log("run finished with internal error at %s\n%s" % (now(), e))
            log_games_in_progress()
            raise RingmasterInternalError(e)
        except:
            self.log("run finished with internal error at %s" % now())
            self.log(compact_tracebacks.format_traceback())
            log_games_in_progress()
            raise
        self.log("run finished at %s" % now())
        self._close_files()

    def delete_state_and_output(self):
        """Delete all files generated by this competition.

        Deletes the persistent state file, game records, log files, and reports.

        """
        for pathname in [
            self.log_pathname,
            self.status_pathname,
            self.command_pathname,
            self.history_pathname,
            self.report_pathname,
            ]:
            if os.path.exists(pathname):
                try:
                    os.remove(pathname)
                except EnvironmentError, e:
                    print >>sys.stderr, e
        for pathname in [
            self.sgf_dir_pathname,
            self.void_dir_pathname,
            self.gtplog_dir_pathname,
            ]:
            if os.path.exists(pathname):
                try:
                    shutil.rmtree(pathname)
                except EnvironmentError, e:
                    print >>sys.stderr, e

    def check_players(self, discard_stderr=False):
        """Check that the engines required for the competition will run.

        If an engine fails, prints a description of the problem and returns
        False without continuing to check.

        Otherwise returns True.

        """
        try:
            to_check = self.competition.get_player_checks()
        except CompetitionError, e:
            raise RingmasterError(e)
        for check in to_check:
            if not discard_stderr:
                print "checking player %s" % check.player.code
            try:
                msgs = game_jobs.check_player(check, discard_stderr)
            except game_jobs.CheckFailed, e:
                print "player %s failed startup check:\n%s" % (
                    check.player.code, e)
                return False
            else:
                if not discard_stderr:
                    for msg in msgs:
                        print msg
        return True

