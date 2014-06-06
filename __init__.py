"""This module enables model-like encapsulation of big dict structure (like JSON data).

    When I die I want to decompose in a barrel of porter and have it served in all the pubs in Dublin.
    J. P. Donleavy

The goal is to *not* map the underlying dict but just wrap it in a programmer-friendly structure
to allow attribute-like access and field aliasing.

Field aliasing enables to virtually:

* change key names
* modify the apparent structure of the dict
"""
from .signals import class_ready
from .utils import import_module
from iso8601 import iso8601
import inspect
from holon import Reaktor
# from money import Money


__all__ = [
    'config', 'Field', 'EmbeddedStoreField', 'Store', 'CollectionStore',
    'BooleanField', 'DateField', 'IntField', 'FloatField', 'LongIntField', 'SplitField',
]


_reaktor_config = {
    'host': 'skins-staging-reaktor',
    'port': 8080,
    'path': '/api/1.50.31/rpc',
    'ssl': False,
    'user_agent': 'hreaktor',
    'connect_timeout': 20,
    'run_timeout': 40,
    'do_retry': False,
    'retry_sleep': 1.,
    'communication_error_class': 'reaktor.ReaktorIOError',
    'http_service': 'services.httplib.HttpLibHttpService',
}


# default app configuration
_default_config = {
    'CACHE_ENGINES': {},
    'DEFAULT_CACHE_ENGINE_NAME': 'barrel',
    # this setting should be overridden
    'REAKTOR': Reaktor(**_reaktor_config),
}

class Config(object):
    """Small helper class that stores app configuration."""
    def __init__(self, config=None):
        self.config = config or {}

    def configure(self, **kwargs):
        self.config.update(kwargs)

    def __getattribute__(self, name):
        get_attr = super(Config, self).__getattribute__
        config = get_attr('config')
        config_value = config.get(name, _default_config.get(name))
        if config_value is not None:
            return config_value
        return get_attr(name)

# app configuration
config = Config()


# storage for fields that need to be initialized later
pending_fields = {}


def resolve_pending_fields(sender):
    """Signal handler that sets `store_class` and `store` field attributes."""
    key = '.'.join([sender.__module__, sender.__name__])
    for field in pending_fields.pop(key, []):
        field.store_class = sender
        # not sure if the following needed
        # since `__getattribute__` uses the `store_class` attribute of a field
        # that we've already set the line above
        if field.is_array:
            field.store = CollectionStore(sender)
        else:
            field.store = sender()

class_ready.connect(resolve_pending_fields)


class StoreMeta(type):
    """Metaclass that farms and gather `Field`-type attributes in a new `fields`
    attributes. This `fields` attribute later helps to easily identify if an
    attribute is `Field` typed without iterating through all attributes.
    """
    def __new__(cls, name, bases, attrs):
        fields = {}
        for k, f in attrs.iteritems():
            if isinstance(f, (Field,)):
                fields[k] = f
        # adding parents' fields
        for parent in bases:
            if hasattr(parent, 'fields'):
                fields.update(parent.fields)
        attrs['fields'] = fields
        cls = super(StoreMeta, cls).__new__(cls, name, bases, attrs)
        # send `class_ready` signal
        class_ready.send(cls)
        return cls


def simple_get(key, dictionary):
    return dictionary[key]


def simple_set(key, dictionary, value):
    dictionary[key] = value


def deep_get(deep_key, dictionary, sep=':'):
    """Fetches through multiple dictionary levels, splitting
    the compound key using the specified separator.
    """
    keys = deep_key.split(sep)
    while keys:
        dictionary = dictionary[keys.pop(0)]
    return dictionary


def deep_set(deep_key, dictionary, value, sep=':'):
    """Sets through multiple dictionary levels, splitting
    the compound key using the specified separator.
    """
    keys = deep_key.split(sep)
    key = keys.pop()
    while keys:
        dictionary = dictionary[keys.pop(0)]
    dictionary[key] = value


class Field(object):
    """Base field class for dict datastore handling."""

    def __init__(self, target, target_sep=':', default=None):
        self.target = target
        self.target_sep = target_sep
        self.default = default

    def get(self, dct):
        try:
            if self.target and self.target_sep in self.target:
                return deep_get(self.target, dct, self.target_sep)
            else:
                return simple_get(self.target, dct)
        except KeyError, err:
            if self.default is not None:
                return self.default
            else:
                raise err

    def set(self, dct, value):
        if self.target and self.target_sep in self.target:
            deep_set(self.target, dct, self.target_sep, value)
        else:
            simple_set(self.target, dct, value)

    def __str__(self):
        return "<%s.%s target=%s>" % (self.__module__, self.__class__.__name__, self.target)


