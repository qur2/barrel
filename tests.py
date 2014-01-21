from . import *
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from unittest import skip


DATA = {
  "userID": 32217171,
  "userName": "FACEBOOK:100003691408573",
  "externalUserIdentifiers": [
    {
      "identifier": "100003691408573",
      "authenticationServiceName": "FACEBOOK"
    }
  ],
  "userPrivateName": "Txtrskins Dev",
  "userDisplayName": "Txtrskins Dev",
  "userNature": "txtr.de",
  "userImageUrl": "https://graph.facebook.com/100003691408573/picture?type=square",
  "EMail": "bjoern.larsson@txtr.com",
  "emailVerified": True,
  "userLevel": "KNOWN",
  "company": "txtr",
  "settings": {
    "com.bookpac.user.settings.locale": "de",
    "com.bookpac.user.settings.shop.address.valid": "true",
    "com.bookpac.user.settings.shop.address1": "gdfgdfgd",
    "com.bookpac.user.settings.shop.birthday": "1970/01/01",
    "com.bookpac.user.settings.shop.country": "DE",
    "com.bookpac.user.settings.shop.firstname": "Txtrskins",
    "com.bookpac.user.settings.shop.gender": "MALE",
    "com.bookpac.user.settings.shop.lastname": "Dev",
    "com.bookpac.user.settings.shop.location": "fgdfgdfgfd",
    "com.bookpac.user.settings.shop.zipcode": "12345"
  },
  "disabled": 'false',
  # the following two lines are not a real world example
  # they are here just for the testing purposes
  "passwordExpiration": "2014-01-25T12:00:00+01:00",
  "money": {
    "amount": 0.99,
    "currency": "USD"
  },
  "xzibit": [{
    "foo": {
      "bar": "some"
    }
  }],
  "someFloatValue": '0.605714'
}


