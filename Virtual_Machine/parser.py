'''
Module implementing the Parser component of the VM Translator.

This module parses a single .vm file one command (line) at a time into its components, which can then be more easily translated into machine code.
'''

class Parser():


    def __init__(self, filename):
        self._vm = iter(self.preprocess(filename))
        self._current = None
        self._finished = False
        self._command = {'add':'C_ARITHMETIC','sub':'C_ARITHMETIC','neg':'C_ARITHMETIC',
                         'eq': 'C_BOOLEAN', 'gt': 'C_BOOLEAN', 'lt':  'C_BOOLEAN',
                         'and': 'C_ARITHMETIC', 'or': 'C_ARITHMETIC', 'not': 'C_ARITHMETIC',
                         'push': 'C_PUSH', 'pop': 'C_POP', 'return': 'C_RETURN',
                         'function': 'C_FUNCTION', 'label': 'C_LABEL', 'if-goto': 'C_IF',
                         'goto': 'C_GOTO', 'call': 'C_CALL'}
        self._call = None
        self._type = None
        self._arg1 = None
        self._arg2 = None

    def preprocess(self, filename):
        with open(filename, 'r') as temp:
            assembly = temp.readlines()
        temp = []
        for line in assembly:
            # remove comments and white space
            line = line.split('//')[0].strip()
            if line:
                # if nonempty, then it should contain valid asm
                temp += [line]
        return temp

    def has_more_commands(self):
        return not self._finished

    def advance(self):
        if not self._finished:
            self._current = next(self._vm, None)
        if self._current is None:
            # file completed
            self._finished = True
            self._type = None
            self._arg1 = None
            self._arg2 = None
        else:
            temp = self._current.strip().split(' ')
            self._call = temp[0]
            self._type = self._command[self._call]
            try:
                self._arg1 = temp[1]
            except IndexError:
                self._arg1 = None
            try:
                self._arg2 = temp[2]
            except IndexError:
                self._arg2 = None

    def command_type(self):
        return self._type

    def command(self):
        return self._call

    def arg1(self):
        return self._arg1

    def arg2(self):
        return self._arg2

