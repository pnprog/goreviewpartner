"""Common code for all tournament types."""

from collections import defaultdict

from gomill import game_jobs
from gomill import competition_schedulers
from gomill import tournament_results
from gomill import competitions
from gomill.competitions import (
    Competition, NoGameAvailable, CompetitionError, ControlFileError)
from gomill.settings import *
from gomill.utils import format_percent

# These all appear as Matchup_description attributes
matchup_settings = competitions.game_settings + [
    Setting('alternating', interpret_bool, default=False),
    Setting('number_of_games', allow_none(interpret_int), default=None),
    ]


class Matchup(tournament_results.Matchup_description):
    """Internal description of a matchup from the configuration file.

    See tournament_results.Matchup_description for main public attributes.

    Additional attributes:
      event_description -- string to show as sgf event

    Instantiate with
      matchup_id -- identifier
      player_1   -- player code
      player_2   -- player code
      parameters -- dict matchup setting name -> value
      name       -- utf-8 string, or None
      event_code -- identifier

    If a matchup setting is missing from 'parameters', the setting's default
    value is used (or, if there is no default value, ValueError is raised).

    'event_code' is used for the sgf event description (combined with 'name'
    if available).

    Instantiation raises ControlFileError if the handicap settings aren't
    permitted.

    """
    def __init__(self, matchup_id, player_1, player_2, parameters,
                 name, event_code):
        self.id = matchup_id
        self.player_1 = player_1
        self.player_2 = player_2

        for setting in matchup_settings:
            try:
                v = parameters[setting.name]
            except KeyError:
                try:
                    v = setting.get_default()
                except KeyError:
                    raise ValueError("'%s' not specified" % setting.name)
            setattr(self, setting.name, v)

        competitions.validate_handicap(
            self.handicap, self.handicap_style, self.board_size)

        if name is None:
            name = "%s v %s" % (self.player_1, self.player_2)
            event_description = event_code
        else:
            event_description = "%s (%s)" % (event_code, name)
        self.name = name
        self.event_description = event_description
        self._game_id_template = ("%s_" +
            competitions.leading_zero_template(self.number_of_games))

    def make_game_id(self, game_number):
        return self._game_id_template % (self.id, game_number)


class Ghost_matchup(object):
    """Dummy Matchup object for matchups which have gone from the control file.

    This is used if the matchup appears in results.

    It has to be a good enough imitation to keep write_matchup_summary() happy.

    """
    def __init__(self, matchup_id, player_1, player_2):
        self.id = matchup_id
        self.player_1 = player_1
        self.player_2 = player_2
        self.name = "%s v %s" % (player_1, player_2)
        self.number_of_games = None

    def describe_details(self):
        return "?? (missing from control file)"


