'''
Defines the SymbolTable component of the Hack Assembler.

Manages a dictionary of symbols and values to be used by the Assembler.
'''

class SymbolTable():
    
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