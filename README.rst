A library provides utilities for creating data-processing pipelines based
on coroutines and generators.  An idea is described in David Beazley's
presentations:

*   `Generator Tricks for Systems Programmers
    <http://www.dabeaz.com/generators/>`_
*   `A Curious Course on Coroutines and Concurrency
    <http://www.dabeaz.com/coroutines/>`_

For example, you need to process log file::

    >>> from io import StringIO
    >>> source = StringIO('''
    ...     01-01-2000 12:00 [INFO] Info message 1
    ...     01-01-2000 12:10 [WARN] Warning message 1
    ...     01-01-2000 12:20 [WARN] Warning message 2
    ...     01-01-2000 12:30 [INFO] Info message 2
    ...     01-01-2000 12:40 [ERROR] Error message 1
    ...     01-01-2000 12:50 [INFO] Info message 3
    ...     01-01-2000 13:00 [ERROR] Error message 2
    ... ''')

Create some workers::

    >>> from copipes import coroutine
    >>> @coroutine
    ... def parse(next):
    ...     while True:
    ...         item = yield
    ...         date, time, type, msg = item.strip().split(' ', 3)
    ...         next.send({
    ...             'date': date,
    ...             'time': time,
    ...             'type': type,
    ...             'msg': msg,
    ...         })
    ...
    >>> @coroutine
    ... def filter(cond, next):
    ...     while True:
    ...         item = yield
    ...         if cond(item):
    ...             next.send(item)
    ...
    >>> @coroutine
    ... def split(info, warn, error):
    ...     map = {
    ...         '[INFO]': info,
    ...         '[WARN]': warn,
    ...         '[ERROR]': error,
    ...     }
    ...     while True:
    ...         item = yield
    ...         map[item['type']].send(item)
    ...
    >>> @coroutine
    ... def echo(next, prefix=''):
    ...     while True:
    ...         item = yield
    ...         print(prefix + item['msg'])
    ...         next.send(item)
    ...
    >>> @coroutine
    ... def write(f, next):
    ...     while True:
    ...         item = yield
    ...         f.write(' '.join((item['date'], item['time'],
    ...                           item['type'], item['msg'])))
    ...         f.write('\\n')
    ...         next.send(item)
    ...

Connect workers to pipeline::

    >>> from copipes import pipeline
    >>> output = StringIO()
    >>> p = pipeline(
    ...     filter.params(lambda line: line.strip()),
    ...     parse,
    ... )
    ...
    >>> with p.fork(split, 3) as (info, warn, error):
    ...     info.plug()
    ...     error.connect(
    ...         filter.params
    ...         echo.params(prefix='! ')
    ...     )
    ...
    >>> p.connect(write.params(output))
    >>> print(repr(p))                                   # doctest: +ELLIPSIS
    filter.params(<function <lambda> at ...>)
    parse
    split:
        -->
            null
        -->
            <empty pipeline>
        -->
            echo.params(prefix='! ')
    write.params(<...>)
    >>> p.feed(source)
    ! Error message 1
    ! Error message 2
    >>> print(output.getvalue())
    01-01-2000 12:10 [WARN] Warning message 1
    01-01-2000 12:20 [WARN] Warning message 2
    01-01-2000 12:40 [ERROR] Error message 1
    01-01-2000 13:00 [ERROR] Error message 2
    <BLANKLINE>
