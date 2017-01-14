"""Support for describing configurable values."""

import re
import shlex

__all__ = ['Setting', 'allow_none', 'load_settings',
           'Config_proxy', 'Quiet_config',
           'interpret_any', 'interpret_bool',
           'interpret_int', 'interpret_positive_int', 'interpret_float',
           'interpret_8bit_string', 'interpret_identifier',
           'interpret_as_utf8', 'interpret_as_utf8_stripped',
           'interpret_colour', 'interpret_enum', 'interpret_callable',
           'interpret_shlex_sequence',
           'interpret_sequence', 'interpret_sequence_of',
           'interpret_sequence_of_quiet_configs',
           'interpret_map', 'interpret_map_of',
           'clean_string',
           ]

def interpret_any(v):
    return v

def interpret_bool(b):
    if b is not True and b is not False:
        raise ValueError("invalid True/False value")
    return b

def interpret_int(i):
    if not isinstance(i, int) or isinstance(i, long):
        raise ValueError("invalid integer")
    return i

def interpret_positive_int(i):
    if not isinstance(i, int) or isinstance(i, long):
        raise ValueError("invalid integer")
    if i <= 0:
        raise ValueError("must be positive integer")
    return i

def interpret_float(f):
    if isinstance(f, float):
        return f
    if isinstance(f, int) or isinstance(f, long):
        return float(f)
    raise ValueError("invalid float")

def interpret_8bit_string(s):
    if isinstance(s, str):
        result = s
    elif isinstance(s, unicode):
        try:
            result = s.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError("non-ascii character in unicode string")
    else:
        raise ValueError("not a string")
    if '\0' in s:
        raise ValueError("contains NUL")
    return result

def interpret_as_utf8(s):
    if isinstance(s, str):
        try:
            s.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("not a valid utf-8 string")
        return s
    if isinstance(s, unicode):
        return s.encode("utf-8")
    if s is None:
        return ""
    raise ValueError("invalid string")

def interpret_as_utf8_stripped(s):
    return interpret_as_utf8(s).strip()


def clean_string(s):
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", s)

# NB, tuners use '#' in player codes
_identifier_re = re.compile(r"\A[-!$%&*+-.:;<=>?^_~a-zA-Z0-9]*\Z")

def interpret_identifier(s):
    if isinstance(s, unicode):
        try:
            s = s.encode("ascii")
        except UnicodeEncodeError:
            raise ValueError(
                "contains forbidden character: %s" %
                clean_string(s.encode("ascii", "replace")))
    elif not isinstance(s, str):
        raise ValueError("not a string")
    if not s:
        raise ValueError("empty string")
    if not _identifier_re.search(s):
        raise ValueError("contains forbidden character: %s" % clean_string(s))
    return s

_colour_dict = {
    'b' : 'b',
    'black' : 'b',
    'w' : 'w',
    'white' : 'w',
    }

def interpret_colour(s):
    if isinstance(s, basestring):
        try:
            return _colour_dict[s.lower()]
        except KeyError:
            pass
    raise ValueError("invalid colour")

def interpret_enum(*values):
    def interpreter(value):
        if value not in values:
            raise ValueError("unknown value")
        return value
    return interpreter

def interpret_callable(c):
    if not callable(c):
        raise ValueError("invalid callable")
    return c

def interpret_shlex_sequence(v):
    """Interpret a sequence of 'shlex' tokens.

    If v is a string, calls shlex.split() on it.

    Otherwise, treats it as a list of strings.

    Rejects empty sequences.

    """
    if isinstance(v, basestring):
        result = shlex.split(interpret_8bit_string(v))
    else:
        try:
            l = interpret_sequence(v)
        except ValueError:
            raise ValueError("not a string or a sequence")
        try:
            result = [interpret_8bit_string(s) for s in l]
        except ValueError, e:
            raise ValueError("element %s" % e)
    if not result:
        raise ValueError("empty")
    return result


def interpret_sequence(l):
    """Interpret a list-like object.

    Accepts any iterable and returns a list.

    """
    try:
        l = list(l)
    except Exception:
        raise ValueError("not a sequence")
    return l

def interpret_sequence_of(item_interpreter):
    """Make an interpreter for list-like objects.

    The interpreter behaves like interpret_list, and additionally calls
    item_interpreter for each list item.

    """
    def interpreter(value):
        l = interpret_sequence(value)
        for i, v in enumerate(l):
            try:
                l[i] = item_interpreter(v)
            except ValueError, e:
                raise ValueError("item %s: %s" % (i, e))
        return l
    return interpreter

def interpret_sequence_of_quiet_configs(cls, allow_simple_values=False):
    """Make an interpreter for sequences of a given Quiet_config.

    If 'allow_simple_values' is true, any value which isn't an instance of 'cls'
    will be used (as a single positional parameter) to instantiate a 'cls'
    instance.

    """
    def interpret(v):
        if not isinstance(v, cls):
            if allow_simple_values:
                v = cls(v)
            else:
                raise ValueError("not a %s" % cls.get_type_name())
        return v
    return interpret_sequence_of(interpret)

def interpret_map(m):
    """Interpret a map-like object.

    Accepts anything that dict() accepts for its first argument.

    Returns a list of pairs (key, value).

    """
    try:
        d = dict(m)
    except Exception:
        raise ValueError("not a map")
    return d.items()

