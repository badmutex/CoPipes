from contextlib import contextmanager
from functools import update_wrapper
from os import linesep
from sys import version_info


__all__ = ['coroutine', 'pipeline', 'null']
__version__ = '0.1'
__author__ = 'Dmitry Vakhrushev <self@kr41.net>'
__license__ = 'BSD'


is2 = version_info[0] == 2


class _null(object):
    """
    A fake coroutine, which does nothing.

    The ``null`` is useful as pipeline end point or default value of next
    worker in coroutine definition:

    ..  code-block:: pycon

        >>> @coroutine
        ... def increment(next=null):
        ...     while True:
        ...         item = yield
        ...         next.send(item + 1)

    Also it's converted to boolean as ``False``:

    ..  code-block:: pycon

        >>> bool(null)
        False
        >>> next = null or increment
        >>> next
        increment

    """

    def __call__(self, *args, **kw):
        """ Mimics to coroutine initialization """
        return self

    def __nonzero__(self):
        """ Python 2.x boolean representation """
        return False

    def __bool__(self):
        """ Python 3.x boolean representation """
        return False

    def __repr__(self):
        """ String representation """
        return 'null'

    def send(self, *args, **kw):
        """ Mimics to coroutine processing """
        pass

    def close(self):
        """ Mimics to coroutine termination """
        pass


null = _null()


class coroutine(object):
    """
    Decorator turns callable to coroutine.

    Examples::

    ..  code-block:: pycon

        >>> @coroutine
        ... def increment(next=null):
        ...     while True:
        ...         item = yield
        ...         next.send(item + 1)

        >>> @coroutine
        ... def collect(target, next=null):
        ...     while True:
        ...         item = yield
        ...         target.append(item)
        ...         next.send(item)

        >>> target = []
        >>> inc = increment(collect(target))    # Init coroutines

        >>> inc.send(1)
        >>> inc.send(2)
        >>> inc.send(3)

        >>> target
        [2, 3, 4]

    """

    def __init__(self, func):
        self.func = func
        self.args = ()
        self.kw = {}
        update_wrapper(self, func)

    def __call__(self, *args, **kw):
        """ Returns initialized coroutine """
        pargs = self.args + args
        kwargs = self.kw.copy()
        kwargs.update(kw)
        c = self.func(*pargs, **kwargs)
        method = getattr(c, 'next' if is2 else '__next__')
        method()
        return c

    def __repr__(self):
        """ Returns string representation """
        params = [repr(a) for a in self.args]
        params.extend('{0!s}={1!r}'.format(k, v) for k, v in self.kw.items())
        params = ', '.join(params)
        return '{0}'.format(self.__name__) if not params else \
               '{0}.params({1})'.format(self.__name__, params)

    def params(self, *args, **kw):
        """
        Returns a parametrized copy of coroutine.

        Examples:

        ..  code-block:: pycon

            >>> @coroutine
            ... def increment(next=null):
            ...     while True:
            ...         item = yield
            ...         next.send(item + 1)

            >>> @coroutine
            ... def collect(target, next=null):
            ...     while True:
            ...         item = yield
            ...         target.append(item)
            ...         next.send(item)

            >>> target = []
            >>> collector = collect.params(target)
            >>> inc = increment(collector())    # Init coroutines

            >>> inc.send(1)
            >>> inc.send(2)
            >>> inc.send(3)

            >>> target
            [2, 3, 4]

        """
        p = self.__class__(self.func)
        p.args = args
        p.kw = kw
        return p


class pipeline(object):
    """ Coroutine pipeline. """

    def __init__(self, *workers):
        self.pipe = []
        self.connect(*workers)

    def __call__(self, next=null):
        """ Returns initialized coroutine pipeline """
        for worker in reversed(self.pipe):
            next = worker(next)
        return next

    def __repr__(self):
        """ Returns string representation """
        return linesep.join(repr(worker) for worker in self.pipe) or \
               '<empty pipeline>'

    def connect(self, *workers):
        self.pipe.extend(workers)

    def plug(self):
        self.pipe.append(null)

    @contextmanager
    def fork(self, worker, pipes_count):
        pipes = tuple(pipeline() for i in range(pipes_count))
        yield pipes
        self.connect(_fork(worker, *pipes))

    def feed(self, source):
        p = self()
        for item in source:
            p.send(item)
        p.close()


class _fork(object):
    """
    Forked coroutine pipeline is utility class.  You don't need to deal
    with it directly, use :meth:`pipeline.fork` method.

    """

    def __init__(self, worker, *pipes):
        self.worker = worker
        self.pipes = pipes

    def __call__(self, next):
        """ Returns initialized forked pipeline """
        pipes = (pipe(next) for pipe in self.pipes)
        return self.worker(*pipes)

    def __repr__(self):
        """ Returns string representation """
        result = [repr(self.worker) + ':']
        for pipe in self.pipes:
            result.append('    -->')
            result.extend(' ' * 8 + wr for wr in repr(pipe).split(linesep))
        return linesep.join(result)
