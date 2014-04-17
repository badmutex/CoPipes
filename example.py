from copipes import coroutine, pipeline, null
from copipes.macros.pipe import pipe


@pipe
def putStrLn():
    """doc"""
    [x]
    print x
    send(x)

@pipe
def replicate(n):
    [x]
    for i in xrange(n):
        send(x)

if __name__ == '__main__':
    pipeline(
        putStrLn,
        replicate.params(3),
        putStrLn,
    ).feed(range(10))
