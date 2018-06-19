from nolst.sourceparser import parse
from nolst.bytecode import compile_ast
from nolst import bytecode
from rpython.rlib import jit
import os

def printable_loc(pc, code, bc):
    return str(pc) + " " + bytecode.bytecodes_by_value[ord(code[pc])]

driver = jit.JitDriver(greens = ['pc', 'code', 'bc'],
                       reds = ['frame'],
                       virtualizables=['frame'],
                       get_printable_location=printable_loc)

class W_Root(object):
    pass

DEBUG = os.environ.get('NDBG')

class W_IntObject(W_Root):
    def __init__(self, intval):
        assert(isinstance(intval, int))
        self.intval = intval

    def add(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type: %s" %str(other))
        return W_IntObject(self.intval + other.intval)

    def lt(self, other):
        if not isinstance(other, W_IntObject):
            raise Exception("wrong type")
        return W_IntObject(self.intval < other.intval)

    def is_true(self):
        return self.intval != 0

    def str(self):
        return str(self.intval)


class W_StringObject(W_Root):
    def __init__(self, strval):
        assert(isinstance(strval, str))
        self.strval = strval

    def add(self, other):
        if not isinstance(other, W_StringObject):
            raise Exception("wrong type")
        return W_StringObject(self.strval + other.strval)

    def lt(self, other):
        if not isinstance(other, W_StringObject):
            raise Exception("wrong type")
        return W_IntObject(self.strval < other.strval)

    def is_true(self):
        return True

    def str(self):
        return self.strval


class W_LambdaObject(W_Root):
    '''
    used for lambda.
    '''
    def __init__(self, args, body):
        #assert(isinstance(strval, str))
        self.args = args
        self.body = body

    def add(self, other):
        raise NotImplementedError('Invalid operation')

    def lt(self, other):
        raise NotImplementedError('Invalid operation')

    def is_true(self):
        return True

    def str(self):
        return "Lambda(args:%s body:%s)" %(self.args, self.body)


class W_SymbolObject(W_Root):
    '''
    used for unevaluated stuff
    '''
    def __init__(self, strval):
        assert(isinstance(strval, str))
        self.strval = strval

    def add(self, other):
        raise NotImplementedError('Invalid operation')

    def lt(self, other):
        if not isinstance(other, W_SymbolObject):
            raise Exception("wrong type")
        return W_IntObject(self.strval < other.strval)

    def is_true(self):
        return True

    def str(self):
        return self.strval



class W_FloatObject(W_Root):
    def __init__(self, floatval):
        assert(isinstance(floatval, float))
        self.floatval = floatval

    def add(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_FloatObject(self.floatval + other.floatval)

    def lt(self, other):
        if not isinstance(other, W_FloatObject):
            raise Exception("wrong type")
        return W_IntObject(self.floatval < other.floatval)

    def str(self):
        return str(self.floatval)

class W_ListObject(W_Root):
    def __init__(self, content):
        assert(isinstance(content, list))
        self.content = content

    def add(self, other):
        if not isinstance(other, W_ListObject):
            raise Exception("wrong type")
        return W_ListObject(self.content + other.content)

    def lt(self, other):
        if not isinstance(other, W_ListObject):
            raise Exception("wrong type")
        return W_IntObject(len(self.content) < len(other.content))

    def is_true(self):
        return True

    def str(self):
        return '[%s]' %', '.join([str(i) for i in self.content])


class W_QuotedListObject(W_Root):
    '''
    KInda list, but for quoted code
    '''
    def __init__(self, content):
        assert(isinstance(content, list))
        self.content = content

    def add(self, other):
        if not isinstance(other, W_QuotedListObject):
            raise Exception("wrong type")
        return W_QuotedListObject(self.content + other.content)

    def lt(self, other):
        if not isinstance(other, W_QuotedListObject):
            raise Exception("wrong type")
        return W_IntObject(len(self.content) < len(other.content))

    def is_true(self):
        return True

    def str(self):
        s = '('
        from nolst.sourceparser import UnevaluatedSymbol, QuotedExpr
        for item in self.content:
            if isinstance(item, UnevaluatedSymbol):
                s += item.strval
            elif isinstance(item, QuotedExpr):
                pass
        s += ')'
        return '(%s)' %', '.join([str(i) for i in self.content])


class Locals(object):
    '''
    '''
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, entry_addr, return_addr):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.entry_addr = entry_addr
        self.return_addr = return_addr
        self.valuestack = [None] * 5
        # safe estimate! no more 5 arguments to a local
        # context
        self.vars = [None] * bc.numvars
        self.valuestack_pos = 0
        self.vars = []


    def get_var(self, idx):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v


    def dump(self):
        b = ''
        for i, v in enumerate(self.vars):
            if v:
                b += '%s: %s\n' %(hex(i), v.str())
        return b



class Frame(object):
    _virtualizable_ = ['valuestack[*]', 'valuestack_pos', 'vars[*]']

    def __init__(self, bc):
        self = jit.hint(self, fresh_virtualizable=True, access_directly=True)
        self.valuestack = [None] * 10 # safe estimate!
        self.vars = [None] * bc.numvars
        self.valuestack_pos = 0
        self.lambdas = bc.lambdas

    def load_lambda(self, name):
        return self.lambdas[name]


    def dump_vars(self):
        b = ''
        for i, v in enumerate(self.vars):
            if v:
                b += '%s: %s\n' %(hex(i), v.str())
        return b

    def dump_stack(self):
        b = ''

        for i, _ in enumerate(self.valuestack):
            if self.valuestack[i] or i == self.valuestack_pos:
                b += "%s:\t%s" %(hex(i), self.valuestack[i])
                if i == self.valuestack_pos - 1:
                    b += ' <---'
                b += '\n'

        return  b

    def push(self, v):
        pos = jit.hint(self.valuestack_pos, promote=True)
        assert pos >= 0
        self.valuestack[pos] = v
        self.valuestack_pos = pos + 1

    def pop(self):
        pos = jit.hint(self.valuestack_pos, promote=True)
        new_pos = pos - 1
        assert new_pos >= 0
        v = self.valuestack[new_pos]
        self.valuestack_pos = new_pos
        return v

def add(left, right):
    return left + right



def execute(frame, bc):
    '''
    execute bytecode `bc.code`.
    `frame` represents the stack
    '''

    # rec is used for function call return addr
    rec = []
    code = bc.code
    pc = 0
    while True:
        # required hint indicating this is the top of the opcode dispatch
        driver.jit_merge_point(pc=pc, code=code, bc=bc, frame=frame)
        c = ord(code[pc])
        arg = ord(code[pc + 1])
        pc += 2

        if DEBUG:
            # DEBUG, dump everyting for each opcodes
            print(
                'INSTRUCTION: %s(ARG:%s) @%d\n'
                %(bytecode.bytecodes_by_value[c], hex(arg) if arg else 'NO_ARG', pc)
            )

        if c == bytecode.LOAD_CONSTANT:
            w_constant = bc.constants[arg]
            frame.push(w_constant)
        elif c == bytecode.DISCARD_TOP:
            frame.pop()
        elif c == bytecode.RETURN:
            return
        elif c == bytecode.BINARY_ADD:
            right = frame.pop()
            left = frame.pop()
            w_res = left.add(right)
            frame.push(w_res)

        elif c == bytecode.BINARY_LT:
            right = frame.pop()
            left = frame.pop()
            frame.push(left.lt(right))
        elif c == bytecode.JUMP_IF_FALSE:
            if not frame.pop().is_true():
                pc = arg
        elif c == bytecode.JUMP_BACKWARD:
            pc = arg
            # required hint indicating this is the end of a loop
            driver.can_enter_jit(pc=pc, code=code, bc=bc, frame=frame)
        elif c == bytecode.PRINT:
            item = frame.pop()
            print('(nolst) ' + item.str())
        elif c == bytecode.ASSIGN:
            # assign the top of the stack
            # to the next free variable slot
            frame.vars[arg] = frame.pop()
        elif c == bytecode.DELETE_VAR:
            frame.vars[arg] = frame.pop()
        elif c == bytecode.LOAD_VAR:
            # load variable TOS
            frame.push(frame.vars[arg])

        elif c== bytecode.AJUMP:
            # takes absolute adress as arg.
            # wild.
            pc = arg

        elif c == bytecode.RJUMP:
            # takes relative adress as arg.
            pc += arg

        elif c == bytecode.LOAD_FUNCTION:
            # load function/lambda object on the stack
            l = frame.load_lambda(arg)
            frame.push(l)

        # play with pc
        elif c == bytecode.CALL:
            # save return address then
            # call a function.
            #
            # The function is on the top of
            # the stack, followed by its arguments.
            # The function's bytecode is responsible
            # for popin' out these arguments
            # and bind them to variables.
            #  :stack:
            # [function]
            # [arg0..]
            # [..argN]

            rec.append(pc)
            function = frame.pop()
            pc = function.args

        elif c == bytecode.BACK:
            # BACK is a special instruction
            # that allow an arbitrary jump
            # after a function call.
            #
            # When a CALL is encountered, the bytecode return
            # address is stored into a list, named `rec`.
            #
            # TODO: replace this list by a set
            # to ignore recursions
            #frame.vars[arg] = frame.pop()

            pc = rec.pop()

        else:
            assert False

        if DEBUG:
            print('=== STACK DUMP ===\n%s' %frame.dump_stack())
            print('=== VARS DUMP ===\n%s' %frame.dump_vars())


def interpret(source, frame=None):
    parsed = parse(source)
    bc = compile_ast(parsed)
    print('\n[*] bytecode produced: ')
    print(bc.dump())
    if not frame:
        frame = Frame(bc)
    execute(frame, bc)
    return frame # for tests and later introspection
