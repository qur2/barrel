from collections import namedtuple
from functools import wraps, partial
from warnings import warn
from libs.own.holon import reaktor


RpcSignature = namedtuple('RpcSignature', 'interface, method, data_converter, args')


def check_data(data_converter, dct):
    """Store class method returns `None` in case the reaktor call returns `void`."""
    if dct:
        return data_converter(dct)


class RpcMixin(object):
    @classmethod
    def signature(cls, interface=None, method=None, data_converter=None, args=None):
        """Returns a named tuple suitable for easy RPC call while providing
        some defaults: the RPC interface and the data converter are read
        from the class.
        """
        return RpcSignature(interface=interface or cls.interface, method=method,
                            data_converter=data_converter or cls, args=args)


def rpc_call(func):
    """Handle RPC calls using the wrapped classmethod returned signature.
    Handles multiple rpc signatures and returns the last result.
    """
    @wraps(func)
    def inner(cls, *args, **kwargs):
        sig = func(cls, *args, **kwargs)
        return do_rpc_call(sig)
    return inner


def do_rpc_call(sig):
    interface = getattr(reaktor(), sig.interface)
    converter = partial(check_data, sig.data_converter)
    return getattr(interface, sig.method)(*sig.args, data_converter=converter)


def deprecated(deprecated_call):
    """Logs a deprecation warning for the call.

    :param deprecated_call: reaktor call, that is deprecated
    :type deprecated_call: str or unicode
    """
    def outer(func):
        @wraps(func)
        def inner(cls, *args, **kwargs):
            warn(Warning("`%s` call is deprecated." % deprecated_call))
            return func(cls, *args, **kwargs)
        return inner
    return outer


#TODO (Iurii Kudriavtsev): think of combining these two decorators
def deprecated_with(deprecated_call, new_call):
    """Logs a deprecation warning for the call.

    :param deprecated_call: reaktor call, that is deprecated
    :type deprecated_call: str or unicode
    :param new_call: reaktor_call that should be used instead of the deprecated call
    :type deprecated_call: str or unicode
    """
    def outer(func):
        @wraps(func)
        def inner(cls, *args, **kwargs):
            warn(Warning("`%s` call is deprecated. Use `%s` call instead." % (deprecated_call, new_call)))
            return func(cls, *args, **kwargs)
        return inner
    return outer
