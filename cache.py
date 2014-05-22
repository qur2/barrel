from django.core.cache import cache as default_cache_engine
from functools import partial, wraps
from itertools import islice
import logging


logger = logging.getLogger(__name__)
#  empty is here to disambiguate None and inexisting values from the cache
empty = object()


def cache(duration=10, engine=default_cache_engine, keygen=None, need_cache=lambda x: True):
    def outer(fn):
        @wraps(fn)
        def inner(cls, *args, **kwargs):
            args = list(args)  # needs casting to list in case there is a need to append
            # beware that dictionaries are not ordered, and we need an injective function to generate keys
            for key in sorted(kwargs):
                args.append(kwargs[key])
            cache_key = (keygen or call_key)(cls, fn, args)
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


def memcached_safe(string):
    """Strip space and make sure there is no utf8 characters left, required
    to keep memcache happy.
    """
    return string.replace(' ', '_').decode('utf8').encode('ascii', 'replace')


def call_key(cls, fn, args, sep=','):
    """Generate a cache key base on a method signature."""
    return '%s.%s(%s)' % (cls.__name__, fn.__name__, memcached_safe(sep.join((map(unicode, args)))))


def reduced_call_key(cls, fn, args, i=0, j=None):
    """Helper to generate a string based on sliced call arguments.
    Useful to ignore the token, for example.
    """
    return call_key(cls, fn, islice(args, i, j))


def sliced_call_args(i, j=None):
    """Helper to get a configured call_key."""
    return partial(reduced_call_key, i=i, j=j)
