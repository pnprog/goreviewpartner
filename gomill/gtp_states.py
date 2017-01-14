"""Stateful GTP engine."""

from __future__ import with_statement

from gomill import __version__
from gomill.common import *
from gomill import ascii_boards
from gomill import boards
from gomill import gtp_engine
from gomill import handicap_layout
from gomill import sgf
from gomill import sgf_grammar
from gomill import sgf_moves
from gomill.gtp_engine import GtpError


class History_move(object):
    """Information about a move (for move_history).

    Public attributes:
      colour
      move     -- (row, col), or None for a pass
      comments -- multiline string, or None
      cookie

    comments are used by gomill-savesgf.

    The cookie attribute stores an arbitrary value which was provided by the
    move generator when the move was played. The cookie attribute of a move
    which did not come from the move generator is None.

    This is a way for a move generator to maintain state across moves, without
    becoming confused by 'undo' &c. It's not intended for storing large amounts
    of data.

    """
    def __init__(self, colour, move, comments=None, cookie=None):
        self.colour = colour
        self.move = move
        self.comments = comments
        self.cookie = cookie

    def is_pass(self):
        return (self.move is None)


class Game_state(object):
    """Data passed to a move generator.

    Public attributes:
      size                      -- int
      board                     -- boards.Board
      komi                      -- float
      history_base              -- boards.Board
      move_history              -- list of History_move objects
      ko_point                  -- (row, col) or None
      handicap                  -- int >= 2 or None
      for_regression            -- bool
      time_settings             -- tuple (m, b, s), or None
      time_remaining            -- int (seconds), or None
      canadian_stones_remaining -- int or None

    'board' represents the current board position.

    history_base represents a (possibly) earlier board position; move_history
    lists the moves leading to 'board' from that position.

    Normally, history_base will be an empty board, or else be the position after
    the placement of handicap stones; but if the loadsgf command has been used
    it may be the position given by setup stones in the SGF file.

    The get_last_move() and get_last_move_and_cookie() functions below are
    provided to help interpret move history.


    ko_point is the point forbidden by the simple ko rule. This is provided for
    convenience for engines which don't want to deduce it from the move history.
    To handle superko properly, engines will have to use the move history.


    'handicap' is provided in case the engine wants to modify its behaviour in
    handicap games; it can safely be ignored. Any handicap stones will be
    present in history_base.


    for_regression is true if the command was 'reg_genmove'; engines which care
    should use a fixed seed in this case.


    time_settings describes the time limits for the game; time_remaining
    describes the current situation.

    time_settings values m, b, s are main time (in seconds), 'Canadian byo-yomi'
    time (in seconds), and 'Canadian byo-yomi' stones; see GTP spec 4.2 (which
    describes what 0 values mean). time_settings None means the information
    isn't available.

    time_remaining None means the game isn't timed. canadian_stones_remaining
    None means we're in main time.

    The most important information for the move generator is in time_remaining;
    time_settings lets it know whether it's going to get overtime as well. It's
    possible for time_remaining to be available but not time_settings (if the
    controller doesn't send time_settings).

    """

class Move_generator_result(object):
    """Return value from a move generator.

    Public attributes:
      resign    -- bool
      pass_move -- bool
      move      -- (row, col), or None
      claim     -- bool (for gomill-genmove_ex claim)
      comments  -- multiline string, or None
      cookie    -- arbitrary value

    Exactly one of the first three attributes should be set to a nondefault
    value. The other attributes can be safely left at their defaults.

    If claim is true, either 'move' or 'pass_move' must still be set.

    comments are used by gomill-explain_last_move and gomill-savesgf.

    See History_move for an explanation of the cookie attribute. It has the
    value None if not explicitly set.

    """
    def __init__(self):
        self.resign = False
        self.pass_move = False
        self.move = None
        self.claim = False
        self.comments = None
        self.cookie = None


