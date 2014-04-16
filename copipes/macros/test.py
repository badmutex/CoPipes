import macropy.activate
# from test_target import pipeline, null, collect, add, multiply, split, putStrLn, replicate
# from nose import tools


# def parametrized_coroutine_test():
#     add_5 = add.params(5)
#     add_3 = add.params(3)

#     # Parametrized coroutine provides readable representation
#     tools.eq_(repr(add_5), 'add.params(5)')
#     tools.eq_(repr(add_3), 'add.params(3)')

#     result_5 = []
#     result_3 = []

#     pipeline(add_5, collect.params(result_5)).feed([1, 2, 3])
#     pipeline(add_3, collect.params(result_3)).feed([1, 2, 3])
#     tools.eq_(result_5, [6, 7, 8])
#     tools.eq_(result_3, [4, 5, 6])

    
# def straight_forward_pipeline_test():
#     result = []
#     p = pipeline(
#         multiply.params(10),
#         add.params(5),
#     )
#     p.connect(
#         add.params(1),
#         collect.params(result),
#     )
#     p.feed([1, 2, 3, 4])
#     tools.eq_(result, [16, 26, 36, 46])

# def forked_pipeline_test():
#     raise NotImplemented

# def forked_named_pipeline_test():
#     raise NotImplemented


# def plugged_pipeline_test():
#     result = []
#     null = []
#     p = pipeline(
#         multiply.params(10),
#         collect.params(result),
#     )
#     p.plug()
#     p.connect(
#         add.params(1),
#         collect.params(null),
#     )
#     p.feed([1, 2, 3, 4])
#     tools.eq_(result, [10, 20, 30, 40])
#     tools.eq_(null, [])


# def complex_pipeline_test():
#     odds = []
#     evens = []
#     result = []
#     p = pipeline(
#         add.params(1)
#     )
#     with p.fork(split, 2) as (even, odd):
#         even.connect(
#             collect.params(evens),
#             multiply.params(2),
#             add.params(5),
#         )
#         odd.connect(
#             collect.params(odds),
#             multiply.params(5),
#             add.params(2),
#         )
#     p.connect(
#         collect.params(result)
#     )
#     p.feed([1, 2, 3, 4])
#     tools.eq_(evens, [2, 4])
#     tools.eq_(odds, [3, 5])
#     tools.eq_(result, [9, 17, 13, 27])



# if __name__ == '__main__':
    
#     p = pipeline(
#         putStrLn,
#         replicate.params(3),
#         putStrLn
#         )
#     print p
#     p.feed(xrange(10))

