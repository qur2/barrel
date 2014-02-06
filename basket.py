from . import Store, Field, BooleanField, DateField, IntField, EmbeddedStoreField
from rpc import RpcMixin, rpc_call
from models import ReaktorMoney
from document import Document
from voucher import Voucher
from django.utils.translation import ugettext as _
from money import Money


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

    @classmethod
    @rpc_call
    def set_basket_quantity(cls, token, basket_id, voucher_code, quantity):
        """This method should call the similar to `changeDocumentBasketPosition` reaktor method, but for Voucher.
        """
        raise NotImplemented


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
