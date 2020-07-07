"""
The main Python module implementing the Hack Assembler as outlined in chapter 6 of 'The Elements of Computing Systems' using the OOP API.

Run using 'python Assembler.py <filename>' where <filename> is an .asm file or a folder containing .asm files  
"""

import os, sys
from parser import Parser
from symboltable import SymbolTable
from codewriter import Code

class Assembler():
    '''
    Takes a single .asm file as input and outputs a .hack file with the same name.
    The assembling takes three passes.
        - Preprocess: Remove whitespace and comments
        - First Pass: Generate symbol table and remove symbolic labels
        - Second Pass: Translates the .asm file into a .hack file, line by line.
    '''
    
    def __init__(self, filename):
        self._input = self.preprocess(filename)
        self._name = filename.split('/')[-1]
        self._name = self._name.split('.')[0]
        self._table = SymbolTable()
        self.first_pass()
        self._parser = Parser(self._input)
        self._output = []
        self._code = Code()
        self.second_pass()
        self.write_output()

    def preprocess(self, filename):
        with open(filename, 'r') as temp:
            assembly = temp.readlines()
        temp = []
        for line in assembly:
            # remove comments and white space
            line = line.split('//')[0].strip().replace(' ','')   
            if line:
                # if nonempty, then it should contain valid asm                                    
                temp += [line]
        return temp
    
    def first_pass(self):
        rom_addr = 0
        temp = []
        for line in self._input:
            if '(' in line:
                symbol = line[1:-1]
                self._table.add_entry(symbol, rom_addr)
            else:
                temp += [line]
                rom_addr += 1
        self._input = temp
    
    def second_pass(self):
        while self._parser.has_more_commands():
            self._parser.advance()
            if self._parser.command_type() == 'A':
                # A type command
                value = self._parser.symbol()
                if set(value) <= set('0123456789'):
                    # symbol is a number
                    value = int(value)
                elif self._table.contains(value):
                    # symbol is a label
                    value = self._table.get_address(value)
                else:
                    # symbol is a variable
                    self._table.add_entry(value)
                    value = self._table.get_address(value)
                self._output += ['0' + "{0:015b}".format(value) + '\n']
            elif self._parser.command_type() == 'C':
                # C type command
                self._output += ['111'
                                 + self._code.comp(self._parser.comp())
                                 + self._code.dest(self._parser.dest())
                                 + self._code.jump(self._parser.jump()) + '\n']
    
    def write_output(self):
        with open('hack/' + self._name + '.hack', 'w') as temp:
            temp.writelines(self._output)
        print(self._name + '.asm', 'translated to', 'hack/' + self._name + '.hack')
    
       
if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    if os.path.isdir(filename):
        # is a directory
        asmfiles = [filename + x for x in os.listdir(filename) if x.endswith(".asm")]
        for inputfile in asmfiles:
            Assembler(inputfile)
    elif filename and filename.endswith('.asm'):
        # is a single .asm file
        Assembler(filename)
    
    
        