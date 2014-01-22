from collections import namedtuple
from functools import wraps, partial
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
        void_sigs = ()
        if not isinstance(sig, RpcSignature):
            void_sigs = sig[:-1]
            sig = sig[-1]
        for s in void_sigs:
            do_rpc_call(s)
        return do_rpc_call(sig)
    return inner


def do_rpc_call(sig):
    interface = getattr(reaktor(), sig.interface)
    converter = partial(check_data, sig.data_converter)
    return getattr(interface, sig.method)(*sig.args, data_converter=converter)
