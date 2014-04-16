from macros import macros, debug_print_ast, debug_print_src, pipe
from copipes import null, coroutine, pipeline


@pipe
def collect(target):
    [x]
    target.append(x)
    send(x)

@pipe
def add(v):
    [x]
    send(x+v)

@pipe
def multiply(v):
    [x]
    send(x*v)

@pipe
def split(even, odd):
    [x]
    raise NotImplemented

@pipe
def putStrLn():
    [x]
    print x
    send(x)

@pipe
def replicate(n):
    [x]
    for i in xrange(n):
        send(x)
