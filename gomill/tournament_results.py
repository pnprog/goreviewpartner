"""Retrieving and reporting on tournament results."""

from __future__ import division

from gomill import ascii_tables
from gomill.utils import format_float, format_percent
from gomill.common import colour_name

class Matchup_description(object):
    """Description of a matchup (pairing of two players).

    Public attributes:
      id              -- matchup id (very short string)
      player_1        -- player code (identifier-like string)
      player_2        -- player code (identifier-like string)
      name            -- string (eg 'xxx v yyy')
      board_size      -- int
      komi            -- float
      alternating     -- bool
      handicap        -- int or None
      handicap_style  -- 'fixed' or 'free'
      move_limit      -- int
      scorer          -- 'internal' or 'players'
      number_of_games -- int or None

    If alternating is False, player_1 plays black and player_2 plays white;
    otherwise they alternate.

    player_1 and player_2 are always different.

    """
    def describe_details(self):
        """Return a text description of game settings.

        This covers the most important game settings which can't be observed
        in the results table (board size, handicap, and komi).

        """
        s = "board size: %s   " % self.board_size
        if self.handicap is not None:
            s += "handicap: %s (%s)   " % (
                self.handicap, self.handicap_style)
        s += "komi: %s" % self.komi
        return s


class Tournament_results(object):
    """Provide access to results of a single tournament.

    The tournament results are catalogued in terms of 'matchups', with each
    matchup corresponding to a series of games which have the same players and
    settings. Each matchup has an id, which is a short string.

    """
    def __init__(self, matchup_list, results):
        self.matchup_list = matchup_list
        self.results = results
        self.matchups = dict((m.id, m) for m in matchup_list)

    def get_matchup_ids(self):
        """Return a list of all matchup ids, in definition order."""
        return [m.id for m in self.matchup_list]

    def get_matchup(self, matchup_id):
        """Describe the matchup with the specified id.

        Returns a Matchup_description (which should be treated as read-only).

        """
        return self.matchups[matchup_id]

    def get_matchups(self):
        """Return a map matchup id -> Matchup_description."""
        return self.matchups.copy()

    def get_matchup_results(self, matchup_id):
        """Return the results for the specified matchup.

        Returns a list of gtp_games.Game_results (in unspecified order).

        The Game_results all have game_id set.

        """
        return self.results[matchup_id][:]

    def get_matchup_stats(self, matchup_id):
        """Return statistics for the specified matchup.

        Returns a Matchup_stats object.

        """
        matchup = self.matchups[matchup_id]
        ms = Matchup_stats(self.results[matchup_id],
                           matchup.player_1, matchup.player_2)
        ms.calculate_colour_breakdown()
        ms.calculate_time_stats()
        return ms


class Matchup_stats(object):
    """Result statistics for games between a pair of players.

    Instantiate with
      results  -- list of gtp_games.Game_results
      player_1 -- player code
      player_2 -- player code
    The game results should all be for games between player_1 and player_2.

    Public attributes:
      player_1    -- player code
      player_2    -- player code
      total       -- int (number of games)
      wins_1      -- float (score)
      wins_2      -- float (score)
      forfeits_1  -- int (number of games)
      forfeits_2  -- int (number of games)
      unknown     -- int (number of games)

    scores are multiples of 0.5 (as there may be jigos).

    """
    def __init__(self, results, player_1, player_2):
        self._results = results
        self.player_1 = player_1
        self.player_2 = player_2

        self.total = len(results)

        js = self._jigo_score = 0.5 * sum(r.is_jigo for r in results)
        self.unknown = sum(r.winning_player is None and not r.is_jigo
                           for r in results)

        self.wins_1 = sum(r.winning_player == player_1 for r in results) + js
        self.wins_2 = sum(r.winning_player == player_2 for r in results) + js

        self.forfeits_1 = sum(r.winning_player == player_2 and r.is_forfeit
                              for r in results)
        self.forfeits_2 = sum(r.winning_player == player_1 and r.is_forfeit
                              for r in results)

    def calculate_colour_breakdown(self):
        """Calculate futher statistics, broken down by colour played.

        Sets the following additional attributes:

        played_1b   -- int (number of games)
        played_1w   -- int (number of games)
        played_2b   -- int (number of games)
        played_y2   -- int (number of games)
        alternating -- bool
          when alternating is true =>
            wins_b   -- float (score)
            wins_w   -- float (score)
            wins_1b  -- float (score)
            wins_1w  -- float (score)
            wins_2b  -- float (score)
            wins_2w  -- float (score)
          else =>
            colour_1 -- 'b' or 'w'
            colour_2 -- 'b' or 'w'

        """
        results = self._results
        player_1 = self.player_1
        player_2 = self.player_2
        js = self._jigo_score

        self.played_1b = sum(r.player_b == player_1 for r in results)
        self.played_1w = sum(r.player_w == player_1 for r in results)
        self.played_2b = sum(r.player_b == player_2 for r in results)
        self.played_y2 = sum(r.player_w == player_2 for r in results)

        if self.played_1w == 0 and self.played_2b == 0:
            self.alternating = False
            self.colour_1 = 'b'
            self.colour_2 = 'w'
        elif self.played_1b == 0 and self.played_y2 == 0:
            self.alternating = False
            self.colour_1 = 'w'
            self.colour_2 = 'b'
        else:
            self.alternating = True
            self.wins_b = sum(r.winning_colour == 'b' for r in results) + js
            self.wins_w = sum(r.winning_colour == 'w' for r in results) + js
            self.wins_1b = sum(
                r.winning_player == player_1 and r.winning_colour == 'b'
                for r in results) + js
            self.wins_1w = sum(
                r.winning_player == player_1 and r.winning_colour == 'w'
                for r in results) + js
            self.wins_2b = sum(
                r.winning_player == player_2 and r.winning_colour == 'b'
                for r in results) + js
            self.wins_2w = sum(
                r.winning_player == player_2 and r.winning_colour == 'w'
                for r in results) + js

    def calculate_time_stats(self):
        """Calculate CPU time statistics.

        average_time_1 -- float or None
        average_time_2 -- float or None

        """
        player_1 = self.player_1
        player_2 = self.player_2
        times_1 = [r.cpu_times[player_1] for r in self._results]
        known_times_1 = [t for t in times_1 if t is not None and t != '?']
        times_2 = [r.cpu_times[player_2] for r in self._results]
        known_times_2 = [t for t in times_2 if t is not None and t != '?']
        if known_times_1:
            self.average_time_1 = sum(known_times_1) / len(known_times_1)
        else:
            self.average_time_1 = None
        if known_times_2:
            self.average_time_2 = sum(known_times_2) / len(known_times_2)
        else:
            self.average_time_2 = None


