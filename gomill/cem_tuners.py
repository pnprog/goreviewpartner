"""Competitions for parameter tuning using the cross-entropy method."""

from __future__ import division

from random import gauss as random_gauss
from math import sqrt

from gomill import compact_tracebacks
from gomill import game_jobs
from gomill import competitions
from gomill import competition_schedulers
from gomill.competitions import (
    Competition, NoGameAvailable, CompetitionError, ControlFileError,
    Player_config)
from gomill.settings import *


def square(f):
    return f * f

class Distribution(object):
    """A multi-dimensional Gaussian probability distribution.

    Instantiate with a list of pairs of floats (mean, variance)

    Public attributes:
      parameters -- the list used to instantiate the distribution

    """
    def __init__(self, parameters):
        self.dimension = len(parameters)
        if self.dimension == 0:
            raise ValueError
        self.parameters = parameters
        self.gaussian_params = [(mean, sqrt(variance))
                                for (mean, variance) in parameters]

    def get_sample(self):
        """Return a random sample from the distribution.

        Returns a list of floats

        """
        return [random_gauss(mean, stddev)
                for (mean, stddev) in self.gaussian_params]

    def get_means(self):
        """Return just the mean from each dimension.

        Returns a list of floats.

        """
        return [mean for (mean, stddev) in self.parameters]

    def format(self):
        return " ".join("%5.2f~%4.2f" % (mean, stddev)
                        for (mean, stddev) in self.parameters)

    def __str__(self):
        return "<distribution %s>" % self.format()

def update_distribution(distribution, elites, step_size):
    """Update a distribution based on the given elites.

    distribution -- Distribution
    elites       -- list of optimiser parameter vectors
    step_size    -- float between 0.0 and 1.0 ('alpha')

    Returns a new distribution

    """
    n = len(elites)
    new_distribution_parameters = []
    for i in range(distribution.dimension):
        v = [e[i] for e in elites]
        elite_mean = sum(v) / n
        elite_var = sum(map(square, v)) / n - square(elite_mean)
        old_mean, old_var = distribution.parameters[i]
        new_mean = (elite_mean * step_size +
                    old_mean * (1.0 - step_size))
        new_var = (elite_var * step_size +
                   old_var * (1.0 - step_size))
        new_distribution_parameters.append((new_mean, new_var))
    return Distribution(new_distribution_parameters)


parameter_settings = [
    Setting('code', interpret_identifier),
    Setting('initial_mean', interpret_float),
    Setting('initial_variance', interpret_float),
    Setting('transform', interpret_callable, default=float),
    Setting('format', interpret_8bit_string, default=None),
    ]

class Parameter_config(Quiet_config):
    """Parameter (ie, dimension) description for use in control files."""
    # positional or keyword
    positional_arguments = ('code',)
    # keyword-only
    keyword_arguments = tuple(setting.name for setting in parameter_settings
                              if setting.name != 'code')

class Parameter_spec(object):
    """Internal description of a parameter spec from the configuration file.

    Public attributes:
      code             -- identifier
      initial_mean     -- float
      initial_variance -- float
      transform        -- function float -> player parameter
      format           -- string for use with '%'

    """

