def import_module(import_name):
    """Import function heavily inspired from `werkzeug.utils.import_string`/
    Just dropped the wide string type support and the better import error reporting.
    """
    if ':' in import_name:
        module, obj = import_name.split(':', 1)
    elif '.' in import_name:
        module, obj = import_name.rsplit('.', 1)
    else:
        return __import__(import_name)
    try:
        return getattr(__import__(module, None, None, [obj]), obj)
    except (ImportError, AttributeError):
        # support importing modules not yet set up by the parent module
        # (or package for that matter)
        import sys
        modname = module + '.' + obj
        __import__(modname)
        return sys.modules[modname]