class EmbeddedStoreField(Field):
    """Field that enables to embed a one or multiple dict datastores.
    By setting the target to `False`, it's also possible to create a virtual
    datastore, i.e. adding a level that doesn't exist in the datastore.
    """
    def __init__(self, target, store_class, is_array=False):
        # it is possible to give the reference to the store class
        # as a string - python path, or as a class
        if isinstance(store_class, basestring):
            path = store_class.split('.')
            # it is dotted path
            if len(path) > 1:
                # key that we might use to resolve the class, once it's ready
                key = store_class
                # module that we will try to import
                module_path = '.'.join(path[:-1])
                # class that we will try to import
                store_class = path[-1]
            # it is the class name from the module of the `EmbeddedStoreField` caller
            else:
                # get the module of the caller
                frm = inspect.stack()[1]
                module_path = inspect.getmodule(frm[0]).__name__
                # key that we might use to resolve the class, once it's ready
                key = '.'.join([module_path, store_class])
            # try to import the `store_class` first - it might be ready
            module = import_module(module_path)
            self.store_class = getattr(module, store_class, None)
            # if the `store_class` is not ready yet, set the field to be resolved later
            if not self.store_class:
                # set the item in `pending_fields` dict
                pending_fields.setdefault(key, []).append(self)
                # mock callable object here
                self.store_class = object
        elif callable(store_class):
            self.store_class = store_class
        else:
            raise TypeError("`store_class` should be either callable or string.")
        self.is_array = is_array
        if is_array:
            self.store = CollectionStore(self.store_class)
        else:
            self.store = self.store_class()
        super(EmbeddedStoreField, self).__init__(target)


class Store(object):
    """Base model class for dict datastore handling."""
    __metaclass__ = StoreMeta

    def __init__(self, data=None):
        if data is None:
            data = {}
        self.data = data
        self._embedded_stores_cache = {}

    def __getattribute__(self, name):
        selfattr = super(Store, self).__getattribute__
        attr = selfattr(name)
        # in case of embedded store, return the store instead of the field
        if isinstance(attr, (EmbeddedStoreField,)):
            # making attribute access less costly
            # no need to create the instance of store on every access
            if name not in self._embedded_stores_cache:
                if attr.target is False:
                    data = self.data
                else:
                    data = self.data[attr.target] if attr.target in self.data else {}
                if attr.is_array:
                    store = CollectionStore(attr.store_class, data)
                else:
                    store = attr.store_class(data)
                self._embedded_stores_cache[name] = store
            return self._embedded_stores_cache[name]
        # if it's a field, fetch the value in the model data and return it
        elif isinstance(attr, (Field,)):
            try:
                return attr.get(self.data)
            except (KeyError,):
                raise AttributeError("'%s' store lookup failed for '%s'" % (
                    self.__class__.__name__, attr.target))
        else:
            return attr

    def __setattr__(self, name, value):
        if name in self.fields:
            attr = self.fields[name]
            # embedded stores are not directly settable
            if isinstance(attr, (EmbeddedStoreField,)):
                raise TypeError("'%s' store does not support %s assignment" % (
                    self.__class__.__name__, EmbeddedStoreField.__name__))
            # if it's a field, set the value in the model data
            elif isinstance(attr, (Field,)):
                try:
                    attr.set(self.data, value)
                except (KeyError,):
                    raise AttributeError("'%s' store lookup failed for '%s'" % (
                        self.__class__.__name__, attr.target))
        else:
            super(Store, self).__setattr__(name, value)

    def __iter__(self):
        for name in self.fields:
            yield name, getattr(self, name)

    def __nonzero__(self):
        return bool(self.data)


class CollectionStore(Store):
    """Handles collection of stores and provide array-like interface to access them.
    """

    def __init__(self, store_class, data=None):
        if data is None:
            data = []
        self.store_class = store_class
        # In reaktor 1.41.80, document categories are returned as hashes rather
        # than lists, so barrel has to make it compatible. Should removed when
        # reaktor is fixed (to check in 1.50.16).
        if isinstance(data, dict):
            data = data.values()
        return super(CollectionStore, self).__init__(data)

    def __getitem__(self, index):
        if index not in self._embedded_stores_cache:
            self._embedded_stores_cache[index] = self.store_class(self.data[index])
        return self._embedded_stores_cache[index]

    def __iter__(self):
        return (self[k] for k in xrange(len(self)))

    def __len__(self):
        return len(self.data)


class BooleanField(Field):
    """Handles the boolean values"""
    def get(self, dct):
        value = super(BooleanField, self).get(dct)
        if value == 'true' or value is True:
            return True
        elif value == 'false' or value is False:
            return False
        else:
            raise ValueError("Cannot convert to boolean: %s" % value)


class DateField(Field):
    """Handles date values - returns datetime object"""
    def get(self, dct):
        value = super(DateField, self).get(dct)
        return iso8601.parse_date(value)


class IntField(Field):
    """Handles integer values - returns int"""
    def get(self, dct):
        value = super(IntField, self).get(dct)
        return int(value)


class FloatField(Field):
    """Handles float values - returns float"""
    def get(self, dct):
        value = super(FloatField, self).get(dct)
        return float(value)


class LongIntField(Field):
    """Handles long integer values - returns long"""
    def get(self, dct):
        value = super(LongIntField, self).get(dct)
        # Reaktor inconsistently returns ISBN containing dashes or no separator.
        # Make sure skins doesn't get in trouble because of that.
        return long(''.join(str(value).split('-')))


class SplitField(Field):
    """Handles splittable strings - returns list"""
    def __init__(self, target, target_sep=':', default=None, value_sep=','):
        super(SplitField, self).__init__(target, target_sep=target_sep, default=default)
        self.value_sep = value_sep

    def get(self, dct):
        value = super(SplitField, self).get(dct)
        # value might be the default, in which would probably already be a list
        if isinstance(value, list):
            return value
        else:
            return value.split(self.value_sep)


# This field is not used at the moment because of the reaktor price handling inconsistency.
# Kept here for the better __future__.
# class MoneyField(Field):
#     """Handles money dictionary values - amount and currency. Expects a dictionary. Returns `Money` object"""
#     def get(self, dct):
#         value = super(MoneyField, self).get(dct)
#         return Money(**value)
