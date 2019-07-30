import weakref

from python2.shared.codec import BaseDecodingSession, BaseEncodingSession


class ServerCodec():
    def __init__(self, server):
        self.server = weakref.proxy(server)

    def encoding_session(self):
        return ServerEncodingSession(self.server)

    def encode(self, obj, depth):
        return self.encoding_session().encode(obj, depth)

    def decoding_session(self):
        return ServerDecodingSession(self.server)

    def decode(self, obj):
        return self.decoding_session().decode(obj)


class ServerEncodingSession(BaseEncodingSession):
    """ Python 2 server object encoder. """

    def __init__(self, server):
        super(ServerEncodingSession, self).__init__()
        self.server = server

    def _enc_ref(self, obj):
        """ Encode an object as a reference. """
        self.server.cache_add(obj)
        return dict(type='ref', id=id(obj))


class ServerDecodingSession(BaseDecodingSession):
    def __init__(self, server):
        super(ServerDecodingSession, self).__init__()
        self.server = server

    def _dec_ref(self, data):
        """ Decode an object reference. """
        return self.server.cache_get(data['id'])
