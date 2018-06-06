bytecodes = {
    'LOAD_CONSTANT': 0x00,
    'LOAD_VAR':     0x01,
    'ASSIGN':        0x02,
    'DISCARD_TOP':   0x03,
    'JUMP_IF_FALSE': 0x04,
    'JUMP_BACKWARD': 0x05,
    'BINARY_ADD':    0x06,
    'BINARY_SUB':    0x07,
    'BINARY_EQ':     0x08,
    'RETURN':        0x09,
    'PRINT':         0x10,
    'BINARY_LT':     0x11,
    'DELETE_VAR':    0x12,
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

    def register_constant(self, v):
        self.constants.append(v)
        return len(self.constants) - 1

    def register_var(self, name):
        try:
            return self.names_to_numbers[name]
        except KeyError:
            self.names_to_numbers[name] = len(self.names)
            self.names.append(name)
            return len(self.names) - 1

    def emit(self, bc, arg=0):
        self.data.append(chr(bc))
        self.data.append(chr(arg))

    def create_bytecode(self, offset=0):
        if offset != 0:
            for idx, v in enumerate(self.data):
                if idx % 2:
                    self.data[idx] += offset

        return ByteCode("".join(self.data), self.constants[:], len(self.names))

class ByteCode(object):
    '''
    '''
    _immutable_fields_ = ['code', 'constants[*]', 'numvars']

    def __init__(self, code, constants, numvars):
        self.code = code
        self.constants = constants
        self.numvars = numvars

    def dump(self):
        lines = []
        i = 0
        for i in range(0, len(self.code), 2):
            c = self.code[i]
            c2 = self.code[i + 1]
            lines.append(bytecodes_by_value[ord(c)] + " " + str(ord(c2)))
        return '\n'.join(lines)

def compile_ast(astnode, offset=0):
    c = CompilerContext()
    astnode.compile(c)
    c.emit(bytecodes['RETURN'], 0)
    return c.create_bytecode(offset=offset)
