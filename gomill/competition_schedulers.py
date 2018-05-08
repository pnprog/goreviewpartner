"""Schedule games in competitions.

These schedulers are used to keep track of the ids of games which have been
started, and which have reported their results.

They provide a mechanism to reissue ids of games which were in progress when an
unclean shutdown occurred.

All scheduler classes are suitable for pickling.

"""

class Simple_scheduler(object):
    """Schedule a single sequence of games.

    The issued tokens are integers counting up from zero.

    Public attributes (treat as read-only):
      issued -- int
      fixed  -- int

    """
    def __init__(self):
        self.next_new = 0
        self.outstanding = set()
        self.to_reissue = set()
        self.issued = 0
        self.fixed = 0
        #self._check_consistent()

    def _check_consistent(self):
        assert self.issued == \
            self.next_new - len(self.to_reissue)
        assert self.fixed == \
            self.next_new - len(self.outstanding) - len(self.to_reissue)

    def __getstate__(self):
        return (self.next_new, self.outstanding, self.to_reissue)

    def __setstate__(self, state):
        (self.next_new, self.outstanding, self.to_reissue) = state
        self.issued = self.next_new - len(self.to_reissue)
        self.fixed = self.issued - len(self.outstanding)
        #self._check_consistent()

    def issue(self):
        """Choose the next game to start.

        Returns an integer 'token'.

        """
        if self.to_reissue:
            result = min(self.to_reissue)
            self.to_reissue.discard(result)
        else:
            result = self.next_new
            self.next_new += 1
        self.outstanding.add(result)
        self.issued += 1
        #self._check_consistent()
        return result

    def fix(self, token):
        """Note that a game's result has been reliably stored."""
        self.outstanding.remove(token)
        self.fixed += 1
        #self._check_consistent()

    def rollback(self):
        """Make issued-but-not-fixed tokens available again."""
        self.issued -= len(self.outstanding)
        self.to_reissue.update(self.outstanding)
        self.outstanding = set()
        #self._check_consistent()


class Group_scheduler(object):
    """Schedule multiple lists of games in parallel.

    This schedules for a number of _groups_, each of which may have a limit on
    the number of games to play. It schedules from the group (of those which
    haven't reached their limit) with the fewest issued games, with smallest
    group code breaking ties.

    group codes might be ints or short strings
    (any sortable, pickleable and hashable object should do).

    The issued tokens are pairs (group code, game number), with game numbers
    counting up from 0 independently for each group code.

    """
    def __init__(self):
        self.allocators = {}
        self.limits = {}

    def __getstate__(self):
        return (self.allocators, self.limits)

    def __setstate__(self, state):
        (self.allocators, self.limits) = state

    def set_groups(self, group_specs):
        """Set the groups to be scheduled.

        group_specs -- iterable of pairs (group code, limit)
          limit -- int or None

        You can call this again after the first time. The limits will be set to
        the new values. Any existing groups not in the list are forgotten.

        """
        new_allocators = {}
        new_limits = {}
        for group_code, limit in group_specs:
            if group_code in self.allocators:
                new_allocators[group_code] = self.allocators[group_code]
            else:
                new_allocators[group_code] = Simple_scheduler()
            new_limits[group_code] = limit
        self.allocators = new_allocators
        self.limits = new_limits

    def issue(self):
        """Choose the next game to start.

        Returns a pair (group code, game number)

        Returns (None, None) if all groups have reached their limit.

        """
        groups = [
            (group_code, allocator.issued, self.limits[group_code])
            for (group_code, allocator) in self.allocators.iteritems()
            ]
        available = [
            (issue_count, group_code)
            for (group_code, issue_count, limit) in groups
            if limit is None or issue_count < limit
            ]
        if not available:
            return None, None
        _, group_code = min(available)
        return group_code, self.allocators[group_code].issue()

    def fix(self, group_code, game_number):
        """Note that a game's result has been reliably stored."""
        self.allocators[group_code].fix(game_number)

    def rollback(self):
        """Make issued-but-not-fixed tokens available again."""
        for allocator in self.allocators.itervalues():
            allocator.rollback()

    def nothing_issued_yet(self):
        """Say whether nothing has been issued yet."""
        return all(allocator.issued == 0
                   for allocator in self.allocators.itervalues())

    def all_fixed(self):
        """Check whether all groups have reached their limits.

        This returns true if all groups have limits, and each group has as many
        _fixed_ tokens as its limit.

        """
        return all(allocator.fixed >= self.limits[g]
                   for (g, allocator) in self.allocators.iteritems())
