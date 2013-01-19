from textwrap import dedent

from nose import tools

from copipes import coroutine, pipeline, null


@coroutine
def collect(target, next):
    """ Connects pipeline to queue """
    while True:
        item = yield
        target.append(item)
        next.send(item)


@coroutine
def add(value, next):
    """ Adds specified ``value`` to each item passed to pipeline """
    while True:
        item = yield
        next.send(item + value)


@coroutine
def multiply(value, next):
    """ Multiplies specified ``value`` by each item passed to pipeline """
    while True:
        item = yield
        next.send(item * value)


@coroutine
def split(even, odd):
    """ Splits up items to evens and odd """
    while True:
        item = yield
        next = odd if item % 2 else even
        next.send(item)


def null_test():
    tools.ok_(not null)
    tools.ok_(null() is null)

    # Following code should not raise an exception
    null.send(1, 2, 3)
    null.close()


def coroutine_preserves_name_and_docstring_test():
    tools.eq_(add.__name__, 'add')
    tools.eq_(add.__doc__, ' Adds specified ``value`` to each'
                           ' item passed to pipeline ')
    tools.eq_(repr(add), 'add')


def parametrized_coroutine_test():
    add_5 = add.params(5)
    add_3 = add.params(3)

    # Parametrized coroutine provides readable representation
    tools.eq_(repr(add_5), 'add.params(5)')
    tools.eq_(repr(add_3), 'add.params(3)')

    result_5 = []
    result_3 = []

    pipeline(add_5, collect.params(result_5)).feed([1, 2, 3])
    pipeline(add_3, collect.params(result_3)).feed([1, 2, 3])
    tools.eq_(result_5, [6, 7, 8])
    tools.eq_(result_3, [4, 5, 6])


def straight_forward_pipeline_test():
    result = []
    p = pipeline(
        multiply.params(10),
        add.params(5),
    )
    p.connect(
        add.params(1),
        collect.params(result),
    )
    p.feed([1, 2, 3, 4])
    tools.eq_(result, [16, 26, 36, 46])


def forked_pipeline_test():
    evens = []
    odds = []
    p = pipeline()
    with p.fork(split, 2) as (even, odd):
        even.connect(
            multiply.params(10),
            collect.params(evens)
        )
        odd.connect(
            add.params(10),
            collect.params(odds)
        )
    p.feed([1, 2, 3, 4])
    tools.eq_(evens, [20, 40])
    tools.eq_(odds, [11, 13])


def forked_named_pipeline_test():
    evens = []
    odds = []
    p = pipeline()
    with p.fork(split, 'odd', 'even') as (odd, even):
        even.connect(
            multiply.params(10),
            collect.params(evens)
        )
        odd.connect(
            add.params(10),
            collect.params(odds)
        )
    p.feed([1, 2, 3, 4])
    tools.eq_(evens, [20, 40])
    tools.eq_(odds, [11, 13])


def plugged_pipeline_test():
    result = []
    null = []
    p = pipeline(
        multiply.params(10),
        collect.params(result),
    )
    p.plug()
    p.connect(
        add.params(1),
        collect.params(null),
    )
    p.feed([1, 2, 3, 4])
    tools.eq_(result, [10, 20, 30, 40])
    tools.eq_(null, [])


def complex_pipeline_test():
    odds = []
    evens = []
    result = []
    p = pipeline(
        add.params(1)
    )
    with p.fork(split, 2) as (even, odd):
        even.connect(
            collect.params(evens),
            multiply.params(2),
            add.params(5),
        )
        odd.connect(
            collect.params(odds),
            multiply.params(5),
            add.params(2),
        )
    p.connect(
        collect.params(result)
    )
    p.feed([1, 2, 3, 4])
    tools.eq_(evens, [2, 4])
    tools.eq_(odds, [3, 5])
    tools.eq_(result, [9, 17, 13, 27])


def pipeline_representation_test():
    p = pipeline(
        add.params(1)
    )
    with p.fork(split, 2) as (even, odd):
        even.connect(
            multiply.params(2),
            add.params(5),
        )
        odd.connect(
            multiply.params(5),
            add.params(2),
        )
    p.connect(
        add.params(2)
    )
    tools.eq_(repr(p).strip(), dedent("""
    add.params(1)
    split:
        -->
            multiply.params(2)
            add.params(5)
        -->
            multiply.params(5)
            add.params(2)
    add.params(2)
    """).strip())
