import macropy.activate
import target
from copipes import pipeline



if __name__ == '__main__':
    p = pipeline(
        target.duplicate,
        target.duplicate,
        target.test_args.params(1),
        target.putStrLn)
    p.feed(xrange(30))
