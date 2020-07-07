'''
Module implementing the VMWriter component of the JACK compiler.
'''

class VMWriter():

    def __init__(self, filename):
        self._name = filename
        self._file = open(filename, 'w')

    
    def write_object_alloc(self, size):
        # allocate space for object on heap, sets pointer to 'this'
        self.write_push('constant', size)
        self.write_call('Memory.alloc', 1)
        self.write_pop('pointer',0)
        
    def write_array_alloc(self, size):
        # puts base address of array on heap
        self.write_push('constant', size)
        self.write_call('Memory.alloc', 1)

    def write_string_constant(self, string):
        # push length of string
        self.write_push('constant',len(string))
        # call String.new, which returns 'this'
        self.write_call('String.new', 1)
        for char in string:
            # push int value of char
            self.write_push('constant',ord(char))
            # append to string
            self.write_call('String.appendChar', 2)

    def write_keyword_constant(self, keyword):
        if keyword == 'true':
            self.write_push('constant',1)
            self._file.writelines(['neg\n'])
        elif keyword == 'false':
            self.write_push('constant',0)
        elif keyword == 'null':
            self.write_push('constant',0)
        elif keyword == 'this':
            self.write_push('pointer',0)
        else:
            assert False, 'bad keyword given: ' + str(keyword)

    def write_operator(self, op):
        if op == '+':
            self._file.writelines(['add\n'])
        elif op == '-':
            self._file.writelines(['sub\n'])
        elif op == '*':
            self.write_call('Math.multiply', 2)
        elif op == '/':
            self.write_call('Math.divide', 2)
        elif op == '&':
            self._file.writelines(['and\n'])
        elif op == '|':
            self._file.writelines(['or\n'])
        elif op == '<':
            self._file.writelines(['lt\n'])
        elif op == '>':
            self._file.writelines(['gt\n'])
        elif op == '=':
            self._file.writelines(['eq\n'])
        else:
            assert False, 'bad operator given: ' + str(op)

    def write_unary(self, op):
        if op == '-':
            self._file.writelines(['neg\n'])
        elif op == '~':
            self._file.writelines(['not\n'])
        else:
            assert False, 'bad operator given: ' + str(op)

    def write_comment(self, string):
        self._file.writelines(['// '+string+'\n'])

    # the following are the atomic vm commands

    def write_push(self, segment, index):
        
        # push segment index
        self._file.writelines(['push ' + segment + ' ' + str(index) + '\n'])

    def write_pop(self, segment, index):
        # pop segment index
        self._file.writelines(['pop ' + segment + ' ' + str(index) + '\n'])

    def write_arithmetic(self, command):
        # command
        self._file.writelines([command + '\n'])

    def write_label(self, label):
        # label symbol
        self._file.writelines(['label ' + label + '\n'])

    def write_goto(self, label):
        # goto symbol
        self._file.writelines(['goto ' + label + '\n'])

    def write_if(self, label):
        # if-goto symbol
        self._file.writelines(['if-goto ' + label + '\n'])

    def write_call(self, name, num_args):
        # call name nargs
        self._file.writelines(['call ' + name + ' ' + str(num_args) + '\n'])

    def write_function(self, name, num_locals):
        # function name nlocals
        self._file.writelines(['function ' + name + ' ' + str(num_locals) + '\n'])

    def write_return(self):
        self._file.writelines(['return\n'])

    def close(self):
        self._file.close()
