from macropy.core.macros import *
from macropy.core.quotes import macros, q, u, ast
from macropy.experimental.pattern import macros, switch

macros = Macros()

@macros.decorator
def print_ast(tree, **kws):
    # import pdb; pdb.set_trace()
    @Walker
    def pprint(tree, collect, **kws):
        print real_repr(tree)
        return tree
    _, names = pprint.recurse_collect(tree)
    return tree

@macros.decorator
def print_source(tree, **kws):
    print unparse(tree).strip()
    return tree

def params_has_name_p(args, name):
    for arg in args.args:
        if arg.id == name:
            return True
    return False

def generate_next(args, gen_sym, **kws):
    """
    return ident, tree
    <ident> = kws.pop('next', null)
    """
    ident = 'next'
    if not params_has_name_p(args, ident):
        args.args.append(Name(ident, Param()))
        args.defaults.append(Name('null', Load()))

    # kws = args.kwarg
    # new_t = Assign([Name(ident, Store())],
    #                Call(Attribute(Name(kws, Load()), 'pop', Load()),
    #                     [Str('next'), Name('null', Load())],
    #                     [], None, None))

    return ident, args

def _rewrite_send(next, body):
    """
    replace each occurence of a call to `send(...)` with `<next_ident>.send(...)`
    """

    @Walker
    def rewrite(tree, **kws):
        # send(...) -> next.send(...)
        if type(tree) is Call and type(tree.func) is Name and tree.func.id == 'send':
            new_t = Call(Attribute(Name(next, Load()), 'send', Load()),
                         tree.args, tree.keywords, tree.starargs, tree.kwargs)
            return new_t
        else:
            return tree

    new_tree = rewrite.recurse(body)
    return new_tree

def generate_while(recv_names, next, body):
    """
    return tree
    while True:
        <receive stmts>
        <body>
    """
    test     = Name('True', Load())
    new_body = [generate_receive(name) for name in recv_names]
    new_body+= _rewrite_send(next, body)
    orElse   = []
    return While(test, new_body, orElse)

def generate_receive(name):
    """
    returns tree
    <ident> = yield
    """
    tree  = Assign([Name(name, Store())], Yield(None))
    return tree

def generate_receives(expr):
    elts = expr.value.elts
    receives = map(generate_receive, elts)
    return receives

@macros.decorator
def make_pipe(tree, gen_sym, **kws):
    func = tree
    body = func.body.pop(0)
    Prms = map(lambda name: name.id, body.value.elts)
    next, Next = generate_next(func.args, gen_sym)
    While = generate_while(Prms, next, func.body)

    new_body = [While]
    tree.body = new_body
    return tree




"""
Goal:

@pipe
def pipe(*params, **kws):
    [a, b, c] #-> Expr(List([Name('a', Load()), Name('b', Load()), Name('c', Load())], Load()))
    send(a * b - c) #-> Expr(Call(Name('send', Load()), ...))

becomes

@copipes.coroutine
def pipe(*params, **kws):
    next = kws.pop('next', copipes.null)
    while True:
        a = yield #-> Assign([Name('a', Store())], Yield(None))
        b = yield #-> Assign([Name('b', Store())], Yield(None))
        c = yield #-> Assign([Name('c', Store())], Yield(None))
        r = a * b - c
        next.send(r)


pipe macro:
def <name>(*params, *kws):
    # receive values to:
    <list: names to receive to>
    # send results to:
    next1234 = kws.pop('next', copiples.null)

    <body>

Steps:

 1. params: find irst elemnt of python ast.FunctionDef.body
    body = funcdef.body
    params = body.pop(0)
    newbody = []
    - params :: type should be <list> or <tuple>
    - each param gets `gen_sym()` called
      for p in params:
          name = gen_sym()
          entry = [u[name] = u[yield]]
          newbody.append(entry)
      newbody.extend(body)

  2. generate
      

"""
