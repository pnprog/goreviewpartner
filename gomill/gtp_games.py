"""Run a game between two GTP engines."""

from gomill import __version__
from gomill.utils import *
from gomill.common import *
from gomill import gtp_controller
from gomill import handicap_layout
from gomill import boards
from gomill import sgf
from gomill.gtp_controller import BadGtpResponse, GtpChannelError

class Game_result(object):
    """Description of a game result.

    Public attributes:
      players             -- map colour -> player code
      player_b            -- player code
      player_w            -- player code
      winning_player      -- player code or None
      losing_player       -- player code or None
      winning_colour      -- 'b', 'w', or None
      losing_colour       -- 'b', 'w', or None
      is_jigo             -- bool
      is_forfeit          -- bool
      sgf_result          -- string describing the game's result (for sgf RE)
      detail              -- additional information (string or None)
      game_id             -- string or None
      cpu_times           -- map player code -> float or None or '?'.

    Winning/losing colour and player are None for a jigo, unknown result, or
    void game.

    cpu_times are user time + system time. '?' means that gomill-cpu_time gave
    an error.

    Game_results are suitable for pickling.

    """
    def __init__(self, players, winning_colour):
        self.players = players.copy()
        self.player_b = players['b']
        self.player_w = players['w']
        self.winning_colour = winning_colour
        self.winning_player = players.get(winning_colour)
        self.is_jigo = False
        self.is_forfeit = False
        self.game_id = None
        if winning_colour is None:
            self.sgf_result = "?"
        else:
            self.sgf_result = "%s+" % winning_colour.upper()
        self.detail = None
        self.cpu_times = {self.player_b : None, self.player_w : None}

    def __getstate__(self):
        return (
            self.player_b,
            self.player_w,
            self.winning_colour,
            self.sgf_result,
            self.detail,
            self.is_forfeit,
            self.game_id,
            self.cpu_times,
            )

    def __setstate__(self, state):
        (self.player_b,
         self.player_w,
         self.winning_colour,
         self.sgf_result,
         self.detail,
         self.is_forfeit,
         self.game_id,
         self.cpu_times,
         ) = state
        self.players = {'b' : self.player_b, 'w' : self.player_w}
        self.winning_player = self.players.get(self.winning_colour)
        self.is_jigo = (self.sgf_result == "0")

    def set_jigo(self):
        self.sgf_result = "0"
        self.is_jigo = True

    @property
    def losing_colour(self):
        if self.winning_colour is None:
            return None
        return opponent_of(self.winning_colour)

    @property
    def losing_player(self):
        if self.winning_colour is None:
            return None
        return self.players.get(opponent_of(self.winning_colour))

    def describe(self):
        """Return a short human-readable description of the result."""
        if self.winning_colour is not None:
            s = "%s beat %s " % (self.winning_player, self.losing_player)
        else:
            s = "%s vs %s " % (self.players['b'], self.players['w'])
        if self.is_jigo:
            s += "jigo"
        else:
            s += self.sgf_result
        if self.detail is not None:
            s += " (%s)" % self.detail
        return s

    def __repr__(self):
        return "<Game_result: %s>" % self.describe()