class Tournament(Competition):
    """A Competition based on a number of matchups.

    """
    def __init__(self, competition_code, **kwargs):
        Competition.__init__(self, competition_code, **kwargs)
        self.working_matchups = set()
        self.probationary_matchups = set()

    def make_matchup(self, matchup_id, player_1, player_2, parameters,
                     name=None):
        """Make a Matchup from the various parameters.

        Raises ControlFileError if any required parameters are missing.

        See Matchup.__init__ for details.

        """
        try:
            return Matchup(matchup_id, player_1, player_2, parameters, name,
                           event_code=self.competition_code)
        except ValueError, e:
            raise ControlFileError(str(e))


    # State attributes (*: in persistent state):
    #  *results               -- map matchup id -> list of Game_results
    #  *scheduler             -- Group_scheduler (group codes are matchup ids)
    #  *engine_names          -- map player code -> string
    #  *engine_descriptions   -- map player code -> string
    #   working_matchups      -- set of matchup ids
    #       (matchups which have successfully completed a game in this run)
    #   probationary_matchups -- set of matchup ids
    #       (matchups which failed to complete their last game)
    #   ghost_matchups        -- map matchup id -> Ghost_matchup
    #       (matchups which have been removed from the control file)

    def _check_results(self):
        """Check that the current results are consistent with the control file.

        This is run when reloading state.

        Raises CompetitionError if they're not.

        (In general, control file changes are permitted. The only thing we
        reject is results for a currently-defined matchup whose players aren't
        correct.)

        """
        # We guarantee that results for a given matchup always have consistent
        # players, so we need only check the first result.
        for matchup in self.matchup_list:
            results = self.results[matchup.id]
            if not results:
                continue
            result = results[0]
            seen_players = sorted(result.players.itervalues())
            expected_players = sorted((matchup.player_1, matchup.player_2))
            if seen_players != expected_players:
                raise CompetitionError(
                    "existing results for matchup %s "
                    "are inconsistent with control file:\n"
                    "result players are %s;\n"
                    "control file players are %s" %
                    (matchup.id,
                     ",".join(seen_players), ",".join(expected_players)))

    def _set_ghost_matchups(self):
        self.ghost_matchups = {}
        live = set(self.matchups)
        for matchup_id, results in self.results.iteritems():
            if matchup_id in live:
                continue
            result = results[0]
            # player_1 and player_2 might not be the right way round, but it
            # doesn't matter.
            self.ghost_matchups[matchup_id] = Ghost_matchup(
                matchup_id, result.player_b, result.player_w)

    def _set_scheduler_groups(self):
        self.scheduler.set_groups(
            [(m.id, m.number_of_games) for m in self.matchup_list] +
            [(id, 0) for id in self.ghost_matchups])

    def set_clean_status(self):
        self.results = defaultdict(list)
        self.engine_names = {}
        self.engine_descriptions = {}
        self.scheduler = competition_schedulers.Group_scheduler()
        self.ghost_matchups = {}
        self._set_scheduler_groups()

    def get_status(self):
        return {
            'results' : self.results,
            'scheduler' : self.scheduler,
            'engine_names' : self.engine_names,
            'engine_descriptions' : self.engine_descriptions,
            }

    def set_status(self, status):
        self.results = status['results']
        self._check_results()
        self._set_ghost_matchups()
        self.scheduler = status['scheduler']
        self._set_scheduler_groups()
        self.scheduler.rollback()
        self.engine_names = status['engine_names']
        self.engine_descriptions = status['engine_descriptions']


    def get_game(self):
        matchup_id, game_number = self.scheduler.issue()
        if matchup_id is None:
            return NoGameAvailable
        matchup = self.matchups[matchup_id]
        if matchup.alternating and (game_number % 2):
            player_b, player_w = matchup.player_2, matchup.player_1
        else:
            player_b, player_w = matchup.player_1, matchup.player_2
        game_id = matchup.make_game_id(game_number)

        job = game_jobs.Game_job()
        job.game_id = game_id
        job.game_data = (matchup_id, game_number)
        job.player_b = self.players[player_b]
        job.player_w = self.players[player_w]
        job.board_size = matchup.board_size
        job.komi = matchup.komi
        job.move_limit = matchup.move_limit
        job.handicap = matchup.handicap
        job.handicap_is_free = (matchup.handicap_style == 'free')
        job.use_internal_scorer = (matchup.scorer == 'internal')
        job.internal_scorer_handicap_compensation = \
            matchup.internal_scorer_handicap_compensation
        job.sgf_event = matchup.event_description
        return job

    def process_game_result(self, response):
        self.engine_names.update(response.engine_names)
        self.engine_descriptions.update(response.engine_descriptions)
        matchup_id, game_number = response.game_data
        game_id = response.game_id
        self.working_matchups.add(matchup_id)
        self.probationary_matchups.discard(matchup_id)
        self.scheduler.fix(matchup_id, game_number)
        self.results[matchup_id].append(response.game_result)
        self.log_history("%7s %s" % (game_id, response.game_result.describe()))

    def process_game_error(self, job, previous_error_count):
        # ignoring previous_error_count, as we can consider all jobs for the
        # same matchup to be equivalent.
        stop_competition = False
        retry_game = False
        matchup_id, game_data = job.game_data
        if (matchup_id not in self.working_matchups or
            matchup_id in self.probationary_matchups):
            stop_competition = True
        else:
            self.probationary_matchups.add(matchup_id)
            retry_game = True
        return stop_competition, retry_game

    def write_matchup_report(self, out, matchup, results):
        """Write the summary block for the specified matchup to 'out'

        results -- nonempty list of Game_results

        """
        # The control file might have changed since the results were recorded.
        # We are guaranteed that the player codes correspond, but nothing else.

        # We use the current matchup to describe 'background' information, as
        # that isn't available any other way, but we look to the results where
        # we can.

        ms = tournament_results.Matchup_stats(
            results, matchup.player_1, matchup.player_2)
        ms.calculate_colour_breakdown()
        ms.calculate_time_stats()
        tournament_results.write_matchup_summary(out, matchup, ms)

    def write_matchup_reports(self, out):
        """Write summary blocks for all live matchups to 'out'.

        This doesn't include ghost matchups, or matchups with no games.

        """
        first = True
        for matchup in self.matchup_list:
            results = self.results[matchup.id]
            if not results:
                continue
            if first:
                first = False
            else:
                print >>out
            self.write_matchup_report(out, matchup, results)

    def write_ghost_matchup_reports(self, out):
        """Write summary blocks for all ghost matchups to 'out'.

        (This may produce no output. Starts with a blank line otherwise.)

        """
        for matchup_id, matchup in sorted(self.ghost_matchups.iteritems()):
            print >>out
            results = self.results[matchup_id]
            self.write_matchup_report(out, matchup, results)

    def write_player_descriptions(self, out):
        """Write descriptions of all players to 'out'."""
        for code, description in sorted(self.engine_descriptions.items()):
            print >>out, ("player %s: %s" % (code, description))

    def get_tournament_results(self):
        return tournament_results.Tournament_results(
            self.matchup_list, self.results)

