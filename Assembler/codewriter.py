'''
This module defines the CodeWriter component of the Hack Assembler. 

Takes the parsed dest, comp, and jump commands from the assembly language and converts them the corresponding binary code.
'''

class Code():
    
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