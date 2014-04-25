from django.core.cache import cache as default_cache_engine
from functools import wraps
from itertools import chain
import logging


logger = logging.getLogger(__name__)
#  empty is here to disambiguate None and inexisting values from the cache
empty = object()


def memoize(duration=10, engine=default_cache_engine, key=None):
    def outer(fn):
        @wraps(fn)
        def inner(cls, *args, **kwargs):
            if not key:
                # cache_key = '%s.%s:%s(%s, %s)' % (cls.__module__, cls.__name__, fn.__name__, args, kwargs)
                # strip space from joined args and make sure there is no utf8 characters left
                suffix = ','.join(chain(args, kwargs.itervalues())).replace(' ', '_').decode('utf8').encode('ascii', 'replace')
                cache_key = '%s.%s(%s)' % (cls.__name__, fn.__name__, suffix)
            cache_val = engine.get(cache_key, empty)
            if cache_val == empty:
                logging.info("cache miss: %s" % cache_key)
                cache_val = fn(cls, *args, **kwargs)
                engine.set(cache_key, cache_val)
            else:
                logging.info("cache hit: %s" % cache_key)
            return cache_val
        return inner
    return outer
