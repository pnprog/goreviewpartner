"""Competitions for all-play-all tournaments."""

from gomill import ascii_tables
from gomill import game_jobs
from gomill import competitions
from gomill import tournaments
from gomill import tournament_results
from gomill.competitions import (
    Competition, CompetitionError, ControlFileError)
from gomill.settings import *
from gomill.utils import format_float


class Competitor_config(Quiet_config):
    """Competitor description for use in control files."""
    # positional or keyword
    positional_arguments = ('player',)
    # keyword-only
    keyword_arguments = ()

class Competitor_spec(object):
    """Internal description of a competitor spec from the configuration file.

    Public attributes:
      player      -- player code
      short_code  -- eg 'A' or 'ZZ'

    """


class Allplayall(tournaments.Tournament):
    """A Tournament with matchups for all pairs of competitors.

    The game ids are like AvB_2, where A and B are the competitor short_codes
    and 2 is the game number between those two competitors.

    This tournament type doesn't permit ghost matchups.

    """

    def control_file_globals(self):
        result = Competition.control_file_globals(self)
        result.update({
            'Competitor' : Competitor_config,
            })
        return result


    special_settings = [
        Setting('competitors',
                interpret_sequence_of_quiet_configs(
                    Competitor_config, allow_simple_values=True)),
        ]

    def competitor_spec_from_config(self, i, competitor_config):
        """Make a Competitor_spec from a Competitor_config.

        i -- ordinal number of the competitor.

        Raises ControlFileError if there is an error in the configuration.

        Returns a Competitor_spec with all attributes set.

        """
        arguments = competitor_config.resolve_arguments()
        cspec = Competitor_spec()

        if 'player' not in arguments:
            raise ValueError("player not specified")
        cspec.player = arguments['player']
        if cspec.player not in self.players:
            raise ControlFileError("unknown player")

        def let(n):
            return chr(ord('A') + n)
        if i < 26:
            cspec.short_code = let(i)
        elif i < 26*27:
            n, m = divmod(i, 26)
            cspec.short_code = let(n-1) + let(m)
        else:
            raise ValueError("too many competitors")
        return cspec

    @staticmethod
    def _get_matchup_id(c1, c2):
        return "%sv%s" % (c1.short_code, c2.short_code)

    def initialise_from_control_file(self, config):
        Competition.initialise_from_control_file(self, config)

        matchup_settings = [
            setting for setting in competitions.game_settings
            if setting.name not in ('handicap', 'handicap_style')
            ] + [
            Setting('rounds', allow_none(interpret_int), default=None),
            ]
        try:
            matchup_parameters = load_settings(matchup_settings, config)
        except ValueError, e:
            raise ControlFileError(str(e))
        matchup_parameters['alternating'] = True
        matchup_parameters['number_of_games'] = matchup_parameters.pop('rounds')

        try:
            specials = load_settings(self.special_settings, config)
        except ValueError, e:
            raise ControlFileError(str(e))

        if not specials['competitors']:
            raise ControlFileError("competitors: empty list")
        # list of Competitor_specs
        self.competitors = []
        seen_competitors = set()
        for i, competitor_spec in enumerate(specials['competitors']):
            try:
                cspec = self.competitor_spec_from_config(i, competitor_spec)
            except StandardError, e:
                code = competitor_spec.get_key()
                if code is None:
                    code = i
                raise ControlFileError("competitor %s: %s" % (code, e))
            if cspec.player in seen_competitors:
                raise ControlFileError("duplicate competitor: %s"
                                       % cspec.player)
            seen_competitors.add(cspec.player)
            self.competitors.append(cspec)

        # map matchup_id -> Matchup
        self.matchups = {}
        # Matchups in order of definition
        self.matchup_list = []
        for c1_i, c1 in enumerate(self.competitors):
            for c2 in self.competitors[c1_i+1:]:
                try:
                    m = self.make_matchup(
                        self._get_matchup_id(c1, c2),
                        c1.player, c2.player,
                        matchup_parameters)
                except StandardError, e:
                    raise ControlFileError("%s v %s: %s" %
                                           (c1.player, c2.player, e))
                self.matchups[m.id] = m
                self.matchup_list.append(m)


    # Can bump this to prevent people loading incompatible .status files.
    status_format_version = 1

    def get_status(self):
        result = tournaments.Tournament.get_status(self)
        result['competitors'] = [c.player for c in self.competitors]
        return result

    def set_status(self, status):
        seen_competitors = status['competitors']
        # This should mean that _check_results can never fail, but might as well
        # still let it run.
        if len(self.competitors) < len(seen_competitors):
            raise CompetitionError(
                "competitor has been removed from control file")
        if ([c.player for c in self.competitors[:len(seen_competitors)]] !=
            seen_competitors):
            raise CompetitionError(
                "competitors have changed in the control file")
        tournaments.Tournament.set_status(self, status)


    def get_player_checks(self):
        result = []
        matchup = self.matchup_list[0]
        for competitor in self.competitors:
            check = game_jobs.Player_check()
            check.player = self.players[competitor.player]
            check.board_size = matchup.board_size
            check.komi = matchup.komi
            result.append(check)
        return result


    def count_games_played(self):
        """Return the total number of games completed."""
        return sum(len(l) for l in self.results.values())

    def count_games_expected(self):
        """Return the total number of games required.

        Returns None if no limit has been set.

        """
        rounds = self.matchup_list[0].number_of_games
        if rounds is None:
            return None
        n = len(self.competitors)
        return rounds * n * (n-1) // 2

    def write_screen_report(self, out):
        expected = self.count_games_expected()
        if expected is not None:
            print >>out, "%d/%d games played" % (
                self.count_games_played(), expected)
        else:
            print >>out, "%d games played" % self.count_games_played()
        print >>out

        t = ascii_tables.Table(row_count=len(self.competitors))
        t.add_heading("") # player short_code
        i = t.add_column(align='left')
        t.set_column_values(i, (c.short_code for c in self.competitors))

        t.add_heading("") # player code
        i = t.add_column(align='left')
        t.set_column_values(i, (c.player for c in self.competitors))

        for c2_i, c2 in enumerate(self.competitors):
            t.add_heading(" " + c2.short_code)
            i = t.add_column(align='left')
            column_values = []
            for c1_i, c1 in enumerate(self.competitors):
                if c1_i == c2_i:
                    column_values.append("")
                    continue
                if c1_i < c2_i:
                    matchup_id = self._get_matchup_id(c1, c2)
                    matchup = self.matchups[matchup_id]
                    player_x = matchup.player_1
                    player_y = matchup.player_2
                else:
                    matchup_id = self._get_matchup_id(c2, c1)
                    matchup = self.matchups[matchup_id]
                    player_x = matchup.player_2
                    player_y = matchup.player_1
                ms = tournament_results.Matchup_stats(
                    self.results[matchup.id],
                    player_x, player_y)
                column_values.append(
                    "%s-%s" % (format_float(ms.wins_1),
                               format_float(ms.wins_2)))
            t.set_column_values(i, column_values)
        print >>out, "\n".join(t.render())

    def write_short_report(self, out):
        def p(s):
            print >>out, s
        p("allplayall: %s" % self.competition_code)
        if self.description:
            p(self.description)
        p('')
        self.write_screen_report(out)
        p('')
        self.write_matchup_reports(out)
        p('')
        self.write_player_descriptions(out)
        p('')

    write_full_report = write_short_report