class Gtp_state(object):
    """Manage the stateful part of the GTP engine protocol.

    This supports implementing a GTP engine using a stateless move generator.

    Sample use:
      gtp_state = Gtp_state(...)
      engine = Gtp_engine_protocol()
      engine.add_commands(gtp_state.get_handlers())

    A Gtp_state maintains the following state:
      board configuration
      move history
      komi
      simple ko ban


    Instantiate with a _move generator function_ and a list of acceptable board
    sizes (default 19 only).

    The move generator function is called to handle genmove. It is passed
    arguments (game_state, colour to play). It should return a
    Move_generator_result. It must not modify data passed in the game_state.

    If the move generator returns an occupied point, Gtp_state will report a GTP
    error. Gtp_state does not enforce any ko rule. It permits self-captures.

    """

    def __init__(self, move_generator, acceptable_sizes=None):
        self.komi = 0.0
        self.time_settings = None
        self.time_status = {
            'b' : (None, None),
            'w' : (None, None),
            }
        self.move_generator = move_generator
        if acceptable_sizes is None:
            self.acceptable_sizes = set((19,))
            self.board_size = 19
        else:
            self.acceptable_sizes = set(acceptable_sizes)
            self.board_size = min(self.acceptable_sizes)
        self.reset()

    def reset(self):
        self.board = boards.Board(self.board_size)
        # None, or a small integer
        self.handicap = None
        self.simple_ko_point = None
        # Player that any simple_ko_point is banned for
        self.simple_ko_player = None
        self.history_base = boards.Board(self.board_size)
        # list of History_move objects
        self.move_history = []

    def set_history_base(self, board):
        """Change the history base to a new position.

        Takes ownership of 'board'.

        Clears the move history.

        """
        self.history_base = board
        self.move_history = []

    def reset_to_moves(self, history_moves):
        """Reset to history base and play the specified moves.

        history_moves -- list of History_move objects.

        'history_moves' becomes the new move history. Takes ownership of
        'history_moves'.

        Raises ValueError if there is an invalid move in the list.

        """
        self.board = self.history_base.copy()
        simple_ko_point = None
        simple_ko_player = None
        for history_move in history_moves:
            if history_move.is_pass():
                self.simple_ko_point = None
                continue
            row, col = history_move.move
            # Propagates ValueError if the move is bad
            simple_ko_point = self.board.play(row, col, history_move.colour)
            simple_ko_player = opponent_of(history_move.colour)
        self.simple_ko_point = simple_ko_point
        self.simple_ko_player = simple_ko_player
        self.move_history = history_moves

    def set_komi(self, f):
        max_komi = 625.0
        if f < -max_komi:
            f = -max_komi
        elif f > max_komi:
            f = max_komi
        self.komi = f

    def handle_boardsize(self, args):
        try:
            size = gtp_engine.interpret_int(args[0])
        except IndexError:
            gtp_engine.report_bad_arguments()
        if size not in self.acceptable_sizes:
            raise GtpError("unacceptable size")
        self.board_size = size
        self.reset()

    def handle_clear_board(self, args):
        self.reset()

    def handle_komi(self, args):
        try:
            f = gtp_engine.interpret_float(args[0])
        except IndexError:
            gtp_engine.report_bad_arguments()
        self.set_komi(f)

    def handle_fixed_handicap(self, args):
        try:
            number_of_stones = gtp_engine.interpret_int(args[0])
        except IndexError:
            gtp_engine.report_bad_arguments()
        if not self.board.is_empty():
            raise GtpError("board not empty")
        try:
            points = handicap_layout.handicap_points(
                number_of_stones, self.board_size)
        except ValueError:
            raise GtpError("invalid number of stones")
        for row, col in points:
            self.board.play(row, col, 'b')
        self.simple_ko_point = None
        self.handicap = number_of_stones
        self.set_history_base(self.board.copy())
        return " ".join(format_vertex((row, col))
                        for (row, col) in points)

    def handle_set_free_handicap(self, args):
        max_points = handicap_layout.max_free_handicap_for_board_size(
            self.board_size)
        if not 2 <= len(args) <= max_points:
            raise GtpError("invalid number of stones")
        if not self.board.is_empty():
            raise GtpError("board not empty")
        try:
            for vertex_s in args:
                move = gtp_engine.interpret_vertex(vertex_s, self.board_size)
                if move is None:
                    raise GtpError("'pass' not permitted")
                row, col = move
                try:
                    self.board.play(row, col, 'b')
                except ValueError:
                    raise GtpError("engine error: %s is occupied" % vertex_s)
        except Exception:
            self.reset()
            raise
        self.set_history_base(self.board.copy())
        self.handicap = len(args)
        self.simple_ko_point = None

    def _choose_free_handicap_moves(self, number_of_stones):
        i = min(number_of_stones,
                handicap_layout.max_fixed_handicap_for_board_size(
                    self.board_size))
        return handicap_layout.handicap_points(i, self.board_size)

    def handle_place_free_handicap(self, args):
        try:
            number_of_stones = gtp_engine.interpret_int(args[0])
        except IndexError:
            gtp_engine.report_bad_arguments()
        max_points = handicap_layout.max_free_handicap_for_board_size(
            self.board_size)
        if not 2 <= number_of_stones <= max_points:
            raise GtpError("invalid number of stones")
        if not self.board.is_empty():
            raise GtpError("board not empty")
        if number_of_stones == max_points:
            number_of_stones = max_points - 1
        moves = self._choose_free_handicap_moves(number_of_stones)
        try:
            try:
                if len(moves) > number_of_stones:
                    raise ValueError
                for row, col in moves:
                    self.board.play(row, col, 'b')
            except (ValueError, TypeError):
                raise GtpError("invalid result from move generator: %s"
                               % format_vertex_list(moves))
        except Exception:
            self.reset()
            raise
        self.simple_ko_point = None
        self.handicap = number_of_stones
        self.set_history_base(self.board.copy())
        return " ".join(format_vertex((row, col))
                        for (row, col) in moves)

    def handle_play(self, args):
        try:
            colour_s, vertex_s = args[:2]
        except ValueError:
            gtp_engine.report_bad_arguments()
        colour = gtp_engine.interpret_colour(colour_s)
        move = gtp_engine.interpret_vertex(vertex_s, self.board_size)
        if move is None:
            self.simple_ko_point = None
            self.move_history.append(History_move(colour, None))
            return
        row, col = move
        try:
            self.simple_ko_point = self.board.play(row, col, colour)
            self.simple_ko_player = opponent_of(colour)
        except ValueError:
            raise GtpError("illegal move")
        self.move_history.append(History_move(colour, move))

    def handle_showboard(self, args):
        return "\n%s\n" % ascii_boards.render_board(self.board)

    def _handle_genmove(self, args, for_regression=False, allow_claim=False):
        """Common implementation for genmove commands."""
        try:
            colour = gtp_engine.interpret_colour(args[0])
        except IndexError:
            gtp_engine.report_bad_arguments()
        game_state = Game_state()
        game_state.size = self.board_size
        game_state.board = self.board
        game_state.history_base = self.history_base
        game_state.move_history = self.move_history
        game_state.komi = self.komi
        game_state.for_regression = for_regression
        if self.simple_ko_point is not None and self.simple_ko_player == colour:
            game_state.ko_point = self.simple_ko_point
        else:
            game_state.ko_point = None
        game_state.handicap = self.handicap
        game_state.time_settings = self.time_settings
        game_state.time_remaining, game_state.canadian_stones_remaining = \
            self.time_status[colour]
        generated = self.move_generator(game_state, colour)
        if allow_claim and generated.claim:
            return 'claim'
        if generated.resign:
            return 'resign'
        if generated.pass_move:
            if not for_regression:
                self.move_history.append(History_move(
                    colour, None, generated.comments, generated.cookie))
            return 'pass'
        row, col = generated.move
        vertex = format_vertex((row, col))
        if not for_regression:
            try:
                self.simple_ko_point = self.board.play(row, col, colour)
                self.simple_ko_player = opponent_of(colour)
            except ValueError:
                raise GtpError("engine error: tried to play %s" % vertex)
            self.move_history.append(
                History_move(colour, generated.move,
                             generated.comments, generated.cookie))
        return vertex

    def handle_genmove(self, args):
        return self._handle_genmove(args)

    def handle_genmove_ex(self, args):
        if not args:
            return "claim"
        allow_claim = False
        for arg in args[1:]:
            if arg == 'claim':
                allow_claim = True
        return self._handle_genmove(args[:1], allow_claim=allow_claim)

    def handle_reg_genmove(self, args):
        return self._handle_genmove(args, for_regression=True)

    def handle_undo(self, args):
        if not self.move_history:
            raise GtpError("cannot undo")
        try:
            self.reset_to_moves(self.move_history[:-1])
        except ValueError:
            raise GtpError("corrupt history")

    def _load_file(self, pathname):
        """Read the specified file and return its contents as a string.

        Subclasses can override this to change how loadsgf interprets filenames.

        May raise EnvironmentError.

        """
        with open(pathname) as f:
            return f.read()

    def handle_loadsgf(self, args):
        try:
            pathname = args[0]
        except IndexError:
            gtp_engine.report_bad_arguments()
        if len(args) > 1:
            move_number = gtp_engine.interpret_int(args[1])
        else:
            move_number = None
        # The GTP spec mandates the "cannot load file" error message, so we
        # can't be more helpful.
        try:
            s = self._load_file(pathname)
        except EnvironmentError:
            raise GtpError("cannot load file")
        try:
            sgf_game = sgf.Sgf_game.from_string(s)
        except ValueError:
            raise GtpError("cannot load file")
        new_size = sgf_game.get_size()
        if new_size not in self.acceptable_sizes:
            raise GtpError("unacceptable size")
        self.board_size = new_size
        try:
            komi = sgf_game.get_komi()
        except ValueError:
            raise GtpError("bad komi")
        try:
            handicap = sgf_game.get_handicap()
        except ValueError:
            # Handicap isn't important, so soldier on
            handicap = None
        try:
            sgf_board, plays = sgf_moves.get_setup_and_moves(sgf_game)
        except ValueError, e:
            raise GtpError(str(e))
        history_moves = [History_move(colour, move)
                         for (colour, move) in plays]
        if move_number is None:
            new_move_history = history_moves
        else:
            # gtp spec says we want the "position before move_number"
            move_number = max(0, move_number-1)
            new_move_history = history_moves[:move_number]
        old_history_base = self.history_base
        old_move_history = self.move_history
        try:
            self.set_history_base(sgf_board)
            self.reset_to_moves(new_move_history)
        except ValueError:
            try:
                self.set_history_base(old_history_base)
                self.reset_to_moves(old_move_history)
            except ValueError:
                raise GtpError("bad move in file and corrupt history")
            raise GtpError("bad move in file")
        self.set_komi(komi)
        self.handicap = handicap

    def handle_time_left(self, args):
        # colour time stones
        try:
            colour = gtp_engine.interpret_colour(args[0])
            time_remaining = gtp_engine.interpret_int(args[1])
            stones_remaining = gtp_engine.interpret_int(args[2])
        except IndexError:
            gtp_engine.report_bad_arguments()
        if stones_remaining == 0:
            stones_remaining = None
        self.time_status[colour] = (time_remaining, stones_remaining)

    def handle_time_settings(self, args):
        try:
            main_time = gtp_engine.interpret_int(args[0])
            canadian_time = gtp_engine.interpret_int(args[1])
            canadian_stones = gtp_engine.interpret_int(args[2])
        except IndexError:
            gtp_engine.report_bad_arguments()
        self.time_settings = (main_time, canadian_time, canadian_stones)

    def handle_explain_last_move(self, args):
        try:
            return self.move_history[-1].comments
        except IndexError:
            return None

    def _save_file(self, pathname, contents):
        """Write a string to the specified file.

        Subclasses can override this to change how gomill-savesgf interprets
        filenames.

        May raise EnvironmentError.

        """
        with open(pathname, "w") as f:
            f.write(contents)

    def handle_savesgf(self, args):
        try:
            pathname = args[0]
        except IndexError:
            gtp_engine.report_bad_arguments()

        sgf_game = sgf.Sgf_game(self.board_size)
        root = sgf_game.get_root()
        root.set('KM', self.komi)
        root.set('AP', ("gomill", __version__))
        sgf_game.set_date()
        if self.handicap is not None:
            root.set('HA', self.handicap)
        for arg in args[1:]:
            try:
                identifier, value = arg.split("=", 1)
                if not identifier.isalpha():
                    raise ValueError
                identifier = identifier.upper()
                value = value.replace("\\_", " ").replace("\\\\", "\\")
            except Exception:
                gtp_engine.report_bad_arguments()
            root.set_raw(identifier, sgf_grammar.escape_text(value))
        sgf_moves.set_initial_position(sgf_game, self.history_base)
        for history_move in self.move_history:
            node = sgf_game.extend_main_sequence()
            node.set_move(history_move.colour, history_move.move)
            if history_move.comments is not None:
                node.set("C", history_move.comments)
        sgf_moves.indicate_first_player(sgf_game)
        try:
            self._save_file(pathname, sgf_game.serialise())
        except EnvironmentError, e:
            raise GtpError("error writing file: %s" % e)


    def get_handlers(self):
        return {'boardsize'                : self.handle_boardsize,
                'clear_board'              : self.handle_clear_board,
                'komi'                     : self.handle_komi,
                'fixed_handicap'           : self.handle_fixed_handicap,
                'set_free_handicap'        : self.handle_set_free_handicap,
                'place_free_handicap'      : self.handle_place_free_handicap,
                'play'                     : self.handle_play,
                'genmove'                  : self.handle_genmove,
                'gomill-genmove_ex'        : self.handle_genmove_ex,
                'reg_genmove'              : self.handle_reg_genmove,
                'undo'                     : self.handle_undo,
                'showboard'                : self.handle_showboard,
                'loadsgf'                  : self.handle_loadsgf,
                'gomill-explain_last_move' : self.handle_explain_last_move,
                'gomill-savesgf'           : self.handle_savesgf,
                }

    def get_time_handlers(self):
        """Return handlers for time-related commands.

        These are separated out so that engines which don't support time
        handling can avoid advertising time support.

        """
        return {'time_left'           : self.handle_time_left,
                'time_settings'       : self.handle_time_settings,
                }


def get_last_move(history_moves, player):
    """Get the last move from the move history, checking it's by the opponent.

    This is a convenience function for use by move generators.

    history_moves -- list of History_move objects
    player        -- player to play current move ('b' or 'w')

    Returns a pair (move_is_available, move)
    where move is (row, col), or None for a pass.

    If the last move is unknown, or it wasn't by the opponent, move_is_available
    is False and move is None.

    """
    if not history_moves:
        return False, None
    if history_moves[-1].colour != opponent_of(player):
        return False, None
    return True, history_moves[-1].move

def get_last_move_and_cookie(history_moves, player):
    """Interpret recent move history.

    This is a convenience function for use by move generators.

    This is a variant of get_last_move, which also returns the last-but-one
    move's cookie if available.

    Returns a tuple (move_is_available, opponent's move, cookie)

    move_is_available has the same meaning as for get_last_move().

    If move_is_available is false, or if the next-to-last move is unavailable or
    wasn't by the current player, cookie is None.

    """
    move_is_available, opponents_move = get_last_move(history_moves, player)
    if (move_is_available and len(history_moves) > 1 and
        history_moves[-2].colour == player):
        cookie = history_moves[-2].cookie
    else:
        cookie = None
    return move_is_available, opponents_move, cookie


