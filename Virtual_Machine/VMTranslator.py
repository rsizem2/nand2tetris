"""
Translates .vm code files into HACK assembly .asm files. Follows the API outlined in the book.

To use this script run:
	- VMTranslator.py <directory>
	- VMTranslator.py <vm file>
"""

import sys, os
from parser import Parser 
from codewriter import CodeWriter 


class VMTranslator():
    '''
    Manages the translation effort, bridging the gap between the Parser and Codewriter objects. 
    A new Parser is created for each file in the directory.
    '''

    def __init__(self, filename):
        if os.path.isdir(filename):
            self._files = [filename + '/' + x for x in os.listdir(filename) if x.endswith(".vm")]
            self._isdir = True
            self._name = filename + '/' + filename.split('/')[-1] + '.asm'
        elif os.path.isfile(filename) and filename.endswith('.vm'):
            self._files = [filename]
            self._isdir = False
            self._name = filename.replace('.vm','.asm')
        else:
            self._files = list()
            self._isdir = False
            return
        self._output = []
        self._code = CodeWriter(self._name)
        if self._isdir:
            self._code.write_init()
        for file in self._files:
            self._parser = Parser(file)
            self._code.filename(file.replace('.vm','').split('/')[-1])
            self.translate()
        self._code.close()

    def translate(self):
        # using input from parser, translate and output
        while self._parser.has_more_commands():
            self._parser.advance()
            if self._parser.command_type() in ['C_ARITHMETIC','C_BOOLEAN']:
                self._code.write_arithmetic(self._parser.command())
            elif self._parser.command_type() in ['C_POP','C_PUSH']:
                self._code.write_pushpop(self._parser.command_type(),
                                          self._parser.arg1(),
                                          self._parser.arg2())
            elif self._parser.command_type() == 'C_LABEL':
                self._code.write_label(self._parser.arg1())
            elif self._parser.command_type() == 'C_GOTO':
                self._code.write_goto(self._parser.arg1())
            elif self._parser.command_type() == 'C_IF':
                self._code.write_if(self._parser.arg1())
            elif self._parser.command_type() == 'C_FUNCTION':
                self._code.write_function(self._parser.arg1(), self._parser.arg2())
            elif self._parser.command_type() == 'C_CALL':
                self._code.write_call(self._parser.arg1(), self._parser.arg2())
            elif self._parser.command_type() == 'C_RETURN':
                self._code.write_return()



if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    VMTranslator(filename)