class Cem_tuner(Competition):
    """A Competition for parameter tuning using the cross-entropy method.

    The game ids are like 'g0#1r3', where 0 is the generation number, 1 is the
    candidate number and 3 is the round number.

    """
    def __init__(self, competition_code, **kwargs):
        Competition.__init__(self, competition_code, **kwargs)
        self.seen_successful_game = False

    def control_file_globals(self):
        result = Competition.control_file_globals(self)
        result.update({
            'Parameter' : Parameter_config,
            })
        return result

    global_settings = (Competition.global_settings +
                       competitions.game_settings + [
        Setting('batch_size', interpret_positive_int),
        Setting('samples_per_generation', interpret_positive_int),
        Setting('number_of_generations', interpret_positive_int),
        Setting('elite_proportion', interpret_float),
        Setting('step_size', interpret_float),
        ])

    special_settings = [
        Setting('opponent', interpret_identifier),
        Setting('parameters',
                interpret_sequence_of_quiet_configs(Parameter_config)),
        Setting('make_candidate', interpret_callable),
        ]

    def parameter_spec_from_config(self, parameter_config):
        """Make a Parameter_spec from a Parameter_config.

        Raises ControlFileError if there is an error in the configuration.

        Returns a Parameter_spec with all attributes set.

        """
        if not isinstance(parameter_config, Parameter_config):
            raise ControlFileError("not a Parameter")

        arguments = parameter_config.resolve_arguments()
        interpreted = load_settings(parameter_settings, arguments)
        pspec = Parameter_spec()
        for name, value in interpreted.iteritems():
            setattr(pspec, name, value)
        if pspec.initial_variance < 0.0:
            raise ValueError("'initial_variance': must be nonnegative")
        try:
            transformed = pspec.transform(pspec.initial_mean)
        except Exception:
            raise ValueError(
                "error from transform (applied to initial_mean)\n%s" %
                (compact_tracebacks.format_traceback(skip=1)))
        if pspec.format is None:
            pspec.format = pspec.code + ":%s"
        try:
            pspec.format % transformed
        except Exception:
            raise ControlFileError("'format': invalid format string")
        return pspec

    def initialise_from_control_file(self, config):
        Competition.initialise_from_control_file(self, config)

        competitions.validate_handicap(
            self.handicap, self.handicap_style, self.board_size)

        if not 0.0 < self.elite_proportion < 1.0:
            raise ControlFileError("elite_proportion out of range (0.0 to 1.0)")
        if not 0.0 < self.step_size < 1.0:
            raise ControlFileError("step_size out of range (0.0 to 1.0)")

        try:
            specials = load_settings(self.special_settings, config)
        except ValueError, e:
            raise ControlFileError(str(e))

        try:
            self.opponent = self.players[specials['opponent']]
        except KeyError:
            raise ControlFileError(
                "opponent: unknown player %s" % specials['opponent'])

        self.parameter_specs = []
        if not specials['parameters']:
            raise ControlFileError("parameters: empty list")
        seen_codes = set()
        for i, parameter_spec in enumerate(specials['parameters']):
            try:
                pspec = self.parameter_spec_from_config(parameter_spec)
            except StandardError, e:
                code = parameter_spec.get_key()
                if code is None:
                    code = i
                raise ControlFileError("parameter %s: %s" % (code, e))
            if pspec.code in seen_codes:
                raise ControlFileError(
                    "duplicate parameter code: %s" % pspec.code)
            seen_codes.add(pspec.code)
            self.parameter_specs.append(pspec)

        self.candidate_maker_fn = specials['make_candidate']

        self.initial_distribution = Distribution(
            [(pspec.initial_mean, pspec.initial_variance)
             for pspec in self.parameter_specs])


    # State attributes (*: in persistent state):
    #  *generation        -- current generation (0-based int)
    #  *distribution      -- Distribution for current generation
    #  *sample_parameters -- optimiser_params
    #                        (list indexed by candidate number)
    #  *wins              -- number of games won
    #                        half a point for a game with no winner
    #                        (list indexed by candidate number)
    #   candidates        -- Players (code attribute is the candidate code)
    #                        (list indexed by candidate number)
    #  *scheduler         -- Group_scheduler (group codes are candidate numbers)
    #
    # These are all reset for each new generation.
    #
    #   seen_successful_game -- bool (per-run state)

    def set_clean_status(self):
        self.generation = 0
        self.distribution = self.initial_distribution
        self.reset_for_new_generation()

    def _set_scheduler_groups(self):
        self.scheduler.set_groups(
            (i, self.batch_size) for i in xrange(self.samples_per_generation)
            )

    # Can bump this to prevent people loading incompatible .status files.
    status_format_version = 0

    def get_status(self):
        return {
            'generation'         : self.generation,
            'distribution'       : self.distribution.parameters,
            'sample_parameters'  : self.sample_parameters,
            'wins'               : self.wins,
            'scheduler'          : self.scheduler,
            }

    def set_status(self, status):
        self.generation = status['generation']
        self.distribution = Distribution(status['distribution'])
        self.sample_parameters = status['sample_parameters']
        self.wins = status['wins']
        self.prepare_candidates()
        self.scheduler = status['scheduler']
        # Might as well notice if they changed the batch_size
        self._set_scheduler_groups()
        self.scheduler.rollback()

    def reset_for_new_generation(self):
        get_sample = self.distribution.get_sample
        self.sample_parameters = [get_sample()
                                  for _ in xrange(self.samples_per_generation)]
        self.wins = [0] * self.samples_per_generation
        self.prepare_candidates()
        self.scheduler = competition_schedulers.Group_scheduler()
        self._set_scheduler_groups()

    def transform_parameters(self, optimiser_parameters):
        l = []
        for pspec, v in zip(self.parameter_specs, optimiser_parameters):
            try:
                l.append(pspec.transform(v))
            except Exception:
                raise CompetitionError(
                    "error from transform for %s\n%s" %
                    (pspec.code, compact_tracebacks.format_traceback(skip=1)))
        return tuple(l)

    def format_engine_parameters(self, engine_parameters):
        l = []
        for pspec, v in zip(self.parameter_specs, engine_parameters):
            try:
                s = pspec.format % v
            except Exception:
                s = "[%s?%s]" % (pspec.code, v)
            l.append(s)
        return "; ".join(l)

    def format_optimiser_parameters(self, optimiser_parameters):
        return self.format_engine_parameters(self.transform_parameters(
            optimiser_parameters))

    @staticmethod
    def make_candidate_code(generation, candidate_number):
        return "g%d#%d" % (generation, candidate_number)

    def make_candidate(self, player_code, engine_parameters):
        """Make a player using the specified engine parameters.

        Returns a game_jobs.Player.

        """
        try:
            candidate_config = self.candidate_maker_fn(*engine_parameters)
        except Exception:
            raise CompetitionError(
                "error from make_candidate()\n%s" %
                compact_tracebacks.format_traceback(skip=1))
        if not isinstance(candidate_config, Player_config):
            raise CompetitionError(
                "make_candidate() returned %r, not Player" %
                candidate_config)
        try:
            candidate = self.game_jobs_player_from_config(
                player_code, candidate_config)
        except Exception, e:
            raise CompetitionError(
                "bad player spec from make_candidate():\n"
                "%s\nparameters were: %s" %
                (e, self.format_engine_parameters(engine_parameters)))
        return candidate

    def prepare_candidates(self):
        """Set up the candidates array.

        This is run for each new generation, and when reloading state.

        Requires generation and sample_parameters to be already set.

        Initialises self.candidates.

        """
        self.candidates = []
        for candidate_number, optimiser_params in \
                enumerate(self.sample_parameters):
            candidate_code = self.make_candidate_code(
                self.generation, candidate_number)
            engine_parameters = self.transform_parameters(optimiser_params)
            self.candidates.append(
                self.make_candidate(candidate_code, engine_parameters))

    def finish_generation(self):
        """Process a generation's results and calculate the new distribution.

        Writes a description of the generation to the history log.

        Updates self.distribution.

        """
        sorter = [(wins, candidate_number)
                  for (candidate_number, wins) in enumerate(self.wins)]
        sorter.sort(reverse=True)
        elite_count = max(1,
            int(self.elite_proportion * self.samples_per_generation + 0.5))
        self.log_history("Generation %s" % self.generation)
        self.log_history("Distribution\n%s" %
                         self.format_distribution(self.distribution))
        self.log_history(self.format_generation_results(sorter, elite_count))
        self.log_history("")
        elite_samples = [self.sample_parameters[index]
                         for (wins, index) in sorter[:elite_count]]
        self.distribution = update_distribution(
            self.distribution, elite_samples, self.step_size)

    def get_player_checks(self):
        engine_parameters = self.transform_parameters(
            self.initial_distribution.get_sample())
        candidate = self.make_candidate('candidate', engine_parameters)
        result = []
        for player in [candidate, self.opponent]:
            check = game_jobs.Player_check()
            check.player = player
            check.board_size = self.board_size
            check.komi = self.komi
            result.append(check)
        return result

    def get_game(self):
        if self.scheduler.nothing_issued_yet():
            self.log_event("\nstarting generation %d" % self.generation)

        candidate_number, round_id = self.scheduler.issue()
        if candidate_number is None:
            return NoGameAvailable

        candidate = self.candidates[candidate_number]

        job = game_jobs.Game_job()
        job.game_id = "%sr%d" % (candidate.code, round_id)
        job.game_data = (candidate_number, candidate.code, round_id)
        job.player_b = candidate
        job.player_w = self.opponent
        job.board_size = self.board_size
        job.komi = self.komi
        job.move_limit = self.move_limit
        job.handicap = self.handicap
        job.handicap_is_free = (self.handicap_style == 'free')
        job.use_internal_scorer = (self.scorer == 'internal')
        job.internal_scorer_handicap_compensation = \
            self.internal_scorer_handicap_compensation
        job.sgf_event = self.competition_code
        job.sgf_note = ("Candidate parameters: %s" %
                        self.format_optimiser_parameters(
                            self.sample_parameters[candidate_number]))
        return job

    def process_game_result(self, response):
        self.seen_successful_game = True
        candidate_number, candidate_code, round_id = response.game_data
        self.scheduler.fix(candidate_number, round_id)
        gr = response.game_result
        assert candidate_code in (gr.player_b, gr.player_w)

        # Counting jigo or no-result as half a point for the candidate
        if gr.winning_player == candidate_code:
            self.wins[candidate_number] += 1
        elif gr.winning_player is None:
            self.wins[candidate_number] += 0.5

        if self.scheduler.all_fixed():
            self.finish_generation()
            self.generation += 1
            if self.generation != self.number_of_generations:
                self.reset_for_new_generation()

    def process_game_error(self, job, previous_error_count):
        ## If the very first game to return a response gives an error, halt.
        ## Otherwise, retry once and halt on a second failure.
        stop_competition = False
        retry_game = False
        if (not self.seen_successful_game) or (previous_error_count > 0):
            stop_competition = True
        else:
            retry_game = True
        return stop_competition, retry_game


    def format_distribution(self, distribution):
        """Pretty-print a distribution.

        Returns a string.

        """
        return "%s\n%s" % (
            self.format_optimiser_parameters(distribution.get_means()),
            distribution.format())

    def format_generation_results(self, ordered_samples, elite_count):
        """Pretty-print the results of a single generation.

        ordered_samples -- list of pairs (wins, candidate number)
        elite_count     -- number of samples to mark as elite

        """
        result = []
        for i, (wins, candidate_number) in enumerate(ordered_samples):
            opt_parameters = self.sample_parameters[candidate_number]
            result.append(
                "%s%s %s %3d" %
                (self.make_candidate_code(self.generation, candidate_number),
                 "*" if i < elite_count else " ",
                 self.format_optimiser_parameters(opt_parameters),
                 wins))
        return "\n".join(result)

    def write_static_description(self, out):
        def p(s):
            print >>out, s
        p("CEM tuning event: %s" % self.competition_code)
        if self.description:
            p(self.description)
        p("board size: %s" % self.board_size)
        p("komi: %s" % self.komi)

    def write_screen_report(self, out):
        print >>out, "generation %d" % self.generation
        print >>out
        print >>out, "wins from current samples:\n%s" % self.wins
        print >>out
        if self.generation == self.number_of_generations:
            print >>out, "final distribution:"
        else:
            print >>out, "distribution for generation %d:" % self.generation
        print >>out, self.format_distribution(self.distribution)

    def write_short_report(self, out):
        self.write_static_description(out)
        self.write_screen_report(out)

    write_full_report = write_short_report

