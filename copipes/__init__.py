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
        >>> inc = increment()
        >>> inc.send(1)         # No exception is raised

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
        # Python 2.x boolean representation
        return False

    def __bool__(self):
        # Python 3.x boolean representation
        return False

    def __repr__(self):
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
    """
    Coroutine pipeline is utility class to connect number of coroutines into
    single pipeline.  The main goal is readability.  The following examples
    of code are equal:

    ..  code-block:: pycon

        >>> @coroutine
        ... def collect(target, next=null):
        ...     while True:
        ...         item = yield
        ...         target.append(item)
        ...         next.send(item)

        >>> @coroutine
        ... def increment(next=null):
        ...     while True:
        ...         item = yield
        ...         next.send(item + 1)

        >>> # Without pipelines
        >>> result = []
        >>> p = increment(collect(result))
        >>> for i in [1, 2, 3]:
        ...     p.send(i)
        >>> p.close()

        >>> # With pipelines
        >>> result = []
        >>> p = pipeline(
        ...     increment,
        ...     collect.params(result),
        ... )
        >>> p.feed([1, 2, 3])

    Pipeline also provides a readable representation, which is useful in debug:

    ..  code-block:: pycon

        >>> p
        increment
        collect.params([2, 3, 4])

    """

    def __init__(self, *workers):
        self.pipe = []
        self.connect(*workers)

    def __call__(self, next=null):
        """ Returns initialized coroutine pipeline """
        for worker in reversed(self.pipe):
            next = worker(next)
        return next

    def __repr__(self):
        return linesep.join(repr(worker) for worker in self.pipe) or \
               '<empty pipeline>'

    def connect(self, *workers):
        """
        Connect to pipeline passed coroutines.

        Examples:

        ..  code-block:: pycon

            >>> @coroutine
            ... def collect(target, next=null):
            ...     while True:
            ...         item = yield
            ...         target.append(item)
            ...         next.send(item)

            >>> @coroutine
            ... def increment(next=null):
            ...     while True:
            ...         item = yield
            ...         next.send(item + 1)

            >>> result = []
            >>> p = pipeline()
            >>> p.connect(increment, collect.params(result))
            >>> p.feed([1, 2, 3])
            >>> result
            [2, 3, 4]

        """
        self.pipe.extend(workers)

    def plug(self):
        """ Plug pipeline, i.e. connect ``null`` to pipeline """
        self.pipe.append(null)

    @contextmanager
    def fork(self, worker, *pipes):
        """
        Connect to pipeline forked coroutine.  The method is a context manager.
        The first argument is a coroutine.  If the second one is a number, then
        this number of pipelines will be created and passed to coroutine as
        positional arguments during initialization.  If the second argument and
        next ones are strings, then coroutine will be initialized using
        keyword arguments.

        Examples:

        ..  code-block:: pycon

            >>> @coroutine
            ... def collect(target, next=null):
            ...     while True:
            ...         item = yield
            ...         target.append(item)
            ...         next.send(item)

            >>> @coroutine
            ... def split(even=null, odd=null):
            ...     while True:
            ...         item = yield
            ...         next = odd if item % 2 else even
            ...         next.send(item)

            >>> evens = []
            >>> odds = []
            >>> p = pipeline()
            >>> with p.fork(split, 2) as (even, odd):
            ...     # ``p.fork(split, 'even', 'odd')`` is also correct
            ...     even.connect(collect.params(evens))
            ...     odd.connect(collect.params(odds))

            >>> p.feed([1, 2, 3, 4])
            >>> evens
            [2, 4]
            >>> odds
            [1, 3]

        Note, forked pipelines are joined at the end of fork.  This means that
        if you connect some coroutines after fork, it will be connected to each
        of forked pipeline.  To prevent this behavior call :meth:`plug` on the
        forked pipeline.

        ..  code-block:: pycon

            >>> @coroutine
            ... def broadcast(*next):
            ...     while True:
            ...         item = yield
            ...         for n in next:
            ...             n.send(item)

            >>> @coroutine
            ... def increment(next=null):
            ...     while True:
            ...         item = yield
            ...         next.send(item + 1)

            >>> @coroutine
            ... def decrement(next=null):
            ...     while True:
            ...         item = yield
            ...         next.send(item - 1)

            >>> incremented = []
            >>> decremented = []
            >>> original = []
            >>> result = []
            >>> p = pipeline()
            >>> with p.fork(broadcast, 3) as (inc, dec, orig):
            ...     inc.connect(increment, collect.params(incremented))
            ...     dec.connect(decrement, collect.params(decremented))
            ...     orig.connect(collect.params(original))
            ...     orig.plug()
            >>> p.connect(collect.params(result))

            >>> p.feed([1, 2, 3])
            >>> incremented
            [2, 3, 4]
            >>> decremented
            [0, 1, 2]
            >>> original
            [1, 2, 3]
            >>> result
            [2, 0, 3, 1, 4, 2]

        The representation of forked pipeline looks like:

        ..  code-block:: pycon

            >>> p
            broadcast:
                -->
                    increment
                    collect.params([2, 3, 4])
                -->
                    decrement
                    collect.params([0, 1, 2])
                -->
                    collect.params([1, 2, 3])
                    null
            collect.params([2, 0, 3, 1, 4, 2])

        """
        if isinstance(pipes[0], int):
            pipe_count = pipes[0]
            pipe_names = None
        else:
            pipe_count = len(pipes)
            pipe_names = pipes
        pipes = tuple(pipeline() for i in range(pipe_count))
        yield pipes
        if pipe_names:
            self.connect(_fork(worker, **dict(zip(pipe_names, pipes))))
        else:
            self.connect(_fork(worker, *pipes))

    def feed(self, source):
        """
        Feed pipeline using items from ``source``.

        The method initializes pipeline, feeds it, then closes it.

        """
        p = self()
        for item in source:
            p.send(item)
        p.close()


class _fork(object):
    """
    Forked coroutine pipeline is utility class.  You don't need to deal
    with it directly, use :meth:`pipeline.fork` method.

    """

    def __init__(self, worker, *pipes, **named_pipes):
        self.worker = worker
        self.pipes = pipes
        self.named_pipes = named_pipes

    def __call__(self, next):
        """ Returns initialized forked pipeline """
        pipes = (pipe(next) for pipe in self.pipes)
        named_pipes = dict((name, pipe(next)) for name, pipe
                                              in self.named_pipes.items())
        return self.worker(*pipes, **named_pipes)

    def __repr__(self):
        result = [repr(self.worker) + ':']
        for pipe in self.pipes:
            result.append('    -->')
            result.extend(' ' * 8 + wr for wr in repr(pipe).split(linesep))
        for name, pipe in self.named_pipes.items():
            result.append('    {0} -->'.format(name))
            result.extend(' ' * 8 + wr for wr in repr(pipe).split(linesep))
        return linesep.join(result)
