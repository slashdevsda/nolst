
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
        for stmt in self.stmts:
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
    """
    def __init__(self, args, body):
        self.args = args
        self.body = body

    def compile(self, ctx):
        #for arg in self.args:
        #    ctx.emit(bytecode.LOAD_VAR, ctx.register_var(self.arg))
        #ctx.emit(bytecode.JUMP_IF_FALSE, 2)
        from nolst.interpreter import W_LambdaObject

        w = W_LambdaObject(
            bytecode.compile_ast(self.args),
            bytecode.compile_ast(self.body)
        )
        ctx.emit(bytecode.LOAD_CONSTANT, ctx.register_constant(w))
        #self.args.compile(ctx)
        #self.body.compile(ctx)
        # ctx.emit(bytecode.RETURN, 0)


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

    def compile(self, ctx):
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

        raise NotImplementedError()


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
                # if t == 'SYMBOL':
                #     l.append(Variable(item.children[0].token.source))
                # elif t == 'DECIMAL':
                #     l.append(ConstantInt(int(item.children[0].token.source)))
                # elif t == 'STRING':
                #     l.append(ConstantString(item.children[0].token.source))

                # for i in n.children:
                #     print('~~+~~',self.visit_qsexpr(n))
                #     sub.append(self.visit_qsexpr(n))
                #l.append(QuotedExpr())
            else:
                raise NotImplementedError(item)


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
                print('VAR DEF')
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
                    Lambda(self.dispatch(node.children[1]), self.dispatch(node.children[2]))
                )
            elif c.children[0].token.source == 'add':
                # addition
                expr.append(
                    BinOp(
                        '+',
                        self.dispatch(node.children[1]),
                        self.dispatch(node.children[2]))
                )
            elif c.children[0].token.source == 'print':
                expr.append(Print(self.dispatch(node.children[1])))
            else:
                cc = [self.dispatch(i) for i in node.children]
                expr.append(
                    Do(cc)
                )

            #print(c.children[0].token.source)
            #expr.append(c.children[0].token)

        return Sexpr(expr)


transformer = Transformer()

def parse(source):
    """ Parse the source code and produce an AST
    """
    parsed = _parse(source)
    #print(parsed)
    #parsed.view()
    transformed = ToAST().transform(parsed)
    #transformed.view()

    t = transformer.visit_main(transformed)
    return t

def main():

    import sys
    parse(sys.stdin.read())

if __name__ == '__main__':
    main()