class Game(object):
    """A single game between two GTP engines.

    Instantiate with:
      board_size -- int
      komi       -- float (default 0.0)
      move_limit -- int   (default 1000)

    The 'commands' values are lists of strings, as for subprocess.Popen.

    Normal use:

      game = Game(...)
      game.set_player_code('b', ...)
      game.set_player_code('w', ...)
      game.use_internal_scorer() or game.allow_scorer(...) [optional]
      game.set_move_callback...() [optional]
      game.set_player_subprocess('b', ...) or set_player_controller('b', ...)
      game.set_player_subprocess('w', ...) or set_player_controller('w', ...)
      game.request_engine_descriptions() [optional]
      game.ready()
      game.set_handicap(...) [optional]
      game.run()
      game.close_players()
      game.make_sgf() or game.write_sgf(...) [optional]

    then retrieve the Game_result and moves.

    If neither use_internal_scorer() nor allow_scorer() is called, the game
    won't be scored.

    Public attributes for reading:
      players               -- map colour -> player code
      game_id               -- string or None
      result                -- Game_result (None before the game is complete)
      moves                 -- list of tuples (colour, move, comment)
                               move is a pair (row, col), or None for a pass
      player_scores         -- map player code -> string or None
      engine_names          -- map player code -> string
      engine_descriptions   -- map player code -> string

   player_scores values are the response to the final_score GTP command (if the
   player was asked).

   Methods which communicate with engines may raise BadGtpResponse if the
   engine returns a failure response.

   Methods which communicate with engines will normally raise GtpChannelError
   if there is trouble communicating with the engine. But after the game result
   has been decided, they will set these errors aside; retrieve them with
   describe_late_errors().

   This enforces a simple ko rule, but no superko rule. It accepts self-capture
   moves.

   """

    def __init__(self, board_size, komi=0.0, move_limit=1000):
        self.players = {'b' : 'b', 'w' : 'w'}
        self.game_id = None
        self.controllers = {}
        self.claim_allowed = {'b' : False, 'w' : False}
        self.after_move_callback = None
        self.board_size = board_size
        self.komi = komi
        self.move_limit = move_limit
        self.allowed_scorers = []
        self.internal_scorer = False
        self.handicap_compensation = "no"
        self.handicap = 0
        self.first_player = "b"
        self.engine_names = {}
        self.engine_descriptions = {}
        self.moves = []
        self.player_scores = {'b' : None, 'w' : None}
        self.additional_sgf_props = []
        self.late_errors = []
        self.handicap_stones = None
        self.result = None
        self.board = boards.Board(board_size)
        self.simple_ko_point = None


    ## Configuration methods (callable before set_player_...)

    def set_player_code(self, colour, player_code):
        """Specify a player code.

        player_code -- short ascii string

        The player codes are used to identify the players in game results, sgf
        files, and the error messages.

        Setting these is optional but strongly encouraged. If not explicitly
        set, they will just be 'b' and 'w'.

        Raises ValueError if both players are given the same code.

        """
        s = str(player_code)
        if self.players[opponent_of(colour)] == s:
            raise ValueError("player codes must be distinct")
        self.players[colour] = s

    def set_game_id(self, game_id):
        """Specify a game id.

        game_id -- string

        The game id is reported in the game result, and used as a default game
        name in the SGF file.

        If you don't set it, it will have value None.

        """
        self.game_id = str(game_id)

    def use_internal_scorer(self, handicap_compensation='no'):
        """Set the scoring method to internal.

        The internal scorer uses area score, assuming all stones alive.

        handicap_compensation -- 'no' (default), 'short', or 'full'.

        If handicap_compensation is 'full', one point is deducted from Black's
        score for each handicap stone; if handicap_compensation is 'short', one
        point is deducted from Black's score for each handicap stone except the
        first. (The number of handicap stones is taken from the parameter to
        set_handicap().)

        """
        self.internal_scorer = True
        if handicap_compensation not in ('no', 'short', 'full'):
            raise ValueError("bad handicap_compensation value: %s" %
                             handicap_compensation)
        self.handicap_compensation = handicap_compensation

    def allow_scorer(self, colour):
        """Allow the specified player to score the game.

        If this is called for both colours, both are asked to score.

        """
        self.allowed_scorers.append(colour)

    def set_claim_allowed(self, colour, b=True):
        """Allow the specified player to claim a win.

        This will have no effect if the engine doesn't implement
        gomill-genmove_ex.

        """
        self.claim_allowed[colour] = bool(b)

    def set_move_callback(self, fn):
        """Specify a callback function to be called after every move.

        This function is called after each move is played, including passes but
        not resignations, and not moves which triggered a forfeit.

        It is passed three parameters: colour, move, board
          move is a pair (row, col), or None for a pass

        Treat the board parameter as read-only.

        Exceptions raised from the callback will be propagated unchanged out of
        run().

        """
        self.after_move_callback = fn


    ## Channel methods

    def set_player_controller(self, colour, controller,
                              check_protocol_version=True):
        """Specify a player using a Gtp_controller.

        controller             -- Gtp_controller
        check_protocol_version -- bool (default True)

        By convention, the channel name should be 'player <player code>'.

        If check_protocol_version is true, rejects an engine that declares a
        GTP protocol version <> 2.

        Propagates GtpChannelError if there's an error checking the protocol
        version.

        """
        self.controllers[colour] = controller
        if check_protocol_version:
            controller.check_protocol_version()

    def set_player_subprocess(self, colour, command,
                              check_protocol_version=True, **kwargs):
        """Specify the a player as a subprocess.

        command                -- list of strings (as for subprocess.Popen)
        check_protocol_version -- bool (default True)

        Additional keyword arguments are passed to the Subprocess_gtp_channel
        constructor.

        If check_protocol_version is true, rejects an engine that declares a
        GTP protocol version <> 2.

        Propagates GtpChannelError if there's an error creating the
        subprocess or checking the protocol version.

        """
        try:
            channel = gtp_controller.Subprocess_gtp_channel(command, **kwargs)
        except GtpChannelError, e:
            raise GtpChannelError(
                "error starting subprocess for player %s:\n%s" %
                (self.players[colour], e))
        controller = gtp_controller.Gtp_controller(
            channel, "player %s" % self.players[colour])
        self.set_player_controller(colour, controller, check_protocol_version)

    def get_controller(self, colour):
        """Return the underlying Gtp_controller for the specified engine."""
        return self.controllers[colour]

    def send_command(self, colour, command, *arguments):
        """Send the specified GTP command to one of the players.

        colour    -- player to talk to ('b' or 'w')
        command   -- gtp command name (string)
        arguments -- gtp arguments (strings)

        Returns the response as a string.

        Raises BadGtpResponse if the engine returns a failure response.

        You can use this at any time between set_player_...() and
        close_players().

        """
        return self.controllers[colour].do_command(command, *arguments)

    def maybe_send_command(self, colour, command, *arguments):
        """Send the specified GTP command, if supported.

        Variant of send_command(): if the command isn't supported by the
        engine, or gives a failure response, returns None.

        """
        controller = self.controllers[colour]
        if controller.known_command(command):
            try:
                result = controller.do_command(command, *arguments)
            except BadGtpResponse:
                result = None
        else:
            result = None
        return result

    def known_command(self, colour, command):
        """Check whether the specified GTP command is supported."""
        return self.controllers[colour].known_command(command)

    def close_players(self):
        """Close both controllers (if they're open).

        Retrieves the late errors for describe_late_errors().

        If cpu times are not already set in the game result, sets them from the
        CPU usage of the engine subprocesses.

        """
        for colour in ("b", "w"):
            controller = self.controllers.get(colour)
            if controller is None:
                continue
            controller.safe_close()
            self.late_errors += controller.retrieve_error_messages()
        self.update_cpu_times_from_channels()


    ## High-level methods

    def request_engine_descriptions(self):
        """Obtain the engines' name, version, and description by GTP.

        After you have called this, you can retrieve the results from the
        engine_names and engine_descriptions attributes.

        If this has been called, other methods will use the engine name and/or
        description when appropriate (ie, call this if you want proper engine
        names to appear in the SGF file).

        """
        for colour in "b", "w":
            controller = self.controllers[colour]
            player = self.players[colour]
            short_s, long_s = gtp_controller.describe_engine(controller, player)
            self.engine_names[player] = short_s
            self.engine_descriptions[player] = long_s

    def ready(self):
        """Reset the engines' GTP game state (board size, contents, komi)."""
        for colour in "b", "w":
            controller = self.controllers[colour]
            controller.do_command("boardsize", str(self.board_size))
            controller.do_command("clear_board")
            controller.do_command("komi", str(self.komi))

    def set_handicap(self, handicap, is_free):
        """Initialise the board position for a handicap.

        Raises ValueError if the number of stones isn't valid (see GTP spec).

        Raises BadGtpResponse if there's an invalid respone to
        place_free_handicap or fixed_handicap.

        """
        if is_free:
            max_points = handicap_layout.max_free_handicap_for_board_size(
                self.board_size)
            if not 2 <= handicap <= max_points:
                raise ValueError
            vertices = self.send_command(
                "b", "place_free_handicap", str(handicap))
            try:
                points = [move_from_vertex(vt, self.board_size)
                          for vt in vertices.split(" ")]
                if None in points:
                    raise ValueError("response included 'pass'")
                if len(set(points)) < len(points):
                    raise ValueError("duplicate point")
            except ValueError, e:
                raise BadGtpResponse(
                    "invalid response from place_free_handicap command "
                    "to %s: %s" % (self.players["b"], e))
            vertices = [format_vertex(point) for point in points]
            self.send_command("w", "set_free_handicap", *vertices)
        else:
            # May propagate ValueError
            points = handicap_layout.handicap_points(handicap, self.board_size)
            for colour in "b", "w":
                vertices = self.send_command(
                    colour, "fixed_handicap", str(handicap))
                try:
                    seen_points = [move_from_vertex(vt, self.board_size)
                                   for vt in vertices.split(" ")]
                    if set(seen_points) != set(points):
                        raise ValueError
                except ValueError:
                    raise BadGtpResponse(
                        "bad response from fixed_handicap command "
                        "to %s: %s" % (self.players[colour], vertices))
        self.board.apply_setup(points, [], [])
        self.handicap = handicap
        self.additional_sgf_props.append(('HA', handicap))
        self.handicap_stones = points
        self.first_player = "w"

    def _forfeit_to(self, winner, msg):
        self.winner = winner
        self.forfeited = True
        self.forfeit_reason = msg

    def _play_move(self, colour):
        opponent = opponent_of(colour)
        if (self.claim_allowed[colour] and
            self.known_command(colour, "gomill-genmove_ex")):
            genmove_command = ["gomill-genmove_ex", colour, "claim"]
            may_claim = True
        else:
            genmove_command = ["genmove", colour]
            may_claim = False
        try:
            move_s = self.send_command(colour, *genmove_command).lower()
        except BadGtpResponse, e:
            self._forfeit_to(opponent, str(e))
            return
        if move_s == "resign":
            self.winner = opponent
            self.seen_resignation = True
            return
        if may_claim and move_s == "claim":
            self.winner = colour
            self.seen_claim = True
            return
        try:
            move = move_from_vertex(move_s, self.board_size)
        except ValueError:
            self._forfeit_to(opponent, "%s attempted ill-formed move %s" % (
                self.players[colour], move_s))
            return
        comment = self.maybe_send_command(colour, "gomill-explain_last_move")
        comment = sanitise_utf8(comment)
        if comment == "":
            comment = None
        if move is not None:
            self.pass_count = 0
            if move == self.simple_ko_point:
                self._forfeit_to(
                    opponent, "%s attempted move to ko-forbidden point %s" % (
                        self.players[colour], move_s))
                return
            row, col = move
            try:
                self.simple_ko_point = self.board.play(row, col, colour)
            except ValueError:
                self._forfeit_to(
                    opponent, "%s attempted move to occupied point %s" % (
                        self.players[colour], move_s))
                return
        else:
            self.pass_count += 1
            self.simple_ko_point = None
        try:
            self.send_command(opponent, "play", colour, move_s)
        except BadGtpResponse, e:
            if e.gtp_error_message == "illegal move":
                # we assume the move really was illegal, so 'colour' should lose
                self._forfeit_to(opponent, "%s claims move %s is illegal" % (
                    self.players[opponent], move_s))
            else:
                self._forfeit_to(colour, str(e))
            return
        self.moves.append((colour, move, comment))
        if self.after_move_callback:
            self.after_move_callback(colour, move, self.board)

    def run(self):
        """Run a complete game between the two players.

        Sets self.moves and self.result.

        Sets CPU times in the game result if available via GTP.

        """
        self.pass_count = 0
        self.winner = None
        self.margin = None
        self.scorers_disagreed = False
        self.seen_resignation = False
        self.seen_claim = False
        self.forfeited = False
        self.hit_move_limit = False
        self.forfeit_reason = None
        self.passed_out = False
        player = self.first_player
        move_count = 0
        while move_count < self.move_limit:
            self._play_move(player)
            if self.pass_count == 2:
                self.passed_out = True
                self.winner, self.margin, self.scorers_disagreed = \
                    self._score_game()
                break
            if self.winner is not None:
                break
            player = opponent_of(player)
            move_count += 1
        else:
            self.hit_move_limit = True
        self.calculate_result()
        self.calculate_cpu_times()

    def fake_run(self, winner):
        """Set state variables as if the game had been run (for testing).

        You don't need to use set_player_{subprocess,controller} to call this.

        winner -- 'b' or 'w'

        """
        self.winner = winner
        self.seen_resignation = False
        self.seen_claim = False
        self.forfeited = False
        self.hit_move_limit = False
        self.forfeit_reason = None
        self.passed_out = True
        self.margin = True
        self.scorers_disagreed = False
        self.calculate_result()

    def _score_game(self):
        is_disagreement = False
        if self.internal_scorer:
            score = self.board.area_score() - self.komi
            if self.handicap:
                if self.handicap_compensation == "full":
                    score -= self.handicap
                elif self.handicap_compensation == "short":
                    score -= (self.handicap - 1)
            if score > 0:
                winner = "b"
                margin = score
            elif score < 0:
                winner = "w"
                margin = -score
            else:
                winner = None
                margin = 0
        else:
            winners = []
            margins = []
            for colour in self.allowed_scorers:
                final_score = self.maybe_send_command(colour, "final_score")
                if final_score is None:
                    continue
                self.player_scores[colour] = final_score
                final_score = final_score.upper()
                if final_score == "0":
                    winners.append(None)
                    margins.append(0)
                    continue
                if final_score.startswith("B+"):
                    winners.append("b")
                elif final_score.startswith("W+"):
                    winners.append("w")
                else:
                    continue
                try:
                    margin = float(final_score[2:])
                    if margin <= 0:
                        margin = None
                except ValueError:
                    margin = None
                margins.append(margin)
            if len(set(winners)) == 1:
                winner = winners[0]
                if len(set(margins)) == 1:
                    margin = margins[0]
                else:
                    margin = None
            else:
                if len(set(winners)) > 1:
                    is_disagreement = True
                winner = None
                margin = None
        return winner, margin, is_disagreement

    def calculate_result(self):
        """Set self.result.

        You shouldn't normally call this directly.

        """
        result = Game_result(self.players, self.winner)
        result.game_id = self.game_id
        if self.hit_move_limit:
            result.sgf_result = "Void"
            result.detail = "hit move limit"
        elif self.seen_resignation:
            result.sgf_result += "R"
        elif self.seen_claim:
            # Leave SGF result in form 'B+'
            result.detail = "claim"
        elif self.forfeited:
            result.sgf_result += "F"
            result.is_forfeit = True
            result.detail = "forfeit: %s" % self.forfeit_reason
        else:
            assert self.passed_out
            if self.winner is None:
                if self.margin == 0:
                    result.set_jigo()
                elif self.scorers_disagreed:
                    result.detail = "players disagreed"
                else:
                    result.detail = "no score reported"
            elif self.margin is not None:
                result.sgf_result += format_float(self.margin)
            else:
                # Players returned something like 'B+?',
                # or disagreed about the margin
                # Leave SGF result in form 'B+'
                result.detail = "unknown margin"
        self.result = result

    def calculate_cpu_times(self):
        """Set CPU times in self.result.

        You shouldn't normally call this directly.

        """
        # The ugliness with cpu_time '?' is to avoid using the cpu time reported
        # by channel close() for engines which claim to support gomill-cpu_time
        # but give an error.
        for colour in ('b', 'w'):
            cpu_time = None
            controller = self.controllers[colour]
            if controller.safe_known_command('gomill-cpu_time'):
                try:
                    s = controller.safe_do_command('gomill-cpu_time')
                    cpu_time = float(s)
                except (BadGtpResponse, ValueError, TypeError):
                    cpu_time = "?"
            self.result.cpu_times[self.players[colour]] = cpu_time

    def update_cpu_times_from_channels(self):
        """Set CPU times in self.result from the channel resource usage.

        There's normally no need to call this directly: close_players() will do
        it.

        Has no effect if CPU times have already been set.

        """
        for colour in ('b', 'w'):
            controller = self.controllers.get(colour)
            if controller is None:
                continue
            ru = controller.channel.resource_usage
            if (ru is not None and self.result is not None and
                self.result.cpu_times[self.players[colour]] is None):
                self.result.cpu_times[self.players[colour]] = \
                    ru.ru_utime + ru.ru_stime

    def describe_late_errors(self):
        """Retrieve the late error messages.

        Returns a string, or None if there were no late errors.

        This is only available after close_players() has been called.

        The late errors are low-level errors which occurred after the game
        result was decided and so were set asied. In particular, they include
        any errors from closing (including failure responses from the final
        'quit' command)

        """
        if not self.late_errors:
            return None
        return "\n".join(self.late_errors)

    def describe_scoring(self):
        """Return a multiline string describing the game's scoring."""
        if self.result is None:
            return ""
        def normalise_score(s):
            s = s.upper()
            if s.endswith(".0"):
                s = s[:-2]
            return s
        l = [self.result.describe()]
        sgf_result = self.result.sgf_result
        score_b = self.player_scores['b']
        score_w = self.player_scores['w']
        if ((score_b is not None and normalise_score(score_b) != sgf_result) or
            (score_w is not None and normalise_score(score_w) != sgf_result)):
            for colour, score in (('b', score_b), ('w', score_w)):
                if score is not None:
                    l.append("%s final_score: %s" %
                             (self.players[colour], score))
        return "\n".join(l)

    def make_sgf(self, game_end_message=None):
        """Return an SGF description of the game.

        Returns an Sgf_game object.

        game_end_message -- optional string to put in the final comment.

        If game_end_message is specified, it appears before the text describing
        'late errors'.

        """
        sgf_game = sgf.Sgf_game(self.board_size)
        root = sgf_game.get_root()
        root.set('KM', self.komi)
        root.set('AP', ("gomill",  __version__))
        for prop, value in self.additional_sgf_props:
            root.set(prop, value)
        sgf_game.set_date()
        if self.engine_names:
            root.set('PB', self.engine_names[self.players['b']])
            root.set('PW', self.engine_names[self.players['w']])
        if self.game_id:
            root.set('GN', self.game_id)
        if self.handicap_stones:
            root.set_setup_stones(black=self.handicap_stones, white=[])
        for colour, move, comment in self.moves:
            node = sgf_game.extend_main_sequence()
            node.set_move(colour, move)
            if comment is not None:
                node.set("C", comment)
        last_node = sgf_game.get_last_node()
        if self.result is not None:
            root.set('RE', self.result.sgf_result)
            last_node.add_comment_text(self.describe_scoring())
        if game_end_message is not None:
            last_node.add_comment_text(game_end_message)
        late_error_messages = self.describe_late_errors()
        if late_error_messages is not None:
            last_node.add_comment_text(late_error_messages)
        return sgf_game

    def write_sgf(self, pathname, game_end_message=None):
        """Write an SGF description of the game to the specified pathname."""
        sgf_game = self.make_sgf(game_end_message)
        f = open(pathname, "w")
        f.write(sgf_game.serialise())
        f.close()

