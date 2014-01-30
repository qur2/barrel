from . import Store, Field, BooleanField, DateField, IntField, FloatField, LongIntField, EmbeddedStoreField
from rpc import RpcMixin, rpc_call
from django.utils.translation import ugettext as _
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
        subtitle = Field(target='subtitle')
        tax_group = Field(target='tax_group')
        title = Field(target='title')
        year = IntField(target='year')
        large_cover_url = Field(target='cover_image_url_large')
        normal_cover_url = Field(target='cover_image_url_normal')
        medium_cover_url = Field(target='cover_image_url_medium')
        undiscounted_price = FloatField(target='undiscounted_price')

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

    @property
    def undiscounted_price(self):
        return Money(amount=self.attributes.undiscounted_price, currency=self.attributes.currency)

    @classmethod
    @rpc_call
    def get_by_id(cls, token, doc_id):
        """Returns `Document` instance for the given id."""
        return cls.signature(method='getDocument', args=[token, doc_id])

    @classmethod
    @rpc_call
    def get_user_doc_id(cls, token, doc_id):
        """Returns user document id for the catalog document id if any."""
        return cls.signature(method='getUserDocumentID', data_converter=lambda d: d, args=[token, doc_id])


class ReaktorMoney(Store):
    """Helper class to use with the new reaktor price fields."""
    amount = FloatField(target='amount')
    currency = Field(target='currency')


# FIXME: this class is used as embedded for `voucherApplications`
# thus it might differ from the voucher that comes in the basket position
class Voucher(Store, RpcMixin):
    code = LongIntField(target='code')
    text = Field(target='text')
    _initial_amount = EmbeddedStoreField(target='initialAmount', store_class=ReaktorMoney)
    _amount = EmbeddedStoreField(target='amount', store_class=ReaktorMoney)
    # not sure if it is needed
    # java_cls = Field(target='javaClass')

    @property
    def initial_amount(self):
        return Money(amount=self._initial_amount.amount, currency=self._initial_amount.currency)

    @property
    def amount(self):
        return Money(amount=self._amount.amount, currency=self._amount.currency)


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

    @classmethod
    def add_to_basket(cls, token, basket_id, item_id):
        """A convenience shortcut to provide nicer API."""
        return cls.set_basket_quantity(token, basket_id, item_id, 1)

    @classmethod
    def remove_from_basket(cls, token, basket_id, item_id):
        """A convenience shortcut to provide nicer API."""
        return cls.set_basket_quantity(token, basket_id, item_id, 0)


class DocumentItem(Item, RpcMixin):
    interface = 'WSDocMgmt'
    document = EmbeddedStoreField(target='item', store_class=Document)

    @classmethod
    @rpc_call
    def set_basket_quantity(cls, token, basket_id, doc_id, quantity):
        """Reaktor `WSDocMgmt.changeDocumentBasketPosition` call.
        If `quantity` is 0, then removes the document from the basket.
        If `quantity` is not 0, then adds the document into the basket.
        Returns None.
        """
        return cls.signature(method='changeDocumentBasketPosition', args=[token, basket_id, doc_id, quantity])


