class Py2Error(Exception):
    """
    Exception raised when a Python 2 operation throws an exception.

    The underlying Python 2 exception object is stored as the `exception`
    attribute.
    """

    def __init__(self, *args, exception):
        super(Py2Error, self).__init__(*args)
        self.exception = exception

    def __repr__(self):
        return "<{} {!r}>".format(self.__class__.__name__, self.exception)
