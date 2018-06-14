import py
from rpython.rlib.parsing.ebnfparse import parse_ebnf, make_parse_function
from nolst import bytecode

grammar = py.path.local("./nolst/").join('grammar.txt').read("rt")
regexs, rules, ToAST = parse_ebnf(grammar)
_parse = make_parse_function(regexs, rules, eof=True)

class Node(object):
    """ The abstract AST node
    """
    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self == other

class Sexpr(Node):
    """ A list of statements
    """
    def __init__(self, stmts):
        self.stmts = stmts

    def compile(self, ctx):
        print('\n===')
        for stmt in self.stmts:
            print('smtm:', stmt)
            stmt.compile(ctx)


class Do(Node):
    """ A list of unrelated statements
    """
    def __init__(self, stmts):
        self.stmts = stmts

    def compile(self, ctx):
        for stmt in self.stmts:
            stmt.compile(ctx)


        #for i in range(len(self.stmts) - 1):


class Lambda(Node):
    """ An annonymous function
    handled like a variable
    """
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def compile(self, ctx):
        #for arg in self.args:
        #    ctx.emit(bytecode.LOAD_VAR, ctx.register_var(self.arg))
        #ctx.emit(bytecode.JUMP_IF_FALSE, 2)
        from nolst.interpreter import W_LambdaObject

        # write RJUMP first
        rjm_addr = ctx.emit(
            bytecode.AJUMP,
            0
            #a_unit.size() + b_unit.size() + 2 #+ len(self.args.stmts) * 2
        )


        a_unit = bytecode.compile_partial(self.args, ctx)
        b_unit = bytecode.compile_partial(self.body, ctx)
        # + 2 is for the last BACK
        # len(self.args.stmts) * 2 is for cleanup bytecode (arguments unbind)

        # compile the lambda object right
        #a_unit = bytecode.compile_partial(self.args, ctx)
        #b_unit = bytecode.compile_partial(self.body, ctx)
        #self.args.compile(ctx)
        #self.body.compile(ctx)

        w = W_LambdaObject(
            rjm_addr + 2 ,
            rjm_addr + 2 + a_unit.size()
        )
        print("pwet:",w.str())
        ctx.hotfix_inst_arg(rjm_addr, ctx.size() + 2)

        # cleanup code
        #for item in self.args.stmts:
        #    item.compile_cleanup(ctx)

        # return from were we came
        ctx.emit(bytecode.BACK)
        # instruction to load function on the stack?
        ctx.emit(bytecode.LOAD_FUNCTION, ctx.register_lambda(w))

    #def __init__(self, varname):
    #    self.varname = varname

    #def compile(self, ctx):
    #    ctx.emit(bytecode.LOAD_VAR, ctx.register_var(self.varname))


class Stmt(Node):
    """ A single statement
    """
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.DISCARD_TOP)

class ConstantInt(Node):
    """ Represent a constant
    """
    def __init__(self, intval):
        self.intval = intval

    def compile(self, ctx):
        # convert the integer to W_IntObject already here
        from nolst.interpreter import W_IntObject
        w = W_IntObject(self.intval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))

class ConstantString(Node):
    """ Represent a constant
    """
    def __init__(self, strval):
        self.strval = strval

    def compile(self, ctx):
        # convert the integer to W_IntObject already here
        from nolst.interpreter import W_StringObject
        w = W_StringObject(self.strval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))

class UnevaluatedSymbol(Node):
    """ Represent anything unevaluated
    """
    def __init__(self, strval):
        self.strval = strval

    def compile(self, ctx):
        # convert the integer to W_IntObject already here
        from nolst.interpreter import W_SymbolObject
        w = W_SymbolObject(self.strval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))


class ConstantFloat(Node):
    """ Represent a constant
    """
    def __init__(self, floatval):
        self.floatval = floatval

    def compile(self, ctx):
        # convert the integer to W_FloatObject already here
        from nolst.interpreter import W_FloatObject
        w = W_FloatObject(self.floatval)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))


