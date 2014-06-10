from . import Store, Field, FloatField
from rpc import RpcMixin, rpc_call


class Nature(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    home_country = Field(target='homeCountry')
    auth_hash_method = Field(target='authenticationHashAlgorithm')

    @classmethod
    @rpc_call
    def load(cls, name):
        return cls.signature(method='getNature', args=[name])


class ReaktorMoney(Store):
    """Helper class to use with the new reaktor price fields."""
    amount = FloatField(target='amount')
    currency = Field(target='currency')
