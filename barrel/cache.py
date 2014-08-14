from collections import namedtuple
import contextlib
import logging


logger = logging.getLogger(__name__)
#  empty is here to disambiguate None and inexisting values from the cache
empty = object()


def call_key(cls_or_module, fn, args, sep=','):
    """Generate a cache key base on function call arguments."""
    return '%s.%s(%s)' % (cls_or_module, fn, sep.join(map(unicode, args)).replace(' ', '_'))


needs_cache_always = lambda x: True


class Cacher(namedtuple('Cacher', 'engine, keygen, needs_cache, duration')):
    def __call__(self, fn, *args, **kwargs):
        """Handles caching for a function call. It builds the cache key using the instance `keygen`.
        With the instance `needs_cache` callable, the cache may be discarded.
        """
        # needs casting to list in case there is a need to append
        keygen_args = list(args)
        # beware that dictionaries are not ordered, and
        # we need an injective function to generate keys
        for key in sorted(kwargs):
            keygen_args.append(kwargs[key])
        cls_or_module = fn.im_self.__name__ if hasattr(fn, 'im_self') else fn.__module__
        cache_key = self.keygen(cls_or_module, fn.__name__, keygen_args)
        cache_val = self.engine.get(cache_key, empty)
        if cache_val is empty:
            cache_val = fn(*args, **kwargs)
            if self.needs_cache(cache_val):
                logger.info("cache miss: %s" % cache_key)
                self.engine.set(cache_key, cache_val, self.duration)
            else:
                logger.info("no cache: %s" % cache_key)
        else:
            logger.info("cache hit: %s" % cache_key)
        return cache_val


class CacheClearer(namedtuple('Cacher', 'engine, keygen')):
    """Clears cache for given arguments. It builds multiple cache keys using the instance `keygen`
    and delete them all from the cache. This means that the `keygen` is expected to return a
    collection of keys at once.
    """
    def __call__(self, *args, **kwargs):
        # needs casting to list in case there is a need to append
        keygen_args = list(args)
        # beware that dictionaries are not ordered, and
        # we need an injective function to generate keys
        for key in sorted(kwargs):
            keygen_args.append(kwargs[key])
        # usually, clearing cache is intended for other keys,
        # so make no assumption from the proxied function.
        cache_keys = self.keygen(*keygen_args)
        self.engine.delete_many(cache_keys)
        logger.info("cache clear: %s" % repr(cache_keys))


def get_cacher(engine, keygen, needs_cache, duration):
    return Cacher(engine, keygen, needs_cache, duration)


def get_cache_clearer(engine, keygen):
    return CacheClearer(engine, keygen)


@contextlib.contextmanager
def caching(engine, keygen=call_key, needs_cache=needs_cache_always, duration=10):
    cacher = get_cacher(engine, keygen, needs_cache, duration)
    try:
        yield cacher
    finally:
        pass


@contextlib.contextmanager
def cache_clearing(engine, keygen=call_key):
    cacher = get_cache_clearer(engine, keygen)
    try:
        yield cacher
    finally:
        pass