def interpret_map_of(key_interpreter, value_interpreter):
    """Make an interpreter for map-like objects.

    The interpreter behaves like interpret_map, and additionally calls
    key_interpreter for each key and value_interpreter for each value.

    Sorts the result by key.

    """
    def interpreter(m):
        result = []
        for key, value in interpret_map(m):
            try:
                new_key = key_interpreter(key)
            except ValueError, e:
                raise ValueError("bad key: %s" % e)
            try:
                new_value = value_interpreter(value)
            except ValueError, e:
                # we assume validated keys are fit to print
                raise ValueError("bad value for '%s': %s" % (new_key, e))
            result.append((new_key, new_value))
        # We assume validated items are suitable for sorting
        return sorted(result)
    return interpreter

def allow_none(fn):
    """Make a new interpreter from an existing one, which maps None to None."""
    def sub(v):
        if v is None:
            return None
        return fn(v)
    return sub

_nodefault = object()

class Setting(object):
    """Describe a single setting.

    Instantiate with:
      setting name
      interpreter function
    optionally:
      default value, or
      defaultmaker -- callable creating the default value

    """
    def __init__(self, name, interpreter,
                 default=_nodefault, defaultmaker=None):
        self.name = name
        self.interpreter = interpreter
        self.default = default
        self.defaultmaker = defaultmaker

    def get_default(self):
        """Return the default value for this setting.

        Raises KeyError if there isn't one.

        """
        if self.default is not _nodefault:
            return self.default
        if self.defaultmaker is not None:
            return self.defaultmaker()
        raise KeyError

    def interpret(self, value):
        """Validate the value and normalise if necessary.

        Returns the normalised value (usually unchanged).

        Raises ValueError with a description if the value is invalid.

        """
        try:
            return self.interpreter(value)
        except ValueError, e:
            raise ValueError("'%s': %s" % (self.name, e))

def load_settings(settings, config, apply_defaults=True, allow_missing=False):
    """Read settings values from configuration.

    settings       -- list of Settings
    config         -- dict containing the values to be read
    apply_defaults -- bool (default true)
    allow_missing  -- bool (default false)

    Returns a dict: setting name -> interpreted value

    Handling of values which aren't present in 'config':
      - if apply_defaults is true, the setting's default is substituted
      - if apply_defaults is false or the setting has no default:
        - if allow_missing is true, omits the setting from the returned dict
        - if allow_missing is false, raises ValueError

    Resolves Config_proxy objects (see below)

    Raises ValueError with a description if a value can't be interpreted.

    """
    result = {}
    for setting in settings:
        try:
            try:
                v = config[setting.name]
                if isinstance(v, Config_proxy):
                    try:
                        v = v.resolve()
                    except ValueError, e:
                        raise ValueError("'%s': %s" % (setting.name, e))
                # May propagate ValueError
                v = setting.interpret(v)
            except KeyError:
                if apply_defaults:
                    v = setting.get_default()
                else:
                    raise
        except KeyError:
            if allow_missing:
                continue
            else:
                raise ValueError("'%s' not specified" % setting.name)
        result[setting.name] = v
    return result

class Config_proxy(object):
    """Class proxy for use in control files.

    To use this, define a subclass, giving it the following class attribute:
      underlying -- the underlying class

    Then in the control file, the proxy can be used anywhere which will be
    interpreted using the settings mechanism. An instance of the underlying
    class will be created by load_settings and then passed to the interpret
    function as usual.

    Any errors from the underlying class's __init__ will be raised as ValueError
    from load_settings().

    """
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def resolve(self):
        try:
            return self.underlying(*self.args, **self.kwargs)
        except Exception, e:
            raise ValueError("invalid parameters for %s:\n%s" %
                             (self.__class__.__name__, e))


class Quiet_config(object):
    """Configuration object for use in control files.

    At instantiation time, this just records its arguments, so they can be
    validated later.

    """
    # These may be specified as positional or keyword
    positional_arguments = ()
    # These are keyword-only
    keyword_arguments = ()
    # Used by interpret_sequence_of_quiet_configs
    type_name = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def get_type_name(cls):
        """Return a name for the config type, for use in error messages."""
        if cls.type_name is not None:
            return cls.type_name
        return cls.__name__.partition("_config")[0]

    def resolve_arguments(self):
        """Combine positional and keyword arguments.

        Returns a dict: argument name -> value

        Raises ValueError if the arguments are invalid.

        Checks for:
         - too many positional arguments
         - unknown keyword arguments
         - argument specified as both positional and keyword

        Unspecified arguments (either positional or keyword) are not considered
        errors; they're just not included in the result.

        """
        result = {}
        if len(self.args) > len(self.positional_arguments):
            raise ValueError("too many positional arguments")
        for name, val in zip(self.positional_arguments, self.args):
            result[name] = val
        allowed = set(self.positional_arguments + self.keyword_arguments)
        for name, val in sorted(self.kwargs.iteritems()):
            if name not in allowed:
                raise ValueError("unknown argument '%s'" % name)
            if name in result:
                raise ValueError(
                    "%s specified as both positional and keyword argument" %
                    name)
            result[name] = val
        return result

    def get_key(self):
        """Retrieve the first positional argument, if possible.

        Does the right thing if it was specified as a keyword argument.

        Returns None if there isn't one.

        """
        try:
            if self.args:
                return self.args[0]
            return self.kwargs[self.positional_arguments[0]]
        except LookupError:
            return None

