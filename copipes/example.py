"""
The following example demonstrates common use cases of CoPipes library.

The task is to parse fake log file.  The file contains messages from three
modules.  We need to remove all debug messages and split the log into four
ones.  Three files for each module and last one for errors and warnings.
Last file should not contain duplicate records.

"""

import os
import sys
from io import StringIO
from collections import namedtuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from copipes import coroutine, pipeline, null


log = StringIO(u"""
    WARNING first  Warning message 1
    DEBUG   second Debug message 4
    INFO    third  Info message 1
    WARNING third  Warning message 1
    INFO    third  Info message 1
    DEBUG   third  Debug message 2
    ERROR   first  Error message 2
    INFO    third  Info message 3
    DEBUG   second Debug message 5
    ERROR   second Error message 4
    ERROR   third  Error message 4
    ERROR   third  Error message 3
    INFO    first  Info message 5
    DEBUG   second Debug message 3
    ERROR   second Error message 5
    WARNING first  Warning message 4
    DEBUG   third  Debug message 5
    DEBUG   first  Debug message 3
    DEBUG   second Debug message 2
    DEBUG   first  Debug message 3
    WARNING first  Warning message 1
    INFO    first  Info message 3
    WARNING third  Warning message 3
    WARNING second Warning message 5
    ERROR   first  Error message 3
""")


@coroutine
def parse(next=null):
    LogRecord = namedtuple('LogRecord', ['level', 'module', 'message'])
    while True:
        line = yield
        line = line.strip()
        if not line:
            # Skip blank line
            continue
        level, module, message = line.split(None, 2)
        next.send(LogRecord(level, module, message))


@coroutine
def broadcast(*channels):
    while True:
        record = yield
        for channel in channels:
            channel.send(record)


@coroutine
def split(selector, **channels):
    while True:
        record = yield
        channel = selector(record)
        channels[channel].send(record)


@coroutine
def filter(condition, next=null):
    while True:
        record = yield
        if condition(record):
            next.send(record)


@coroutine
def unique(next=null):
    passed = set()
    while True:
        record = yield
        if record in passed:
            continue
        passed.add(record)
        next.send(record)


@coroutine
def save(file, next=null):
    while True:
        record = yield
        file.write(u'{0.level:7.7} {0.module:6.6} {0.message}\n'.format(record))
        next.send(record)


if __name__ == '__main__':
    error_log = StringIO()
    first_log = StringIO()
    second_log = StringIO()
    third_log = StringIO()

    p = pipeline(
        parse,
        filter.params(lambda r: r.level != 'DEBUG'),
    )
    with p.fork(broadcast, 2) as (modules, errors):
        module_names = ()
        with modules.fork(split.params(lambda r: r.module),
                         'first', 'second', 'third') as (first, second, third):
            first.connect(save.params(first_log))
            second.connect(save.params(second_log))
            third.connect(save.params(third_log))

        errors.connect(
            filter.params(lambda r: r.level in ('ERROR', 'WARNING')),
            unique,
            save.params(error_log)
        )

    p.feed(line for line in log)

    print('---------------------------------')
    print('First log:\n')
    print(first_log.getvalue())

    print('---------------------------------')
    print('Second log:\n')
    print(second_log.getvalue())

    print('---------------------------------')
    print('Third log:\n')
    print(third_log.getvalue())

    print('---------------------------------')
    print('Error log:\n')
    print(error_log.getvalue())
