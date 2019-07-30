import logging
import weakref


logger = logging.getLogger(__name__)


class Py2Object:
    """ Proxy for a Python 2 object. """

    __slots__ = ('__client__', '__oid__', '__weakref__')

    def __init__(self, client, oid):
        object.__setattr__(self, '__client__', weakref.proxy(client))
        object.__setattr__(self, '__oid__', oid)

    @property
    def _(self):
        """ Convert this object to its Python 3 equivalent. """
        return self.__client__.do_command('lift', self)

    @property
    def __(self):
        """ Recursively convert this object to its Python 3 equivalent. """
        return self.__client__.do_command('deeplift', self)

    def __repr__(self):
        obj_repr = self.__client__.do_command('repr', self)
        return '<{} {}>'.format(self.__class__.__name__,
                                obj_repr.decode(errors='replace'))

    def __str__(self):
        return self.__client__.do_command('unicode', self)

    def __bytes__(self):
        return self.__client__.do_command('str', self)

    def __format__(self, format_spec):
        return self.__client__.do_command('format', self, format_spec)

    def __lt__(self, other):
        return self.__client__.do_command('lt', self, other)

    def __le__(self, other):
        return self.__client__.do_command('le', self, other)

    def __eq__(self, other):
        return self.__client__.do_command('eq', self, other)

    def __ne__(self, other):
        return self.__client__.do_command('ne', self, other)

    def __gt__(self, other):
        return self.__client__.do_command('gt', self, other)

    def __ge__(self, other):
        return self.__client__.do_command('ge', self, other)

    def __hash__(self):
        return self.__client__.do_command('hash', self)

    def __bool__(self):
        return self.__client__.do_command('bool', self)

    def __getattr__(self, name):
        return self.__client__.do_command('getattr', self, name)

    def __setattr__(self, name, value):
        return self.__client__.do_command('setattr', self, name, value)

    def __delattr__(self, name):
        return self.__client__.do_command('delattr', self, name)

    def __call__(self, *args, **kwargs):
        return self.__client__.do_command('call', self, args, kwargs)

    def __len__(self):
        return self.__client__.do_command('len', self)

    def __getitem__(self, key):
        return self.__client__.do_command('getitem', self, key)

    def __setitem__(self, key, value):
        return self.__client__.do_command('setitem', self, key, value)

    def __delitem__(self, key):
        return self.__client__.do_command('delitem', self, key)

    def __iter__(self):
        return self.__client__.do_command('iter', self)

    def __reversed__(self):
        return self.__client__.do_command('reversed', self)

    def __contains__(self, item):
        return self.__client__.do_command('contains', self, item)

    def __next__(self):
        return self.__client__.do_command('next', self)

    def __add__(self, other):
        return self.__client__.do_command('add', self, other)

    def __sub__(self, other):
        return self.__client__.do_command('sub', self, other)

    def __mul__(self, other):
        return self.__client__.do_command('mul', self, other)

    def __truediv__(self, other):
        cmd = 'div' if isinstance(other, Py2Object) else 'truediv'
        return self.__client__.do_command(cmd, self, other)

    def __floordiv__(self, other):
        return self.__client__.do_command('floordiv', self, other)

    def __mod__(self, other):
        return self.__client__.do_command('mod', self, other)

    def __divmod__(self, other):
        return self.__client__.do_command('divmod', self, other)

    def __pow__(self, other, modulo=None):
        if modulo is None:
            return self.__client__.do_command('pow', self, other)
        else:
            return self.__client__.do_command('pow3', self, other, modulo)

    def __lshift__(self, other):
        return self.__client__.do_command('lshift', self, other)

    def __rshift__(self, other):
        return self.__client__.do_command('rshift', self, other)

    def __and__(self, other):
        return self.__client__.do_command('and', self, other)

    def __xor__(self, other):
        return self.__client__.do_command('xor', self, other)

    def __or__(self, other):
        return self.__client__.do_command('or', self, other)

    def __radd__(self, other):
        return self.__client__.do_command('add', other, self)

    def __rsub__(self, other):
        return self.__client__.do_command('sub', other, self)

    def __rmul__(self, other):
        return self.__client__.do_command('mul', other, self)

    def __rtruediv__(self, other):
        cmd = 'div' if isinstance(other, Py2Object) else 'truediv'
        return self.__client__.do_command(cmd, other, self)

    def __rfloordiv__(self, other):
        return self.__client__.do_command('floordiv', other, self)

    def __rmod__(self, other):
        return self.__client__.do_command('mod', other, self)

    def __rdivmod__(self, other):
        return self.__client__.do_command('divmod', other, self)

    def __rpow__(self, other):
        return self.__client__.do_command('pow', other, self)

    def __rlshift__(self, other):
        return self.__client__.do_command('lshift', other, self)

    def __rrshift__(self, other):
        return self.__client__.do_command('rshift', other, self)

    def __rand__(self, other):
        return self.__client__.do_command('and', other, self)

    def __rxor__(self, other):
        return self.__client__.do_command('xor', other, self)

    def __ror__(self, other):
        return self.__client__.do_command('or', other, self)

    def __iadd__(self, other):
        return self.__client__.do_command('iadd', self, other)

    def __isub__(self, other):
        return self.__client__.do_command('isub', self, other)

    def __imul__(self, other):
        return self.__client__.do_command('imul', self, other)

    def __itruediv__(self, other):
        cmd = 'idiv' if isinstance(other, Py2Object) else 'itruediv'
        return self.__client__.do_command(cmd, self, other)

    def __ifloordiv__(self, other):
        return self.__client__.do_command('ifloordiv', self, other)

    def __imod__(self, other):
        return self.__client__.do_command('imod', self, other)

    def __ipow__(self, other):
        return self.__client__.do_command('ipow', self, other)

    def __ilshift__(self, other):
        return self.__client__.do_command('ilshift', self, other)

    def __irshift__(self, other):
        return self.__client__.do_command('irshift', self, other)

    def __iand__(self, other):
        return self.__client__.do_command('iand', self, other)

    def __ixor__(self, other):
        return self.__client__.do_command('ixor', self, other)

    def __ior__(self, other):
        return self.__client__.do_command('ior', self, other)

    def __complex__(self):
        return self.__client__.do_command('complex', self)

    def __int__(self):
        return self.__client__.do_command('int', self)

    def __float__(self):
        return self.__client__.do_command('float', self)

    def __round__(self, n=0):
        return self.__client__.do_command('round', self, n)

    def __index__(self):
        return self.__client__.do_command('index', self)

    def __del__(self):
        try:
            logger.debug("Deleting object {}".format(self.__oid__))
            self.__client__.do_command('del', self)
        except Exception:
            logger.debug("Delete failed", exc_info=True)
            pass  # Session may have already ended
