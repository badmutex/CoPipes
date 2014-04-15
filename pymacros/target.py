from macropy.tracing import macros, trace, log
from macro_module import macros, print_ast, print_source, make_pipe
from copipes import null, coroutine

def my_coroutine(fn):
    with trace:
        return coroutine(fn)

@make_pipe
@my_coroutine
def test_args(a, b=42, c=24, **kws):
    [z]
    send(a+b+c+z)


@make_pipe
@coroutine
def putStrLn(*args, **kws):
    [v]
    print v

@make_pipe
@coroutine
def foo(*args, **kws):
    [a,b,c]
    print a
    z = 42
    send(a*b*c*z)

@make_pipe
@coroutine
# @print_source
def duplicate(*args, **kws):
    [x]
    send(x)
    send(x)

@coroutine
def duplicate2(*args, **kws):
    log[args, kws]
    __next_coroutine__ = kws.pop('next', null)
    while True:
        x = (yield )
        __next_coroutine__.send(x)
        __next_coroutine__.send(x)


# @print_ast
# @print_source
@coroutine
def duplicate3():
    next = kws.pop('next')
    while True:
        x = yield
        next.send(x)
        next.send(x)

# @print_ast
def bar(a, b, *rest, **kws):
    next = kws.pop('next', null)
    while True:
        a = yield
        b = yield
        c = yield
        next.send(a*b*c)
        next.send(a/b/c)
