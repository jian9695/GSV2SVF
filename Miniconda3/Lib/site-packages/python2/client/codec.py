import weakref

from python2.client.object import Py2Object
from python2.shared.codec import BaseDecodingSession, BaseEncodingSession


class ClientCodec():
    def __init__(self, client):
        self.client = weakref.proxy(client)

    def encoding_session(self):
        return ClientEncodingSession(self.client)

    def encode(self, obj):
        return self.encoding_session().encode(obj)

    def decoding_session(self):
        return ClientDecodingSession(self.client)

    def decode(self, obj):
        return self.decoding_session().decode(obj)


class ClientEncodingSession(BaseEncodingSession):
    def __init__(self, client):
        super(ClientEncodingSession, self).__init__()
        self.client = client

    def _enc_ref(self, obj):
        """ Encode an object as a reference. """
        if isinstance(obj, Py2Object):
            if obj is not self.client.get_object(obj.__oid__):
                raise ValueError("Py2Object {} belongs to a different Python2"
                                 " session".format(obj.__oid__))
            return dict(type='ref', id=obj.__oid__)
        else:
            raise TypeError("Cannot encode object of type {}".format(
                type(obj).__name__))


class ClientDecodingSession(BaseDecodingSession):
    def __init__(self, client):
        super(ClientDecodingSession, self).__init__()
        self.client = client

    def _dec_ref(self, data):
        """ Decode an object reference. """
        oid = data['id']
        obj = self.client.get_object(oid)
        if obj is None:
            obj = self.client.create_object(oid)
        return obj