class BarrelTestCase(TestCase):
    """The test case for Barrel."""

    def setUp(self):
        self.raw_data = DATA

    def testSimpleGet(self):
        """`simple_get` behaves like dictionary `__getitem__`"""
        self.assertEqual(simple_get("userID", self.raw_data), self.raw_data["userID"])

    def testDeepGet(self):
        """`deep_get` handles nested dictionaries"""
        self.assertEqual(deep_get("settings:com.bookpac.user.settings.locale", self.raw_data), self.raw_data["settings"]["com.bookpac.user.settings.locale"])

    def testSimpleSet(self):
        """`simple_set` behaves like dictionary `__setitem__`"""
        local_data = {'userID': 'oui'}
        simple_set("userID", local_data, 'non')
        self.assertEqual(local_data["userID"], 'non')

    def testDeepSet(self):
        """`deep_set` handles nested dictionaries"""
        local_data = {'userID': {'foo': {'bar': 'oui'}}}
        deep_set("userID:foo:bar", local_data, 'non')
        self.assertEqual(local_data["userID"]["foo"]["bar"], 'non')

    def testDeepGetSeparator(self):
        """`deep_get` can receive any separator"""
        self.assertEqual(deep_get("settings/com.bookpac.user.settings.locale", self.raw_data, sep='/'), self.raw_data["settings"]["com.bookpac.user.settings.locale"])

    def testFieldNoTarget(self):
        """`Field` cannot be instantiated without target"""
        self.assertRaises(TypeError, Field)

    def testStore(self):
        """`Store` gets a default attribute called `fields`"""
        self.assertTrue(hasattr(Store(), 'fields'))

    def testStoreField(self):
        """`Store` handles `Field`-type attributes"""
        class User(Store):
            id = Field(target='userID')
        u = User(self.raw_data)
        self.assertEqual(u.id, self.raw_data["userID"])

    def testStoreFieldSet(self):
        """`Store` sets `Field`-type attributes"""
        local_data = self.raw_data.copy()
        class User(Store):
            id = Field(target='userID')
        u = User(local_data)
        u.id = 'eureka!'
        self.assertEqual(u.id, local_data['userID'])

    def testStoreAttr(self):
        """`Store` handles any attributes"""
        class User(Store):
            id = 'some'
        # check that __getattribute__ doesn't mess with the normal attributes
        self.assertEqual(User().id, 'some')

    def testEmbeddedStoreField(self):
        """`EmbeddedStoreField` has the `store` attribute of the given class"""
        class Foo(Store): pass
        f = EmbeddedStoreField('target', Foo)
        self.assertEqual(f.store.__class__.__name__, 'Foo')

    def testEmbeddedStoreFieldCollection(self):
        """`EmbeddedStoreField` has the `store` attribute of the `CollectionStore` type in case of an array"""
        class Foo(Store): pass
        f = EmbeddedStoreField('target', Foo, is_array=True)
        self.assertEqual(f.store.__class__.__name__, 'CollectionStore')

    def testEmbeddedStoreFieldData(self):
        """`EmbeddedStoreField` store `data` attribute has correct data for target"""
        class Foo(Store): pass
        f = EmbeddedStoreField('userID', Foo)
        f.set_store_data(self.raw_data)
        self.assertEqual(f.store.data, self.raw_data["userID"])

    def testEmbeddedStoreFieldDataNoTarget(self):
        """`EmbeddedStoreField` store `data` attribute has correct data if no target"""
        class Foo(Store): pass
        f = EmbeddedStoreField(False, Foo)
        f.set_store_data(self.raw_data)
        self.assertEqual(f.store.data, self.raw_data)

    def testStoreWithEmbeddedStoreField(self):
        """`Store` propagates data to the embedded store"""
        class UserSettings(Store):
            locale = Field(target='com.bookpac.user.settings.locale')
        class User(Store):
            settings = EmbeddedStoreField(target='settings', store_class=UserSettings)

        u = User(self.raw_data)
        self.assertEqual(u.settings.locale, self.raw_data["settings"]["com.bookpac.user.settings.locale"])

    def testStoreWithEmbeddedStoreFieldSet(self):
        """`Store` sets data in the embedded store"""
        local_data = deepcopy(self.raw_data)
        class UserSettings(Store):
            locale = Field(target='com.bookpac.user.settings.locale')
        class User(Store):
            settings = EmbeddedStoreField(target='settings', store_class=UserSettings)

        u = User(local_data)
        u.settings.locale = 'FU'
        self.assertEqual(u.settings.locale, local_data["settings"]["com.bookpac.user.settings.locale"])

    def testCollectionStore(self):
        """`CollectionStore` items have the given store class"""
        class Foo(Store): pass
        c = CollectionStore(Foo, self.raw_data["externalUserIdentifiers"])
        self.assertEqual(c[0].__class__.__name__, 'Foo')

    def testCollectionStoreLength(self):
        """`CollectionStore` looks like an list"""
        class Foo(Store): pass
        c = CollectionStore(Foo, self.raw_data["externalUserIdentifiers"])
        self.assertEqual(len(c), len(self.raw_data["externalUserIdentifiers"]))

    def testEmbeddedCollectionStoreFieldData(self):
        """Nested `EmbeddedStoreField` store `data` attribute has correct data for target"""
        class Bar(Store):
            bar = Field('bar')
        class Foo(Store):
            foo = EmbeddedStoreField('foo', Bar)
        f = EmbeddedStoreField('xzibit', Foo, is_array=True)
        f.set_store_data(self.raw_data)
        self.assertEqual(f.store[0].foo.bar, self.raw_data["xzibit"][0]["foo"]["bar"])

    def testStoreWithEmbeddedStoreFieldCollection(self):
        """`Store` propagates data to the embedded collection store"""
        class UserExternalUid(Store):
            service = Field(target='authenticationServiceName')
        class User(Store):
            external_uid = EmbeddedStoreField(target='externalUserIdentifiers', store_class=UserExternalUid, is_array=True)
        u = User(self.raw_data)
        self.assertEqual(u.external_uid[0].service, self.raw_data["externalUserIdentifiers"][0]["authenticationServiceName"])

    def testStoreAttributeLookupError(self):
        """`Store` throws `AttributeError` for non-existing keys"""
        class Foo(Store):
            id = Field(target='foo')
        f = Foo(self.raw_data)
        self.assertRaises(AttributeError, lambda: f.id)

    def testBooleanField(self):
        """`BooleanField` returns boolean value"""
        class User(Store):
            disabled = BooleanField(target='disabled')
        u = User(self.raw_data)
        self.assertFalse(u.disabled)

    def testBooleanFieldValueError(self):
        """`BooleanField` throws ValueError when converting from invalid data"""
        class User(Store):
            disabled = BooleanField(target='userID')
        u = User(self.raw_data)
        self.assertRaises(ValueError, lambda: u.disabled)

    def testDateField(self):
        """`DateField` returns datetime object"""
        class User(Store):
            password_expiration = DateField(target='passwordExpiration')
        u = User(self.raw_data)
        self.assertTrue(isinstance(u.password_expiration, datetime))

    def testIntegerField(self):
        """`IntegerField` returns int"""
        class User(Store):
            id = IntegerField(target='userID')
        u = User(self.raw_data)
        self.assertTrue(isinstance(u.id, int))

    def testFloatField(self):
        """`FloatField` returns float"""
        class User(Store):
            value = FloatField(target='someFloatValue')
        u = User(self.raw_data)
        self.assertTrue(isinstance(u.value, float))

    def testLongIntField(self):
        """`LongIntField` returns long"""
        class User(Store):
            id = LongIntField(target='userID')
        u = User(self.raw_data)
        self.assertTrue(isinstance(u.id, long))

    @skip('`MoneyField` is not supported yet')
    def testMoneyField(self):
        """`MoneyField` returns `Money` object"""
        class User(Store):
            money = MoneyField(target='money')
        u = User(self.raw_data)
        self.assertTrue(isinstance(u.money, Money))

    @skip('`MoneyField` is not supported yet')
    def testMoneyFieldAmount(self):
        """`MoneyField` amount is correct"""
        class User(Store):
            money = MoneyField(target='money')
        u = User(self.raw_data)
        self.assertEqual(u.money.amount, Decimal(self.raw_data['money']['amount']).quantize(Decimal("0.00")))

    @skip('`MoneyField` is not supported yet')
    def testMoneyFieldCurrency(self):
        """`MoneyField` currency is correct"""
        class User(Store):
            money = MoneyField(target='money')
        u = User(self.raw_data)
        self.assertEqual(u.money.currency.code, self.raw_data['money']['currency'])