class FuncCall(Node):
    """ A function call
    """
    def __init__(self, fname, arguments=[]):
        print(fname)
        #exit(0)
        self.function_name = fname
        self.args = arguments

    def compile(self, ctx):

        for a in self.args:
            a.compile(ctx)
            #ctx.emit(bytecode.LOAD_VAR, a)

        #faddr = ctx.function_addr(self.function_name)
        #if faddr < 1:a
        #    raise Error()

        # load function var
        self.function_name.compile(ctx)
        #ctx.emit(bytecode.LOAD_CONSTANT, self.function_name)
        ctx.emit(bytecode.CALL)




class BinOp(Node):
    """ A binary operation
    """
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def compile(self, ctx):
        self.left.compile(ctx)
        self.right.compile(ctx)
        ctx.emit(bytecode.BINOP[self.op])

class BaseList(Node):
    """ Base class for list related
    """
    def __init__(self, content):
        self.content = content

    def compile(self, ctx):
        from nolst.interpreter import W_ListObject

        obj = W_ListObject(self.content)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(obj))

class QuotedExpr(BaseList):

    """ Represent a quoted expr - kinda like a special string
    """
    def __init__(self, content):
        self.content = content



    def compile(self, ctx):
        # convert the integer to W_IntObject already here
        from nolst.interpreter import W_QuotedListObject
        obj = W_QuotedListObject(self.content)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(obj))

    def compile(self, ctx):
        from nolst.interpreter import W_QuotedListObject, W_SymbolObject
        obj = W_QuotedListObject(self.content)
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(obj))
        for item in self.content:
            #item.compile(ctx)
            pass
            # w = W_SymbolObject(item.strval)
            # ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))


class InlineList(BaseList):
    pass


class Variable(Node):
    """ Variable reference
    """
    def __init__(self, varname):
        self.varname = varname

    def compile(self, ctx):
        ctx.emit(bytecode.LOAD_VAR, ctx.register_var(self.varname))

class Assignment(Node):
    """ Assign to a variable
    """
    def __init__(self, varname, expr):
        self.varname = varname
        self.expr = expr

    def compile_cleanup(self, ctx):
        ctx.emit(bytecode.DELETE_VAR, ctx.var_pos(self.varname))

    def compile(self, ctx):
        if self.expr is not None:
            self.expr.compile(ctx)
        ctx.emit(bytecode.ASSIGN, ctx.register_var(self.varname))


