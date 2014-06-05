from functools import partial, wraps
from itertools import islice
import logging


logger = logging.getLogger(__name__)
#  empty is here to disambiguate None and inexisting values from the cache
empty = object()


class Engines(object):
    """Helper class to hold engines the cache decorator shoud know about.
    To register the engines, simply call `Engines.configure()` with some `kwargs`.
    """
    def configure(self, **kwargs):
        """`kwargs` is a dictionary of `engine_name:engine`.
        """
        for key, engine in kwargs.iteritems():
            setattr(self, key, engine)

    def __getitem__(self, key):
        """Implements dictionary access for easy getting.
        Note that it never raises, and leaves the decision to do so to the caller.
        """
        return getattr(self, key, None)


engines = Engines()


def cache(duration=10, keygen=None, need_cache=lambda x: True, engine_name='barrel'):
    """Decorator used to cache the return value of a function.
    If the engine is not available, a warning is issued but everything will run smoothly,
    wihtout any cache.

    :param duration: The caching duration
    :type duration: int
    :param keygen: The key generator function. Defaults to `call_key`.
    :type keygen: Callable
    :param need_cache: Callable that checks if the value needs to be cached or not.
    :type need_cache: Callable
    :param engine_name: The cache engine name to work with. It will be fetched from the `barrel.cache.engines`.
    :type engine_name: String, the engine itself should ducktype `django.core.cache.BaseCache`
    :returns: Decorated function, which tries to hit the cache before running the inner function.
                If the engine is not properly configured, then the inner function is not decorated.
    """
    def outer(fn):
        engine = engines[engine_name]
        if not engine:
            logging.warning("cache not properly configured for %s" % fn)
            return fn

        @wraps(fn)
        def inner(cls, *args, **kwargs):
            # needs casting to list in case there is a need to append
            keygen_args = list(args)
            # beware that dictionaries are not ordered, and we need an injective function to generate keys
            for key in sorted(kwargs):
                keygen_args.append(kwargs[key])
            cache_key = (keygen or call_key)(cls, fn, keygen_args)
            cache_val = engine.get(cache_key, empty)
            if cache_val == empty:
                cache_val = fn(cls, *args, **kwargs)
                if need_cache(cache_val):
                    logging.info("cache miss: %s" % cache_key)
                    engine.set(cache_key, cache_val)
                else:
                    logging.info("no cache: %s" % cache_key)
            else:
                logging.info("cache hit: %s" % cache_key)
            return cache_val
        return inner
    return outer


def clear_cache(keygen, engine_name='barrel'):
    """Decorator used to clear some cache keys.
    If the engine is not available, a warning is issued but everything will run smoothly,
    wihtout any cache clearing ability.

    :param keygen: The key generator function. It expects a bunch pf keys at once.
    :type keygen: Callable that returns a list or a tuple
    :param engine_name: The caching engine to work with. Defaults to django's default engine.
    :type engine_name: String, the engine itself should ducktype `django.core.cache.BaseCache`
    :returns: Decorated function, which tries to clear some cache entries before running the inner function.
                If the engine is not properly configured, then the inner function is not decorated.
    """
    def outer(fn):
        engine = engines[engine_name]
        if not engine:
            logging.warning("cache not properly configured for %s" % fn)
            return fn

        @wraps(fn)
        def inner(cls, *args, **kwargs):
            # Prepare the args for the cache key generator.
            keygen_args = list(args)
            # Beware of the order in kwargs.
            for key in sorted(kwargs):
                keygen_args.append(kwargs[key])
            # Clearing cache does not need `cls` and `fn` since it's targeting
            # at clearing somebody else's cache.
            cache_keys = keygen(*keygen_args)
            engine.delete_many(cache_keys)
            logging.info("cache clear: %s" % repr(cache_keys))
            return fn(cls, *args, **kwargs)
        return inner
    return outer


def memcached_safe(string):
    """Strip spaces, required to keep memcache happy."""
    return string.replace(' ', '_')


def call_key(cls, fn, args, sep=','):
    """Generate a cache key base on function call arguments."""
    return '%s.%s(%s)' % (cls.__name__, fn.__name__, memcached_safe(sep.join((map(unicode, args)))))


def reduced_call_key(cls, fn, args, i=0, j=None):
    """Helper to generate a string based on sliced call arguments.
    Useful to ignore the token, for example.
    """
    return call_key(cls, fn, islice(args, i, j))


def sliced_call_args(i, j=None):
    """Helper to get a configured call_key."""
    return partial(reduced_call_key, i=i, j=j)
