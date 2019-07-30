"""
Encoding and decoding classes for Python 2 client/server communication.

This module is used by both the Python 2 server and the Python 3 client, with
some modification to handle object references.

The encoding supports basic types and data structures.  Everything else will
be encoded as an opaque object reference.

The basic encoding algorithm involves recursively iterating over the members of
each container type.  For each object traversed, the encoder adds the object
to an internal cache.  If an object is seen again, it is encoded as a pointer
to the previous occurrence.  The decoder traverses the encoding in the same
order and maintains a similar cache which is used to translate cache pointers.

This simple algorithm runs into trouble when dealing with tuples containing
circular references.  During decoding, a tuple's members must be decoded
before the tuple can be created, since the tuple is immutable after
instantiation.  But this would create a problem if we encounter a cache pointer
to the tuple before the tuple had been instantiated.

To resolve this issue, we must modify the simple preorder traversal initially
described.  When we encounter a mutable collection (list or dict)*, we
initially create an empty placeholder for the collection and come back to it
later once we have traversed all other reachable objects.  This ensures that by
the time we encounter a cache pointer the cached object is guaranteed to be
initialized.

For example, suppose we have the following tuple `T`::

    T = ([T], 1)

When encoding, we initially add `T` to the cache.  Then we encounter the list
`[T]`.  We create a placeholder in the encoding and remember it for later.
Next we encode `1`.  Finally, we return to `[T]` and recur into the list.
Since `T` is in the cache, we encode the nested occurrence as a cache pointer.

When decoding, we begin decoding the elements of `T`.  When we get to the
encoding of `[T]`, we create an empty list and continue, remembering our place
for later. Then we decode `1` and initialize `T` to `([], 1)`, storing it in
the cache. Next we return to the encoded list update the list with its decoded
contents. When we get to the cache reference for `T`, we can look it up in the
cache with no problems since it has already been initialized.

*It is not necessary to do the placeholder procedure for sets, even though they
are mutable, because any circularly-referential data structure must contain a
mutable object, which makes it unhashable.
"""


# Possible improvements:
#
# - Is the complexity really worth it? How likely are circular references
#   anyway?
#
#     - Could detect and error out instead, or document as a limitation
#
# - Current algorithm requires encoding/decoding to occur in consistent order
#   within session.  Can we avoid this?
#
# - Is there a way to avoid incurring the costs of caching when not needed?
#   maybe a two-pass algorithm that checks before encoding?


import base64
import collections
import sys


PYTHON_VERSION = sys.version_info[0]
if PYTHON_VERSION == 2:
    _long = long  # noqa
    _bytes = str
    _unicode = unicode  # noqa
    _range = xrange  # noqa
    _items = dict.iteritems
elif PYTHON_VERSION == 3:
    _long = int
    _bytes = bytes
    _unicode = str
    _range = range
    _items = dict.items
else:
    raise Exception("Unsupported Python version: {}".format(PYTHON_VERSION))


_value_types = frozenset({
    type(None), type(NotImplemented), type(Ellipsis), bool, int, _long, float,
    complex, _bytes, _unicode, bytearray, _range
})
_container_types = frozenset({slice, list, tuple, set, frozenset, dict})
_supported_types = _value_types | _container_types


class EncodingDepth(object):
    """ Common values for encoding depth. """
    REF = 0  # Encode as a reference
    SHALLOW = 1  # Convert top-level object to value
    DEEP = -1  # Recursively convert object to value