class While(Node):
    """ Simple loop
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def compile(self, ctx):
        pos = len(ctx.data)
        self.cond.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.body.compile(ctx)
        ctx.emit(bytecode.JUMP_BACKWARD, pos)
        ctx.data[jmp_pos] = chr(len(ctx.data))

class If(Node):
    """ A very simple if
    """
    def __init__(self, cond, body):
        self.cond = cond
        self.body = body

    def compile(self, ctx):
        self.cond.compile(ctx)
        ctx.emit(bytecode.JUMP_IF_FALSE, 0)
        jmp_pos = len(ctx.data) - 1
        self.body.compile(ctx)
        ctx.data[jmp_pos] = chr(len(ctx.data))

class Print(Node):
    def __init__(self, expr):
        self.expr = expr

    def compile(self, ctx):
        self.expr.compile(ctx)
        ctx.emit(bytecode.PRINT, 0)

class Transformer(object):
    def visit_main(self, node):
        return self.dispatch(node)


    def visit_atom(self, node):
        if node.children[0].symbol == 'DECIMAL':
            return ConstantInt(int(node.children[0].token.source))
        elif node.children[0].symbol == 'SYMBOL':
            return Variable(node.children[0].token.source)
        elif node.children[0].symbol == 'STRING':
            #assert len(node.children[0].token.source) > 2
            return ConstantString(node.children[0].token.source.rstrip('"'))
        raise NotImplementedError()


    def dispatch(self, node):
        if node.symbol == 'atom':
            return self.visit_atom(node)
        elif node.symbol == 'sexpr':
            return self.visit_sexpr(node)
        elif node.symbol == 'qsexpr':
            return self.visit_qsexpr(node)
        elif node.symbol == 'root':
            return self.visit_root(node)

        # terminals
        elif node.symbol == 'DECIMAL':
            return ConstantInt(int(node.token.source))

        elif node.symbol == 'SYMBOL':
            return Variable(node.token.source)

        print node.symbol
        raise NotImplementedError()

    def visit_root(self, node):
        '''
        only used in the root scope
        '''
        return Sexpr([self.dispatch(i) for i in node.children])


    def visit_qsexpr(self, node):
        '''
        quoted lisp statement. would store bytecode as string
        '''

        #content = self.dispatch(node.children[0])
        l = []
        for n in node.children:
            item = n
            if item.symbol == 'sexpr':
                r = self.visit_qsexpr(item)
                l.append(r)
            elif item.symbol == 'atom':
                sub = []

                t = item.children[0].token.name
                l.append(UnevaluatedSymbol(item.children[0].token.name))
            else:
                # we evaluate item since it may be resolved
                #return item
                l.append(UnevaluatedSymbol(item.token.name))
                #raise NotImplementedError(item)


        return QuotedExpr(l)


    def visit_sexpr(self, node):

        expr = []
        # node.children contains nor atoms
        # nor other sexpr.
        c = node.children[0]
        if c.symbol == 'atom':
            if c.children[0].token.source == 'def':
                # var definition
                # TODO
                expr.append(
                    Assignment(
                        node.children[1].children[0].token.source,
                        self.dispatch(node.children[2])
                    )
                )
            elif c.children[0].token.source == 'do':
                c = [self.dispatch(i) for i in node.children[1:]]
                expr.append(
                    Do(c)
                )
            elif c.children[0].token.source == 'lambda':
                #c = [self.dispatch(i) for i in node.children[1:]]
                expr.append(
                    Lambda(
                        self.visit_func_args(node.children[1]),
                        self.visit_func_body(node.children[2])
                    )
                )
            elif c.children[0].token.source == 'add':
                # addition
                expr.append(
                    BinOp(
                        '+',
                        self.dispatch(node.children[1]),
                        self.dispatch(node.children[2])
                    )
                )
            elif c.children[0].token.source == 'print':
                expr.append(Print(self.dispatch(node.children[1])))
            else:
                # this is a function call
                # funcname: c.children[0].token.source
                # arguments: c.children[0].token.source
                #
                print('funccal: ' + str(node.children[1:]))
                expr.append(
                    FuncCall(
                        Variable(c.children[0].token.source), #.token.source,
                        [self.dispatch(i.children[0]) for i in (node.children[1:] if len(node.children) + 1 > 0 else [])]
                    )
                )

            #print(c.children[0].token.source)
            #expr.append(c.children[0].token)

        return Sexpr(expr)


    def visit_func_args(self, node):
        '''
        handle a function definition argument's ast
        eg:
        (lambda (x y) (add x y))
        -> the AST resulting to `(x y)` (agument declaration)
        will be passed to this function.

        We'll generate `ASSIGN` bytecode here - values
        are waiting on the stack.
        `ASSIGN` stores TOS into vars[var_num].
        '''
        return Do([Assignment(x.children[0].token.source, None) for x in node.children])

    def visit_func_body(self, node):
        '''

        '''
        return self.visit_sexpr(node)
        #cc = [self.dispatch(i) for i in node.children]
        #print(cc)
        return Do(cc)



transformer = Transformer()

def parse(source):
    """ Parse the source code and produce an AST
    """
    parsed = _parse(source)
    #print(parsed)
    #parsed.view()
    transformed = ToAST().transform(parsed)
    transformed.view()

    t = transformer.visit_main(transformed)
    return t

def main():

    import sys
    parse(sys.stdin.read())

if __name__ == '__main__':
    main()
