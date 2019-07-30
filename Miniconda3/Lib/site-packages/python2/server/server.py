# TODO: Logging

import __builtin__
from functools import wraps
import json
import logging
import operator
import sys
import traceback

from python2.server.codec import ServerCodec
from python2.shared.codec import EncodingDepth


logger = logging.getLogger(__name__)


def _command(edepth=EncodingDepth.REF):
    def wrapper(func):
        @wraps(func)
        def wrapped(self, *args):
            try:
                result = func(self, *args)
            except Exception:
                return self._raise(*sys.exc_info())
            else:
                return self._return(result, edepth=edepth)

        return wrapped

    return wrapper


def _commandfunc(func, edepth=EncodingDepth.REF, name=None):
    def wrapped(self, *args):
        try:
            result = func(*args)
        except Exception:
            return self._raise(*sys.exc_info())
        else:
            return self._return(result, edepth=edepth)

    if name is None:
        name = func.__name__
    wrapped.__name__ = '_do_{}'.format(name)

    return wrapped


def _reflect(obj):
    """ Identity function. """
    return obj


class Python2Server(object):
    """ Python 2 server. """

    def __init__(self, infile, outfile):
        self.infile = infile
        self.outfile = outfile
        self.objects = {}
        self.codec = ServerCodec(self)

    def cache_add(self, obj):
        """ Add an object to the server cache. """
        oid = id(obj)
        logger.debug("Caching object {}".format(oid))
        self.objects[oid] = obj

    def cache_get(self, oid):
        """ Get an object by id from the server cache. """
        return self.objects[oid]

    def cache_del(self, oid):
        """ Delete an object by id from the server cache. """
        logger.debug("Removing object {} from cache".format(oid))
        del self.objects[oid]

    def _send(self, data):
        json.dump(data, self.outfile)
        self.outfile.write('\n')
        self.outfile.flush()

    def _receive(self):
        line = self.infile.readline()
        if line:
            return json.loads(line)

    def _args(self, data):
        session = self.codec.decoding_session()
        return [session.decode(arg) for arg in data['args']]

    def _return(self, result, edepth):
        return dict(
            result='return',
            value=self.codec.encode(result, depth=edepth),
        )

    def _raise(self, exc_type, exc_value, exc_traceback):
        exc_value.__traceback__ = exc_traceback  # XXX: ?
        message = ''.join(traceback.format_exception_only(exc_type, exc_value))
        dct = dict(
            result='raise',
            message=self.codec.encode(
                unicode(message.rstrip('\n'), errors='replace'),
                depth=EncodingDepth.DEEP),
            exception=self.codec.encode(exc_value, depth=EncodingDepth.REF),
            # TODO: More elegant way to do this?
            types=[t.__name__ for t in exc_type.__mro__
                   if t is StopIteration or t is TypeError]
        )

        return dct

    @_command(edepth=EncodingDepth.DEEP)
    def _do_ping(self):
        """ No-op command used to test client-server communication. """
        pass

    # The following three commands all return the object passed in, but differ
    # in how the return value is encoded.
    _do_project = _commandfunc(_reflect, edepth=EncodingDepth.REF,
                               name='project')
    _do_lift = _commandfunc(_reflect, edepth=EncodingDepth.SHALLOW,
                            name='lift')
    _do_deeplift = _commandfunc(_reflect, edepth=EncodingDepth.DEEP,
                                name='deeplift')

    # Objects returned by reference are stored in the server cache.  This
    # command is used to drop an object from the server cache.
    @_command(edepth=EncodingDepth.DEEP)
    def _do_del(self, obj):
        self.cache_del(id(obj))

    @_command()
    def _do_builtin(self, name):
        """ Lookup a builtin by name. """
        return getattr(__builtin__, name)

    @_command()
    def _do_exec(self, code, scope):
        """ Execute code in the given scope. """
        exec code in scope
        return scope

    # String conversion
    _do_format = _commandfunc(format, edepth=EncodingDepth.DEEP)
    _do_repr = _commandfunc(repr, edepth=EncodingDepth.DEEP)
    _do_str = _commandfunc(str, edepth=EncodingDepth.DEEP)
    _do_unicode = _commandfunc(unicode, edepth=EncodingDepth.DEEP)

    # Rich comparisons
    # XXX: NotImplemented?
    _do_lt = _commandfunc(operator.lt, edepth=EncodingDepth.DEEP)
    _do_le = _commandfunc(operator.le, edepth=EncodingDepth.DEEP)
    _do_eq = _commandfunc(operator.eq, edepth=EncodingDepth.DEEP)
    _do_ne = _commandfunc(operator.ne, edepth=EncodingDepth.DEEP)
    _do_gt = _commandfunc(operator.gt, edepth=EncodingDepth.DEEP)
    _do_ge = _commandfunc(operator.ge, edepth=EncodingDepth.DEEP)

    # Basic customization
    _do_bool = _commandfunc(bool, edepth=EncodingDepth.DEEP)
    _do_hash = _commandfunc(hash, edepth=EncodingDepth.DEEP)

    # Attribute access
    _do_getattr = _commandfunc(getattr)
    _do_setattr = _commandfunc(setattr, edepth=EncodingDepth.DEEP)
    _do_delattr = _commandfunc(delattr, edepth=EncodingDepth.DEEP)

    # Callable objects
    @_command()
    def _do_call(self, obj, args, kwargs):
        """ Call a function or callable object. """
        return obj(*args, **kwargs)

    # Container types
    _do_len = _commandfunc(len, edepth=EncodingDepth.DEEP)
    _do_getitem = _commandfunc(operator.getitem)
    _do_setitem = _commandfunc(operator.setitem, edepth=EncodingDepth.DEEP)
    _do_delitem = _commandfunc(operator.delitem, edepth=EncodingDepth.DEEP)
    _do_iter = _commandfunc(iter)
    _do_reversed = _commandfunc(reversed)
    _do_contains = _commandfunc(operator.contains, edepth=EncodingDepth.DEEP)

    # Iterators
    _do_next = _commandfunc(next)

    # Numeric types
    _do_add = _commandfunc(operator.add)
    _do_sub = _commandfunc(operator.sub)
    _do_mul = _commandfunc(operator.mul)
    _do_div = _commandfunc(operator.div)
    _do_truediv = _commandfunc(operator.truediv)
    _do_floordiv = _commandfunc(operator.floordiv)
    _do_mod = _commandfunc(operator.mod)
    _do_divmod = _commandfunc(divmod)
    _do_pow = _commandfunc(pow)
    _do_pow3 = _commandfunc(pow, name='pow3')
    _do_lshift = _commandfunc(operator.lshift)
    _do_rshift = _commandfunc(operator.rshift)
    _do_and = _commandfunc(operator.and_, name='and')
    _do_xor = _commandfunc(operator.xor)
    _do_or = _commandfunc(operator.or_, name='or')

    _do_iadd = _commandfunc(operator.iadd)
    _do_isub = _commandfunc(operator.isub)
    _do_imul = _commandfunc(operator.imul)
    _do_idiv = _commandfunc(operator.idiv)
    _do_itruediv = _commandfunc(operator.itruediv)
    _do_ifloordiv = _commandfunc(operator.ifloordiv)
    _do_imod = _commandfunc(operator.imod)
    _do_ipow = _commandfunc(operator.ipow)
    _do_ilshift = _commandfunc(operator.ilshift)
    _do_irshift = _commandfunc(operator.irshift)
    _do_iand = _commandfunc(operator.iand)
    _do_ixor = _commandfunc(operator.ixor)
    _do_ior = _commandfunc(operator.ior)

    _do_neg = _commandfunc(operator.neg)
    _do_pos = _commandfunc(operator.pos)
    _do_abs = _commandfunc(operator.abs)
    _do_invert = _commandfunc(operator.invert)

    _do_complex = _commandfunc(complex, edepth=EncodingDepth.DEEP)
    _do_int = _commandfunc(int, edepth=EncodingDepth.DEEP)
    _do_float = _commandfunc(float, edepth=EncodingDepth.DEEP)
    _do_round = _commandfunc(round, edepth=EncodingDepth.DEEP)
    _do_index = _commandfunc(operator.index, edepth=EncodingDepth.DEEP)

    def run(self):
        """
        Read and execute commands until the input stream is closed or an
        exception is raised.
        """
        data = self._receive()
        while data:
            # TODO: Handle protocol errors (e.g. invalid command)?
            cmethod = getattr(self, '_do_{}'.format(data['command']))
            args = self._args(data)
            self._send(cmethod(*args))
            data = self._receive()
