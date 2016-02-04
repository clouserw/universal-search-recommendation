import hashlib
import pickle
from functools import wraps
from inspect import getargspec

from wrapt import ObjectProxy

from app.memcached import memcached


class MemorizedObject(ObjectProxy):
    """
    Thin wrapper around any memorized objects, adding attributes indicating
    the object's cache key and whether or not it was returned from cache.
    Mostly used to make logging and testing easier.
    """
    def __init__(self, wrapped):
        super(MemorizedObject, self).__init__(wrapped)
        self._self_from_cache = False
        self._self_cache_key = None

    def __reduce__(self):
        """
        Makes MemorizedObject instances picklable, if the wrapped object is
        picklable itself.
        """
        return type(self), (self.__wrapped__,)

    def __repr__(self):
        """
        When inspecting MemorizedObject instances in a REPL, we want to show
        the wrapped object, rather than <MemorizedObject ...>
        """
        return repr(self.__wrapped__)

    @property
    def from_cache(self):
        return self._self_from_cache

    @from_cache.setter
    def from_cache(self, value):
        if not isinstance(value, bool):
            raise RuntimeError('MemorizedObject().from_cache must be a bool.')
        self._self_from_cache = value

    @property
    def cache_key(self):
        return self._self_cache_key

    @cache_key.setter
    def cache_key(self, value):
        if not isinstance(value, str):
            raise RuntimeError('MemorizedObject().cache_key must be a str.')
        self._self_cache_key = value


class memorize(object):
    """
    Method decorator to memoize that method in memcached based on the name
    of the method, the name of the class to whom that method belongs, and the
    call signature.

    Example:

    class Book(object):
        def __init__(self, title, author):
            self.title = title
            self.author = author

        @memorize
        def attr(self, key):
            return getattr(self, key)

    gow = Book('Grapes of Wrath', 'John Steinbeck')

    title = gow.attr('title')    # 'Grapes of Wrath'
    title.from_cache             # False
    title.cache_key              # 'memorize_c952a93846d07a04f7bf127b7b640ca1'

    title_2 = gow.attr('title')  # 'Grapes of Wrath'
    title_2.from_cache           # True
    title_2.cache_key            # 'memorize_c952a93846d07a04f7bf127b7b640ca1'

    author = gow.attr('author')  # 'John Steinbeck'
    author.from_cache            # False
    author.cache_key             # 'memorize_cd2db0e4dc383ea0c5643ce6478612a3'
    """
    def __init__(self, prefix='memorized', ttl=0):
        self.prefix = prefix
        self.ttl = ttl

    def __call__(self, fn):
        """
        Generate the cache key from the call signature. If there's a memcached
        match, don't execute the function at all, instead return the memoized
        value directly from memcached.
        """
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = self._make_cache_key(fn, args, kwargs)
            value = memcached.get(key)
            if value:
                value = MemorizedObject(value)
                value.from_cache = True
            else:
                value = fn(*args, **kwargs)
                memcached.set(key, value, time=self.ttl)
                value = MemorizedObject(value)
            value.cache_key = key
            return value
        return wrapper

    def _make_cache_key(self, fn, args, kwargs):
        """
        Generate a cache key from 5 data points:

        - The prefix specified when initializing the decorator.
        - The name of the class whose method to which the decorator was
          applied.
        - The name of the method to which the decorator was applied.
        - The decorator's arguments, excluding `self` if applicable.
        - The decorator's keyword arugments.

        This requires all args and kwargs to be picklable.
        """
        fn_args = getargspec(fn).args
        if fn_args and fn_args[0] == 'self' and len(args) == len(fn_args):
            args = args[1:]
        pickled = pickle.dumps([fn.__name__, args, kwargs])
        return '%s_%s' % (self.prefix, hashlib.sha256(pickled).hexdigest())
