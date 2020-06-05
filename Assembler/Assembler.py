"""
Python module which implements the Hack Assembler outlined in chapter 6 of 'The Elements of Computing Systems' using the OOP API.

Place this script in the same folder as the HACK asm files you want to translate into binary. Alternatively, create an 'asm' folder containing these files in the directory.  
"""
import os

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
    
class Parser():
    '''
    Parses a .asm command into it's relevant components.
    '''
    
    def __init__(self, cleanasm):
        self._asm = iter(cleanasm)
        self._current = None
        self._finished = False
        self._dest = None
        self._comp = None
        self._jump = None
        self._symbol = None
        self._type = None
     
    def has_more_commands(self):
        return not self._finished
        
    def advance(self):
        if not self._finished:
            self._current = next(self._asm, None)
        if self._current is None:
            # file completed
            self._finished = True
            self._dest = None
            self._comp = None
            self._jump = None
            self._symbol = None
            self._type = None
        elif '@' in self._current:
            # A type command
            self._dest = None
            self._comp = None
            self._jump = None
            self._symbol = self._current[1:].strip()
            self._type = 'A'
        else:
            # C type command
            temp = self._current.split(';')
            if len(temp) > 1: 
                # with jump
                temp, self._jump = tuple(temp)
            else:
                # without jump
                temp = temp[0]
                self._jump = None
            temp = temp.split('=')
            if len(temp) > 1:
                # with dest
                self._dest, self._comp = tuple(temp)
            else:
                # without dest
                self._comp = temp[0]
                self._dest = None
            self._symbol = None
            self._type = 'C'
            
    def command_type(self):
        return self._type

    def symbol(self):
        return self._symbol

    def dest(self):
        return self._dest
    
    def comp(self):
        return self._comp
    
    def jump(self):
        return self._jump
                    
class SymbolTable():
    '''
    Manages a dictionary of symbols and values to be used by the Assembler
    '''
    
    def __init__(self):
        self._varaddr = 16
        self._table = {'SP':0, 'LCL':1, 'ARG':2, 'THIS':3, 'THAT':4, 
                      'SCREEN':16384, 'KEYBOARD':24576, 
                      'R0':0, 'R1':1, 'R2':2, 'R3':3, 
                      'R4':4, 'R5':5, 'R6':6, 'R7':7, 
                      'R8':8, 'R9':9, 'R10':10, 'R11':11, 
                      'R12':12, 'R13':13, 'R14':14, 'R15':15}
        
    def contains(self, symbol):
        return symbol in self._table
    
    def add_entry(self, symbol, addr = None):
        if self.contains(symbol):
            # if already exists, do nothing
            pass
        elif addr is None:
            # if no addr, given assume it's a variable
            self._table[symbol] = self._varaddr
            self._varaddr += 1
        else:
            # if addr is given, this represents a label, addr is the linenumber 
            self._table[symbol] = addr
            
    def get_address(self, symbol):
        return self._table.get(symbol)
   
class Code():
    '''
    Converts parsed machine language code into binary.
    '''
    
    def __init__(self):
        self._dest = {None:'000', 'M':'001', 
                     'D':'010', 'MD':'011', 
                     'A':'100', 'AM':'101', 
                     'AD':'110', 'AMD':'111'}
        self._jump = {None:'000', 'JGT':'001', 
                     'JEQ':'010', 'JGE':'011', 
                     'JLT':'100', 'JNE':'101', 
                     'JLE':'110','JMP':'111'}
        self._comp = {'0':'101010', '1':'111111', '-1':'111010', 
                     'D':'001100', 'A':'110000', '!D':'001101', 
                     '!A':'110001', '-D':'001111', '-A':'110011', 
                     'D+1':'011111', 'A+1':'110111', 'D-1':'001110', 
                     'A-1':'110010', 'D+A':'000010','D-A':'010011', 
                     'A-D':'000111', 'D&A':'000000', 'D|A':'010101'}
        temp = dict()
        for key, value in self._comp.items():
            temp[key] = '0' + value
            if 'A' in key:
                temp[key.replace('A','M')] = '1' + value
        self._comp.update(temp)
            
    def dest(self, string):
        return self._dest[string]
    
    def comp(self, string):
        return self._comp[string]
    
    def jump(self, string):
        return self._jump[string]
    
       
if __name__ == '__main__':
    asmfiles = list()
    if os.path.isdir('asm'):
        asmfiles = ['asm/' + x for x in os.listdir('asm/') if x.endswith(".asm")]
    asmfiles.extend([x for x in os.listdir() if x.endswith(".asm")])
    
    for inputfile in asmfiles:
        Assembler(inputfile)