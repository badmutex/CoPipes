from macropy.core.macros import *
import copy

macros = Macros()

@macros.decorator
def debug_print_ast(tree, **kws):
    """Print the AST"""
    @Walker
    def print_node(tree, **kws):
        print real_repr(tree)
        return tree
    print_node.recurse(tree)
    return tree

@macros.decorator
def debug_print_src(tree, **kws):
    """Print the python code for the AST"""
    print unparse(tree).strip()
    return tree


def arguments_has_ident(args, ident):
    """Check of the `ast.arguments` has an identifier"""
    for a in args.args:
        if a.id == ident:
            return True
    return False

def rewrite__specify_next_coroutine(args, next='next'):
    """
    Rewrite the Arguments to have a `next=null` defaults

    Params:
      function_args :: ast.arguments
    """
    if not arguments_has_ident(args, next):
        # add `next=null` to the arguments
        args.args.append(Name(next, Param()))
        args.defaults.append(Name('null', Load()))


def rewrite__expand_send(next_ident, tree):
    """Replace each `send(...)` with `<next_ident>.send(...)"""
    @Walker
    def rewrite(tree, **kws):
        if     type(tree)      is Call and \
               type(tree.func) is Name and \
               tree.func.id    == 'send':

            new_tree = Call(Attribute(Name(next_ident, Load()),
                                     'send', Load()),
                            tree.args, tree.keywords, tree.starargs, tree.kwargs)
            return new_tree
        else:
            return tree

    return rewrite.recurse(tree)


def rewrite__create_while_loop(body):
    """Create the `While True: ...` loop"""
    test   = Name('True', Load())
    orElse = []
    return While(test, body, orElse)

def rewrite__create_recvs(idents):
    def recv(name):
        return Assign([Name(name, Store())], Yield(None))
    return [recv(n.id) for n in idents]

def rewrite_args(args, next='next'):
    new_args = copy.deepcopy(args)
    rewrite__specify_next_coroutine(new_args, next=next)
    return new_args

def rewrite_body(body, next='next'):
    new_body = copy.deepcopy(body)
    idents   = new_body.pop(0).value.elts
    recvs    = rewrite__create_recvs(idents)
    new_body = recvs + new_body
    new_body = rewrite__expand_send(next, new_body)
    loop     = rewrite__create_while_loop(new_body)
    return [loop]

def rewrite(tree):
    print 20*'='
    func = tree
    next_ident = 'next'
    new_args   = rewrite_args(func.args, next=next_ident)
    new_body   = rewrite_body(func.body, next=next_ident)
    new_decs   = copy.copy(func.decorator_list) + [Name('coroutine', Load())]
    new_func   = FunctionDef(name=func.name,
                             args=new_args,
                             body=new_body,
                             decorator_list=new_decs,
                            )
    debug_print_src(tree)
    print 20*'^'
    debug_print_src(new_func)
    return new_func


@macros.decorator
def pipe(tree, **kws):
    return rewrite(tree)
