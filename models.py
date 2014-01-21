from . import Store, Field, BooleanField, DateField, IntField, FloatField, LongIntField, EmbeddedStoreField
from rpc import RpcMixin, rpc_call
from money import Money


class Nature(Store, RpcMixin):
    interface = 'WSReaktorMgmt'

    name = Field(target='name')
    home_country = Field(target='homeCountry')
    auth_hash_method = Field(target='authenticationHashAlgorithm')

    @classmethod
    @rpc_call
    def load(cls, name):
        return cls.signature(method='getNature', args=[name])


class Document(Store, RpcMixin):
    interface = 'WSDocMgmt'

    class Author(Store):
        first_name = Field(target='firstName')
        last_name = Field(target='lastName')

    class Attributes(Store):
        author = Field(target='author')
        as_epub = BooleanField(target='available_as_epub') # should be deprecated soon
        as_pdf = BooleanField(target='available_as_pdf') # should be deprecated soon
        as_watermark = BooleanField(target='available_as_watermark') # should be deprecated soon
        via_iap = BooleanField(target='available_via_iap') # should be deprecated soon
        with_adobe_drm = BooleanField(target='available_with_adobe_drm') # should be deprecated soon
        hash = Field(target='binary_hash')
        content_provider_name = Field(target='content_provider_name')
        content_provider_id = Field(target='content_provider_specific_id')
        content_source_id = Field(target='content_source_id')
        cover_ratio = FloatField(target='cover_image_aspect_ratio')
        currency = Field(target='currency')
        first_publication = Field(target='date_of_first_publication')
        description = Field(target='description')
        fulfillment_id = Field(target='fulfillment_id')
        fulfillment_type = Field(target='fulfillment_type')
        isbn = LongIntField(target='isbn')
        language = Field(target='language')
        pages = IntField(target='number_of_pages')
        price = FloatField(target='price')
        publication_date = DateField(target='publication_date')
        publisher = Field(target='publisher')
        size = IntField(target='size')
        tax_group = Field(target='tax_group')
        title = Field(target='title')
        year = IntField(target='year')
        large_cover_url = Field(target='cover_image_url_large')
        normal_cover_url = Field(target='cover_image_url_normal')
        medium_cover_url = Field(target='cover_image_url_medium')

    # probably should be moved outside of this class
    class Category(Store):
        id = Field(target='ID')
        name = Field(target='name')
        offset = IntField(target='offset')
        count = IntField(target='count')
        subtree_size = IntField(target='subtreeSize')
        children = Field(target='childrenIDs')
        parent = Field(target='parentID')
        filter = Field(target='filter')

    class License(Store):
        key = Field(target='key')
        user_roles = Field(target='currentUserRoles')

    id = Field(target='documentID')
    master_id = Field(target='documentMasterID')
    name = Field(target='displayName')
    lang_code = Field(target='languageCode')
    format = Field(target='format')
    version = IntField(target='version')
    attributes = EmbeddedStoreField(target='attributes', store_class=Attributes)
    votes = IntField(target='numberOfVotes')
    modification_date = DateField(target='modificationTime')
    creation_date = DateField(target='creationTime')
    owner = Field(target='owner')
    creator = Field(target='creator')
    in_public_list = BooleanField(target='inPublicList')
    version_size = IntField(target='versionSize')
    version_access_type = Field(target='versionAccessType')
    has_thumbnail = BooleanField(target='hasThumbnail')
    licenses = EmbeddedStoreField(target='licenses', store_class=License, is_array=True)
    category_ids = Field(target='contentCategoryIDs')
    categories = EmbeddedStoreField(target='contentCategories', store_class=Category, is_array=True)
    drm_type = Field(target='drmType')
    catalog_state = Field(target='catalogDocumentState')
    authors = EmbeddedStoreField(target='authors', store_class=Author, is_array=True)

    @property
    def price(self):
        return Money(amount=self.attributes.price, currency=self.attributes.currency)


class ReaktorMoney(Store):
    """Helper class to use with the new reaktor price fields."""
    amount = FloatField(target='amount')
    currency = Field(target='currency')


class Voucher(Store, RpcMixin):
    id = Field(target='caca')


class Item(Store):
    """Base item class, to be extended for specific purposes."""
    _total = EmbeddedStoreField(target='positionTotal', store_class=ReaktorMoney)
    _net_total = EmbeddedStoreField(target='positionNetTotal', store_class=ReaktorMoney)
    _tax_total = EmbeddedStoreField(target='positionTaxTotal', store_class=ReaktorMoney)
    _undiscounted_total = EmbeddedStoreField(target='undiscountedPositionTotal', store_class=ReaktorMoney)

    @property
    def total(self):
        return Money(amount=self._total.amount, currency=self._total.currency)

    @property
    def net_total(self):
        return Money(amount=self._net_total.amount, currency=self._net_total.currency)

    @property
    def tax_total(self):
        return Money(amount=self._tax_total.amount, currency=self._tax_total.currency)

    @property
    def undiscounted_total(self):
        return Money(amount=self._undiscounted_total.amount, currency=self._undiscounted_total.currency)


class DocumentItem(Item):
    document = EmbeddedStoreField(target='item', store_class=Document)


class VoucherItem(Item):
    voucher = EmbeddedStoreField(target='item', store_class=Voucher)


def item_factory(data=None):
    """Item factory to get properly typed basket items."""
    if data is None:
        return Item()
    item_type = data.get('itemType', 'NONE')
    if item_type == 'DOCUMENT':
        return DocumentItem(data)
    elif item_type == 'VOUCHER':
        return VoucherItem(data)
    else:
        raise ValueError('Basket item type not supported: %s' % item_type)


class CheckoutProperties(Store):
    clear_failed_preauth = BooleanField(target='clearFailedAuthorization')
    clear_preauth = BooleanField(target='clearPreAuthorization')
    use_preauth = BooleanField(target='usePreAuthorization')
    recurring_payment = BooleanField(target='requestedRecurringPayment')
    affiliate_id = Field(target='affiliateID')
    external_transaction_id = Field(target='externalTransactionID')


class Basket(Store, RpcMixin):
    interface = 'WSShopMgmt'

    # class Payment(Store):
    #     merchant_account = Field(target='merchantAccount')
    #     merchant_ref = Field(target='merchantReference')

    id = Field(target='ID')
    checked_out = BooleanField(target='checkedOut')
    creation_date = DateField(target='creationTime')
    modification_date = DateField(target='modificationTime')
    country = Field(target='country')
    _total = EmbeddedStoreField(target='total', store_class=ReaktorMoney)
    _net_total = EmbeddedStoreField(target='netTotal', store_class=ReaktorMoney)
    _tax_total = EmbeddedStoreField(target='taxTotal', store_class=ReaktorMoney)
    _undiscounted_total = EmbeddedStoreField(target='undiscountedTotal', store_class=ReaktorMoney)
    # payment_props = EmbeddedStoreField(target='paymentProperties', store_class=Payment)
    items = EmbeddedStoreField(target='positions', store_class=item_factory, is_array=True)

    @property
    def total(self):
        return Money(amount=self._total.amount, currency=self._total.currency)

    @property
    def net_total(self):
        return Money(amount=self._net_total.amount, currency=self._net_total.currency)

    @property
    def tax_total(self):
        return Money(amount=self._tax_total.amount, currency=self._tax_total.currency)

    @property
    def undiscounted_total(self):
        return Money(amount=self._undiscounted_total.amount, currency=self._undiscounted_total.currency)

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