class BaseEncodingSession(object):
    """ Base encoder for Python 2 client and server. """

    def __init__(self):
        self.session = {}
        self.deferred = collections.deque()

    def encode(self, obj, depth=EncodingDepth.DEEP):
        """ Encode an object. """

        data = self._enc(obj, depth)
        while self.deferred:
            self.deferred.popleft()()

        return data

    def _enc(self, obj, depth):
        t = type(obj)
        if depth and any(t is s for s in _supported_types):
            if t in _container_types:
                # For container types, we include the depth in the cache key.
                # This means that if encoding to a finite depth, a given
                # container object will be encoded separately at each depth
                # where it occurs.
                key = id(obj), max(depth, -1)
            else:
                key = id(obj)
            if key in self.session:
                return dict(type='cached', index=self.session[key][0])
            # Store cached objects to prevent garbage collection
            # This ensures that ids uniquely map to objects over the life of
            # the session. We can't use a WeakKeyDictionary to avoid this
            # because most builtin types do not support weak references.
            self.session[key] = len(self.session), obj

            # Singleton objects
            if obj is None:
                return dict(type='None')
            elif obj is NotImplemented:
                return dict(type='NotImplemented')
            elif obj is Ellipsis:
                return dict(type='Ellipsis')

            # Numerical types
            elif t is bool:
                return dict(type='bool', value=obj)
            elif t is int or t is _long:
                return dict(type='int', value=obj)
            elif t is float:
                return dict(type='float', value=obj)
            elif t is complex:
                return dict(type='complex', real=obj.real, imag=obj.imag)

            # String types
            elif t is _bytes:
                return self._enc_bdata('bytes', obj)
            elif t is _unicode:
                return self._enc_bdata('unicode', obj.encode('utf8'))
            elif t is bytearray:
                return self._enc_bdata('bytearray', obj)

            # Range and slice
            elif t is _range:
                return self._enc_range(obj)
            elif t is slice:
                return dict(type='slice',
                            start=self._enc(obj.start, depth-1),
                            stop=self._enc(obj.stop, depth-1),
                            step=self._enc(obj.step, depth-1))

            # Container types
            elif t is list:
                d = dict(type='list', items=Placeholder)
                self.deferred.append(
                    lambda: d.update(items=self._enc_items(obj, depth-1)))
                return d
            elif t is tuple:
                return dict(type='tuple', items=self._enc_items(obj, depth-1))
            elif t is set:
                return dict(type='set', items=self._enc_items(obj, depth-1))
            elif t is frozenset:
                return dict(type='frozenset',
                            items=self._enc_items(obj, depth-1))
            elif t is dict:
                d = dict(type='dict', items=Placeholder)
                self.deferred.append(
                    lambda: d.update(items=[self._enc_kv(key, value, depth-1)
                                     for key, value in _items(obj)]))
                return d
            else:
                # Should never happen
                raise AssertionError("Unexpected type: {}".format(t.__name__))

        # Encode as reference
        return self._enc_ref(obj)

    def _enc_bdata(self, type_, data):
        """ Encode binary data. """
        return dict(type=type_, data=base64.b64encode(data).decode('ascii'))

    def _enc_items(self, itr, depth):
        """ Encode a collection of items. """
        return [self._enc(item, depth) for item in itr]

    if PYTHON_VERSION == 2:
        def _enc_range(self, range_):
            """ Encode a range object. """
            start, stop, step = range_.__reduce__()[1]
            return dict(type='range', start=start, stop=stop, step=step)
    else:
        def _enc_range(self, range_):
            """ Encode a range object. """
            return dict(type='range', start=range_.start, stop=range_.stop,
                        step=range_.step)

    def _enc_kv(self, key, value, depth):
        """ Encode a dict key-value pair. """
        return dict(key=self._enc(key, depth), value=self._enc(value, depth))

    def _enc_ref(self, obj):
        """ Encode an object as a reference. """
        # Implemented by client/server subclasses
        raise NotImplemented()


class BaseDecodingSession(object):
    """ Base decoder for Python 2 client and server. """

    def __init__(self):
        self.session = []
        self.deferred = collections.deque()

    def decode(self, data):
        obj = self._dec(data)
        while self.deferred:
            self.deferred.popleft()()

        return obj

    def _dec(self, data):
        """ Decode an encoded object. """

        dtype = data['type']

        if dtype == 'ref':
            return self._dec_ref(data)

        if dtype == 'cached':
            assert self.session[data['index']] is not Placeholder
            return self.session[data['index']]

        cache_index = len(self.session)
        self.session.append(Placeholder)

        def _cache(obj):
            self.session[cache_index] = obj
            return obj

        # Singleton objects
        if dtype == 'None':
            return _cache(None)
        elif dtype == 'NotImplemented':
            return _cache(NotImplemented)
        elif dtype == 'Ellipsis':
            return _cache(Ellipsis)

        # Numeric types
        elif dtype in ('bool', 'int', 'float'):
            return _cache(data['value'])
        elif dtype == 'complex':
            return _cache(complex(real=data['real'], imag=data['imag']))

        # String types
        elif dtype == 'bytes':
            return _cache(self._dec_bdata(data))
        elif dtype == 'unicode':
            return _cache(self._dec_bdata(data).decode('utf8'))
        elif dtype == 'bytearray':
            return _cache(bytearray(self._dec_bdata(data)))

        # Range and slice
        elif dtype == 'range':
            return _cache(_range(data['start'], data['stop'], data['step']))
        elif dtype == 'slice':
            return _cache(slice(self._dec(data['start']),
                                self._dec(data['stop']),
                                self._dec(data['step'])))

        # Container types
        elif dtype == 'list':
            lst = _cache([])
            self.deferred.append(lambda: lst.extend(self._dec_items(data)))
            return lst
        elif dtype == 'tuple':
            return _cache(tuple(self._dec_items(data)))
        elif dtype == 'set':
            return _cache(set(self._dec_items(data)))
        elif dtype == 'frozenset':
            return _cache(frozenset(self._dec_items(data)))
        elif dtype == 'dict':
            dct = _cache({})
            self.deferred.append(
                lambda: dct.update(self._dec_dict_items(data)))
            return dct
        else:
            raise TypeError("Invalid data type: {}".format(dtype.__name__))

    def _dec_bdata(self, data):
        return base64.b64decode(data['data'].encode('ascii'))

    def _dec_items(self, data):
        return (self._dec(item) for item in data['items'])

    def _dec_dict_items(self, data):
        return ((self._dec(kv['key']), self._dec(kv['value']))
                for kv in data['items'])

    def _dec_ref(self, data):
        """ Decode an object reference. """
        # Implemented by client/server subclasses
        raise NotImplemented()


class PlaceholderType(object):
    """
    Type for a singleton object to be used as a placeholder.
    """
    __slots__ = ()
    __hash__ = None  # Should not be used as a dict key or set member


Placeholder = PlaceholderType()
