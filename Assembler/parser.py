'''
Defines the Parser component of the Hack Assembler. 

Given a preprocessed input file of asm commands, parses each command into the comp, dest, and jump components.
'''

class Parser():
    
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
    