def make_matchup_stats_table(ms):
    """Produce an ascii table showing matchup statistics.

    ms -- Matchup_stats (with all statistics set)

    returns an ascii_tables.Table

    """
    ff = format_float
    pct = format_percent

    t = ascii_tables.Table(row_count=3)
    t.add_heading("") # player name
    i = t.add_column(align='left', right_padding=3)
    t.set_column_values(i, [ms.player_1, ms.player_2])

    t.add_heading("wins")
    i = t.add_column(align='right')
    t.set_column_values(i, [ff(ms.wins_1), ff(ms.wins_2)])

    t.add_heading("") # overall pct
    i = t.add_column(align='right')
    t.set_column_values(i, [pct(ms.wins_1, ms.total),
                            pct(ms.wins_2, ms.total)])

    if ms.alternating:
        t.columns[i].right_padding = 7
        t.add_heading("black", span=2)
        i = t.add_column(align='left')
        t.set_column_values(i, [ff(ms.wins_1b), ff(ms.wins_2b), ff(ms.wins_b)])
        i = t.add_column(align='right', right_padding=5)
        t.set_column_values(i, [pct(ms.wins_1b, ms.played_1b),
                                pct(ms.wins_2b, ms.played_2b),
                                pct(ms.wins_b, ms.total)])

        t.add_heading("white", span=2)
        i = t.add_column(align='left')
        t.set_column_values(i, [ff(ms.wins_1w), ff(ms.wins_2w), ff(ms.wins_w)])
        i = t.add_column(align='right', right_padding=3)
        t.set_column_values(i, [pct(ms.wins_1w, ms.played_1w),
                                pct(ms.wins_2w, ms.played_y2),
                                pct(ms.wins_w, ms.total)])
    else:
        t.columns[i].right_padding = 3
        t.add_heading("")
        i = t.add_column(align='left')
        t.set_column_values(i, ["(%s)" % colour_name(ms.colour_1),
                                "(%s)" % colour_name(ms.colour_2)])

    if ms.forfeits_1 or ms.forfeits_2:
        t.add_heading("forfeits")
        i = t.add_column(align='right')
        t.set_column_values(i, [ms.forfeits_1, ms.forfeits_2])

    if ms.average_time_1 or ms.average_time_2:
        if ms.average_time_1 is not None:
            avg_time_1_s = "%7.2f" % ms.average_time_1
        else:
            avg_time_1_s = "   ----"
        if ms.average_time_2 is not None:
            avg_time_2_s = "%7.2f" % ms.average_time_2
        else:
            avg_time_2_s = "   ----"
        t.add_heading("avg cpu")
        i = t.add_column(align='right', right_padding=2)
        t.set_column_values(i, [avg_time_1_s, avg_time_2_s])

    return t

def write_matchup_summary(out, matchup, ms):
    """Write a summary block for the specified matchup to 'out'.

    matchup -- Matchup_description
    ms      -- Matchup_stats (with all statistics set)

    """
    def p(s):
        print >>out, s

    if matchup.number_of_games is None:
        played_s = "%d" % ms.total
    else:
        played_s = "%d/%d" % (ms.total, matchup.number_of_games)
    p("%s (%s games)" % (matchup.name, played_s))
    if ms.unknown > 0:
        p("unknown results: %d %s" %
          (ms.unknown, format_percent(ms.unknown, ms.total)))

    p(matchup.describe_details())
    p("\n".join(make_matchup_stats_table(ms).render()))