class VoucherItem(Item, RpcMixin):
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

    # txtr to adyen mapping of payment methods;
    # see Enum com.bookpac.server.shop.payment.PaymentMethod and adyen's Integration Manual pp 12+13 for the names
    PAYMENT_METHODS = { "CREDITCARD" : ["visa", "mc"], "ELV":["elv"] }

    PAYMENT_TRANSLATIONS = {
        # See: SKINSTXTRCOM-2165
        'CREDITCARD': _('Credit Card'), # "CREDITCARD should stay to be backward compatible, my son." --Stephan Noske
        'AMEX-SSL': _('American Express'),
        'VISA-SSL': _('Visa'),
        'VISA_COMMERCIAL_CREDIT-SSL': _('Visa'),
        'VISA_CREDIT-SSL': _('Visa'),
        'visa': _('Visa'), # lowercase key, comes from Adyen
        'ECMC-SSL': _('MasterCard'),
        'ECMC_COMMERCIAL_CREDIT-SSL': _('MasterCard'),
        'ECMC_CREDIT-SSL': _('MasterCard'),
        'mc': _('MasterCard'), # lowercase key, comes from Adyen
        'PAYPAL_EXPRESS': _('PayPal'),
        'ELV': _('Direct Debit'),
        'ELV-SSL': _('Direct Debit'),
        'DINERS': _("Diner's Club"),
        'DINERS-SSL': _("Diner's Club"),
    }

    # not sure if this is used
    # NOTE (Iurii Kudriavtsev): this is not a complete fields definition
    # class PaymentProperty(Store):
    #     merchant_account = Field(target='merchantAccount')
    #     merchant_ref = Field(target='merchantReference')

    class AppliedVoucherItem(Store):
        voucher = EmbeddedStoreField(target='voucher', store_class=Voucher)
        discount = EmbeddedStoreField(target='discountAmount', store_class=ReaktorMoney)

    class PaymentForm(Store):
        form = Field(target='com.bookpac.server.shop.payment.paymentform')
        recurring = Field(target='com.bookpac.server.shop.payment.paymentform.recurring')
        worecurring = Field(target='com.bookpac.server.shop.payment.paymentform.worecurring')

    id = Field(target='ID')
    checked_out = BooleanField(target='checkedOut')
    creation_date = DateField(target='creationTime')
    modification_date = DateField(target='modificationTime')
    country = Field(target='country')
    _total = EmbeddedStoreField(target='total', store_class=ReaktorMoney)
    _net_total = EmbeddedStoreField(target='netTotal', store_class=ReaktorMoney)
    _tax_total = EmbeddedStoreField(target='taxTotal', store_class=ReaktorMoney)
    _undiscounted_total = EmbeddedStoreField(target='undiscountedTotal', store_class=ReaktorMoney)
    # payment_props = EmbeddedStoreField(target='paymentProperties', store_class=PaymentProperty)
    payment_forms = EmbeddedStoreField(target='paymentForms', store_class=PaymentForm)
    items = EmbeddedStoreField(target='positions', store_class=item_factory, is_array=True)
    authorized_payment_methods = Field(target='authorizedPaymentMethods')
    applied_vouchers = EmbeddedStoreField(target='voucherApplications', store_class=AppliedVoucherItem, is_array=True)

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

    @property
    def document_items(self):
        """A property that allows to iterate over the document items.
        Returns generator.
        """
        for item in self.items:
            if isinstance(item, DocumentItem):
                yield item

    @property
    def voucher_items(self):
        """A property that allows to iterate over the voucher items.
        Returns generator.
        """
        for item in self.items:
            if isinstance(item, VoucherItem):
                yield item

    @property
    def documents(self):
        """A property that allows to iterate over the documents.
        Returns generator.
        """
        for item in self.document_items:
            yield item.document

    @property
    def vouchers(self):
        """A property that allows to iterate over the vouchers.
        Returns generator.
        """
        for item in self.voucher_items:
            yield item.voucher

    def is_authorized_for(self, payment_method):
        """Check whether the basket is authorized for the given payment_method.
        """
        if payment_method in self.PAYMENT_METHODS.get("CREDITCARD") and hasattr(self, 'authorized_payment_methods'):
            return "CREDITCARD" in self.authorized_payment_methods
        elif payment_method in self.PAYMENT_METHODS.get("ELV") and hasattr(self, 'authorized_payment_methods'):
            return "ELV" in self.authorized_payment_methods
        else:
            return False

    def translate_authorized_payment_methods(self):
        """Returns a list of human-readable authorized payment methods.
        """
        payment_methods = []
        if hasattr(self, 'authorized_payment_methods'):
            for payment_method in self.authorized_payment_methods:
                if payment_method in self.PAYMENT_TRANSLATIONS:
                    payment_methods.append(self.PAYMENT_TRANSLATIONS[payment_method])
                else:
                    payment_methods.append(payment_method)
        return payment_methods


    @classmethod
    @rpc_call
    def get_by_id(cls, token, basket_id):
        return cls.signature(method='getBasket', args=[token, basket_id])

    @classmethod
    @rpc_call
    def checkout(cls, token, basket_id, method_preference, checkout_props):
        # checkoutBasket is deprecated
        return cls.signature(method='checkoutBasket', data_converter=CheckoutResult, args=[token, basket_id, method_preference, checkout_props.data])

    @classmethod
    @rpc_call
    def create(cls, token, marker=None):
        return cls.signature(method='getNewBasket', args=[token, marker])


class CheckoutResult(Store):

    class ItemProperty(Store):
        document_id = Field(target='com.bookpac.server.shop.fulfillment.document.newid')

    basket = EmbeddedStoreField(target='checkedOutBasket', store_class=Basket)
    code = Field(target='resultCode')
    failed_item_index = IntField(target='failingPosition')
    item_properties = EmbeddedStoreField(target='positionResultProperties', store_class=ItemProperty, is_array=True)
    receipt_id = Field(target='receiptIdentifier')
    transaction_id = Field(target='transactionID')
