"""This module enables model-like encapsulation of big dict structure (like JSON data).

    When I die I want to decompose in a barrel of porter and have it served in all the pubs in Dublin.
    J. P. Donleavy

The goal is to *not* map the underlying dict but just wrap it in a programmer-friendly structure
to allow attribute-like access and field aliasing.

Field aliasing enables to virtually:

* change key names
* modify the apparent structure of the dict
"""
from iso8601 import iso8601
# from money import Money


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
        return super(StoreMeta, cls).__new__(cls, name, bases, attrs)


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

    def __init__(self, target, target_sep=':'):
        self.target = target
        self.target_sep = target_sep

    def get(self, dct):
        if self.target and self.target_sep in self.target:
            return deep_get(self.target, dct, self.target_sep)
        else:
            return simple_get(self.target, dct)

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
        self.store_class = store_class
        if is_array:
            self.store = CollectionStore(store_class)
        else:
            self.store = store_class()
        super(EmbeddedStoreField, self).__init__(target)

    @property
    def is_array(self):
        return isinstance(self.store, CollectionStore)


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
                raise AttributeError("'%s' store lookup failed for '%s'" %
                    (self.__class__.__name__, attr.target))
        else:
            return attr

    def __setattr__(self, name, value):
        if name in self.fields:
            attr = self.fields[name]
            # embedded stores are not directly settable
            if isinstance(attr, (EmbeddedStoreField,)):
                raise TypeError("'%s' store does not support %s assignment" %
                        (self.__class__.__name__, EmbeddedStoreField.__name__))
            # if it's a field, set the value in the model data
            elif isinstance(attr, (Field,)):
                try:
                    attr.set(self.data, value)
                except (KeyError,):
                    raise AttributeError("'%s' store lookup failed for '%s'" %
                        (self.__class__.__name__, attr.target))
        else:
            super(Store, self).__setattr__(name, value)


class CollectionStore(Store):
    """Handles collection of stores and provide array-like interface to
    access them.
    """
    def __init__(self, store_class, data=None):
        if data is None:
            data = []
        self.store_class = store_class
        # another patch to overcome reaktor inconsistency.
        # in some cases reaktor returns dictionary of objects in places where the array is expected
        # so we ignore the keys and use the values as an array
        if isinstance(data, dict):
            data = data.values()
        self.data = data

    def __getitem__(self, i):
        return self.store_class(self.data[i])

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
        return long(value)


# This field is not used at the moment because of the reaktor price handling inconsistency.
# Kept here for the better __future__.
# class MoneyField(Field):
#     """Handles money dictionary values - amount and currency. Expects a dictionary. Returns `Money` object"""
#     def get(self, dct):
#         value = super(MoneyField, self).get(dct)
#         return Money(**value)
