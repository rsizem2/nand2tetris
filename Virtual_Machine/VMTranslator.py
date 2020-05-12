"""
VM Translator following the API outlined in the book. 

Takes one or no arguments. If no arguments, the script translate all .vm files 
found in the current directory. If the argument is a .vm file then that file is 
translated, if a directory is given then all files in that directory are translated.
"""

import sys, os

class VMTranslator():
    # All .vm files written to filename.asm
    # one parser for each .vm file
    # one code writer for everything
    
    def __init__(self, filename):
        if os.path.isdir(filename):
            #print('Directory Given')
            self._files = [filename + '/' + x for x in os.listdir(filename) if x.endswith(".vm")]
            #print('Files to be translated:', self._files)
            self._isdir = True
            self._name = filename + '/' + filename.split('/')[-1] + '.asm'
        elif os.path.isfile(filename) and filename.endswith('.vm'):
            #print('File given:', filename)
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
            #print('writing initilization code')
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
        
        
class CodeWriter():
    
    def __init__(self, filename):
        self._name = filename
        self._file = open(filename, 'w')
        #print('Output file:', filename)
        self._current_function = None
        self._command = {'not': ['@SP\n','A=M-1\n','M=!M\n'],
           'or': ['@SP\n','AM=M-1\n','D=M\n','A=A-1\n','M=D|M\n'],
           'and': ['@SP\n','AM=M-1\n','D=M\n','A=A-1\n','M=D&M\n'],
           'add': ['@SP\n','AM=M-1\n','D=M\n','A=A-1\n','M=D+M\n'],
           'sub': ['@SP\n','AM=M-1\n','D=M\n','A=A-1\n','M=M-D\n'],
           'neg': ['@SP\n','A=M-1\n','M=-M\n'],
           'eq': ['D;JEQ\n'],
           'gt': ['D;JGT\n'],
           'lt': ['D;JLT\n'],
           'PUSH_D': ['@SP\n','A=M\n','M=D\n','@SP\n','M=M+1\n'],
           'POP_D': ['@SP\n','AM=M-1\n','D=M\n'],
           'local': ['@LCL\n','D=M\n'],
           'argument': ['@ARG\n','D=M\n'],
           'this': ['@THIS\n','D=M\n'],
           'that': ['@THAT\n','D=M\n'],
           'pointer': ['@3\n','D=A\n'],
           'temp': ['@5\n','D=A\n']}
        self._counter = 0
        
    def filename(self, name):
        self._name = name
        pass
    
    def write_arithmetic(self, command):
        self._file.writelines(['// ' + command + '\n'])
        if command in ['eq', 'gt', 'lt']:
            # pop off the stack
            self._file.writelines(self._command['POP_D'])
            # subtract D from value on top of stack
            self._file.writelines(['A=A-1\n','D=M-D\n'])
            # label for jump
            self._file.writelines(['@TRUE'+str(self._counter)+'\n'])
            # jump condition
            self._file.writelines(self._command[command])
            # label if jump condition falses
            self._file.writelines(['@FALSE'+str(self._counter)+'\n','D=0;JEQ\n'])
            # set D to true
            self._file.writelines(['(TRUE'+str(self._counter)+')\n','D=-1\n'])
            # set D to false
            self._file.writelines(['(FALSE'+str(self._counter)+')\n'])
            # write D to top of stack, change SP
            self._file.writelines(['@SP\n','A=M-1\n','M=D\n'])
            self._counter += 1
        else:
            self._file.writelines(self._command[command])
    
    def write_pushpop(self, command, segment, index):
        if command == 'C_PUSH':
            self._file.writelines(['//' + ' push ' + segment + ' ' + index + '\n'])
            if segment == 'constant':
                self._file.writelines(['@'+index+'\n','D=A\n'])
                self._file.writelines(self._command['PUSH_D'])
            elif segment in ['local','argument','this','that']:
				#Set D to base
                self._file.writelines(self._command[segment])
				#Store contents of base + index in D
                self._file.writelines(['@'+index+'\n','A=D+A\n','D=M\n'])
                self._file.writelines(self._command['PUSH_D'])
            elif segment in ['pointer', 'temp']:
                #Set D to base
                self._file.writelines(self._command[segment])
                #Store contents of base + index in D
                self._file.writelines(['@'+index+'\n','A=D+A\n','D=M\n'])
                self._file.writelines(self._command['PUSH_D'])
            else: # static
                self._file.writelines(['@' + self._name + '.'+ index +'\n','D=M\n'])
                self._file.writelines(self._command['PUSH_D'])
        elif command == 'C_POP':
            self._file.writelines(['//' + ' pop ' + segment + ' ' + index + '\n'])
            if segment in ['local','argument','this','that','pointer','temp']:
                #Set D to base
                self._file.writelines(self._command[segment])
				#Set D = base + index
                self._file.writelines(['@'+index+'\n','D=D+A\n'])
				#Use RAM[13] as storage for base+index
                self._file.writelines(['@R13\n','M=D\n'])
				#Pop actual top of stack
                self._file.writelines(self._command['POP_D'])
				#Retrieve base+index from the "stack"
                self._file.writelines(['@R13\n','A=M\n','M=D\n'])
            elif segment == 'static':
                self._file.writelines(self._command['POP_D'])
                self._file.writelines(['@' + self._name + '.'+ index +'\n','M=D\n'])
    
    def write_label(self, label):
        if self._current_function is None:
            self._file.writelines(['('+label+')\n'])
        else:
            self._file.writelines(['('+self._current_function + '$' + label + ')\n'])
        pass

    def write_goto(self, label):
        self._file.writelines(['//' + ' goto ' + label + '\n'])
        if self._current_function is None:
            self._file.writelines(['@'+label+'\n'])
        else:
            self._file.writelines(['@' + self._current_function + '$' + label + '\n'])
        self._file.writelines(['0;JMP\n'])
        pass

    def write_if(self, label):
        self._file.writelines(['//' + ' if-goto ' + label + '\n'])
        self._file.writelines(self._command['POP_D'])
        if self._current_function is None:
            self._file.writelines(['@'+label+'\n'])
            self._file.writelines(['D;JNE\n'])
        else:
            self._file.writelines(['@' + self._current_function + '$' + label+'\n'])
            self._file.writelines(['D;JNE\n'])
        pass
    
    def write_call(self, name, nargs):
        #Generate unique return address based off of line number
        self._file.writelines(['@CALL'+str(self._counter)+'\n','D=A\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@LCL\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@ARG\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@THIS\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@THAT\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
		#Set ARG to SP-n-5 where n is hte number of args
        self._file.writelines(['@'+nargs+'\n','D=A\n','@5\n','D=D+A\n'])
        self._file.writelines(['@SP\n','D=M-D\n','@ARG\n','M=D\n'])
        self._file.writelines(['@SP\n','D=M\n','@LCL\n','M=D\n'])
        self._file.writelines(['@'+name+'\n','0;JMP\n'])
        self._file.writelines(['(CALL'+str(self._counter)+')\n'])
        self._counter += 1
    
    def write_return(self):
        #Use R14 to store FRAME as defined on p.163
        self._file.writelines(['@LCL\n','D=M\n','@R14\n','M=D\n','@5\n'])
        #Use R15 to store the RET, note that D is still set to FRAME.
        self._file.writelines(['A=D-A\n','D=M\n','@R15\n','M=D\n'])
        #Pop return value, store at ARG
        self._file.writelines(self._command['POP_D'])
        self._file.writelines(['@ARG\n','A=M\n','M=D\n'])
        #Set SP to ARG+1
        self._file.writelines(['@ARG\n','D=M+1\n','@SP\n','M=D\n'])
        #Retrieve and decrement FRAME variable
        self._file.writelines(['@R14\n','AM=M-1\n','D=M\n','@THAT\n','M=D\n'])
        self._file.writelines(['@R14\n','AM=M-1\n','D=M\n','@THIS\n','M=D\n'])
        self._file.writelines(['@R14\n','AM=M-1\n','D=M\n','@ARG\n','M=D\n'])
        self._file.writelines(['@R14\n','A=M-1\n','D=M\n','@LCL\n','M=D\n'])
        self._file.writelines(['@R15\n','A=M\n','0;JEQ\n'])      

    def write_function(self, name, nlocals):
        self._file.writelines(['//' + ' function ' + name + ' ' + nlocals + '\n'])
        self._file.writelines(['('+ name + ')\n'])
        self._current_function = name
        for _ in range(int(nlocals)):
            self.write_pushpop('C_PUSH', 'constant', '0')
    
    def write_init(self):
        self._file.writelines(['@256\n','D=A\n','@SP\n','M=D\n'])
        self.write_call('Sys.init', '0')
    
    def close(self):
        self._file.writelines(['(END)\n', '@END\n', '0;JMP'])
        self._file.close()
    
    
if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    VMTranslator(filename)