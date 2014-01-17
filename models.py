from . import Store, Field, BooleanField, DateField, MoneyField, EmbeddedStoreField
from rpc import RpcMixin, rpc_call


class Nature(Store, RpcMixin):
    interface = 'WSTReaktor'

    name = Field(target='name')
    home_country = Field(target='homeCountry')
    auth_hash_method = Field(target='authenticationHashAlgorithm')

    @classmethod
    @rpc_call
    def load(cls, name):
        return cls.signature(method='getNature', args=[name])


class Document(Store, RpcMixin):
    id = Field(target='documentID')


class Voucher(Store, RpcMixin):
    id = Field(target='caca')


class CheckoutProperties(Store):
    clear_failed_preauth = BooleanField(target='clearFailedAuthorization')
    clear_preauth = BooleanField(target='clearPreAuthorization')
    use_preauth = BooleanField(target='usePreAuthorization')
    recurring_payment = BooleanField(target='requestedRecurringPayment')
    affiliate_id = Field(target='affiliateID')
    external_transaction_id = Field(target='externalTransactionID')


class Basket(Store, RpcMixin):
    interface = 'WSShopMgmt'

    class Item(Store, RpcMixin):
        total = MoneyField(target='positionTotal')
        net_total = MoneyField(target='positionNetTotal')
        tax_total = MoneyField(target='positionTaxTotal')
        undiscounted_total = MoneyField(target='undiscountedPositionTotal')
        # voucher = EmbeddedStoreField(target='item', store_class=Voucher)
        document = EmbeddedStoreField(target='item', store_class=Document)

    class Payment(Store):
        merchant_account = Field(target='merchantAccount')
        merchant_ref = Field(target='merchantReference')

    id = Field(target='ID')
    checked_out = BooleanField(target='checkedOut')
    creation_date = DateField(target='creationTime')
    modification_date = DateField(target='modificationTime')
    country = Field(target='country')
    total = MoneyField(target='total')
    net_total = MoneyField(target='netTotal')
    tax_total = MoneyField(target='taxTotal')
    undiscounted_total = MoneyField(target='undiscountedTotal')
    # payment_props = EmbeddedStoreField(target='paymentProperties', store_class=Payment)
    items = EmbeddedStoreField(target='positions', store_class=Item, is_array=True)

    @classmethod
    @rpc_call
    def get_by_id(cls, token, bid):
        # "tJCodCILTxi3VsRJ2FILYfgbt00sj8-QP4jOxlNYFYD@"
        # "beogb97"
        return cls.signature(method='getBasket', args=[token, bid])

    @classmethod
    @rpc_call
    def checkout(cls, token, bid, checkout_props):
        # checkoutBasket is deprecated
        return cls.signature(method='checkoutBasket', args=[token, bid, checkout_props.data])
