from collections import namedtuple
from functools import wraps, partial
from warnings import warn
from libs.reaktor import reaktor


RpcSignature = namedtuple('RpcSignature', 'interface, method, data_converter, args')


def check_data(data_converter, data):
    """Store class method returns `None` in case the reaktor call returns `void`.
    For empty result (<> void), the data converter is still run because the backend
    omits empty and null attributes for bandwidth efficiency.
    In case of data being an array, a collection of items is assumed and each item
    is converted using the provided `data_converter`.
    """
    if isinstance(data, list):
        return [data_converter(d) for d in data]
    if data is not None:
        return data_converter(data)


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


class RpcMixin(object):
    @classmethod
    @rpc_call
    def signature(cls, interface=None, method=None, data_converter=None, args=None, deprecated=False):
        """Returns a named tuple suitable for easy RPC call while providing
        some defaults: the RPC interface and the data converter are read
        from the class.

        :param interface: rpc interface to use
        :type interface: str or unicode
        :param method: rpc method to call
        :type method: str or unicode
        :param data_converter: python object to abstract the rpc object
        :type data_converter: any callable, e.g. subclass of `apps.barrel.Store`
        :param args: arguments to pass for rpc method
        :type args: list
        :param deprecated: flag to warn about deprecated call
        :type deprecated: bool or str or unicode
        """
        if deprecated:
            if isinstance(deprecated, basestring):
                message = "`%s` call is deprecated. Use `%s` call instead." % (method, deprecated)
            else:
                message = "`%s` call is deprecated." % method
            warn(Warning(message))
        return RpcSignature(interface=interface or cls.interface, method=method,
                            data_converter=data_converter or cls, args=args)
