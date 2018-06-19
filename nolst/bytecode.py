bytecodes = {
    'LOAD_CONSTANT': 0x00,
    'LOAD_VAR':      0x01,
    'ASSIGN':        0x02,
    'DISCARD_TOP':   0x03,
    'JUMP_IF_FALSE': 0x04,
    'JUMP_BACKWARD': 0x05,

    # relative jump
    'RJUMP':         0x13,
    # absolute jump
    # with any kind of
    # restrictions
    'AJUMP':         0x17,

    # back (RETURN from function call)
    'BACK':         0x15,

    # load a lambda object on the
    # top of the stack
    'LOAD_FUNCTION':         0x16,


    'BINARY_ADD':    0x06,
    'BINARY_SUB':    0x07,
    'BINARY_EQ':     0x08,
    'RETURN':        0x09,
    'PRINT':         0x10,
    'BINARY_LT':     0x11,
    'DELETE_VAR':    0x12,
    'CALL':          0x14,
}

bytecodes_by_value = {v:k for k, v in bytecodes.iteritems()}

for bytecode, value in bytecodes.iteritems():
    print(bytecode, value)
    globals()[bytecode] = value

BINOP = {'+': BINARY_ADD, '-': BINARY_SUB, '==': BINARY_EQ, '<': BINARY_LT}


class CompilerContext(object):
    def __init__(self):
        self.data = []
        self.constants = []
        self.names = []
        self.names_to_numbers = {}

        self.lambdas = []

    def register_lambda(self, item):
        self.lambdas.append(item)
        return len(self.lambdas) - 1

    def register_constant(self, v):
        self.constants.append(v)
        return len(self.constants) - 1

    def hotfix_inst_arg(self, offset, arg):
        self.data[offset + 1] = chr(arg)


    def merge(self, cc):
        '''
        merge with another context object.
        '''
        #print(cc)
        assert isinstance(cc, CompilerContext)
        a = len(self.data)
        self.data += cc.data

        return a

    def function_addr(self, fname):
        try:
            return self.names_to_numbers[fname]
        except KeyError:
            return -1

    def register_var(self, name):
        print('REGISTER VAR : ', name)
        try:
            return self.names_to_numbers[name]
        except KeyError:
            print('[*] VAR CREATED: %d' %len(self.names))
            self.names_to_numbers[name] = len(self.names)
            self.names.append(name)
            return len(self.names) - 1

    def var_pos(self, name):
        #try:
        return self.names_to_numbers[name]
        #except KeyError:
        #    return -1


    def emit(self, bc, arg=0):
        a = len(self.data)
        self.data.append(chr(bc))
        self.data.append(chr(arg))
        return a

    def size(self):
        return len(self.data)


    def create_bytecode(self, offset=0):
        if offset != 0:
            for idx, v in enumerate(self.data):
                if idx % 2:
                    self.data[idx] += offset

        return ByteCode("".join(self.data), self.constants[:], len(self.names), self.lambdas)


class ByteCode(object):
    '''
    '''
    _immutable_fields_ = ['code', 'constants[*]', 'numvars']

    def __init__(self, code, constants, numvars, lambda_list):
        self.code = code
        self.constants = constants
        self.numvars = numvars
        self.lambdas = lambda_list


    def merge(self, cc):
        '''
        merge with another bytecode object.
        return offset(pc) where bytecode were inserted,
        if you want to keep some kind of address reference.
        '''
        a = len(self.code)
        self.code += cc.code
        #self.numvars += cc.numvars
        return a


    def dump(self):
        '''
        (debug)
        '''
        lines = []
        i = 0
        for i in range(0, len(self.code), 2):
            c = self.code[i]
            c2 = self.code[i + 1]
            l = str(i) + "\t| " + bytecodes_by_value[ord(c)] + " " + str(ord(c2))
            lines.append(l)
        return '\n'.join(lines)


def compile_partial(astnode, cctx=None):
    if not cctx:
        cctx = CompilerContext()
    astnode.compile(cctx)
    return cctx

def compile_ast(astnode, offset=0):
    c = CompilerContext()
    astnode.compile(c)
    c.emit(bytecodes['RETURN'], 0)
    return c.create_bytecode(offset=offset)
