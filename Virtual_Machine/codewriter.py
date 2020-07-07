'''
Module implementing the CodeWriter component of the VM Translator.

Generates .asm code based on the parsed VM commands, outputs to a file given as input.
'''

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

    def write_arithmetic(self, command):
        self._file.writelines(['// ' + command + '\n'])
        if command in ['eq', 'gt', 'lt']:
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
            else: 
                # static
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
        # Generate unique return address based off of counter
        self._file.writelines(['@CALL'+str(self._counter)+'\n','D=A\n'])
        # push saved lcl, arg, this, that to function frame on stack
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@LCL\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@ARG\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@THIS\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
        self._file.writelines(['@THAT\n','D=M\n'])
        self._file.writelines(self._command['PUSH_D'])
		# Set ARG to SP-n-5 where n is the number of args
        self._file.writelines(['@'+nargs+'\n','D=A\n','@5\n','D=D+A\n'])
        self._file.writelines(['@SP\n','D=M-D\n','@ARG\n','M=D\n'])
        self._file.writelines(['@SP\n','D=M\n','@LCL\n','M=D\n'])
        self._file.writelines(['@'+name+'\n','0;JMP\n'])
        self._file.writelines(['(CALL'+str(self._counter)+')\n'])
        self._counter += 1

    def write_return(self):
        # Use R14 to store FRAME as defined on p.163
        self._file.writelines(['@LCL\n','D=M\n','@R14\n','M=D\n','@5\n'])
        # Use R15 to store the RET, note that D is still set to FRAME.
        self._file.writelines(['A=D-A\n','D=M\n','@R15\n','M=D\n'])
        # Pop return value, store at ARG
        self._file.writelines(self._command['POP_D'])
        self._file.writelines(['@ARG\n','A=M\n','M=D\n'])
        # Set SP to ARG+1
        self._file.writelines(['@ARG\n','D=M+1\n','@SP\n','M=D\n'])
        # Retrieve and decrement FRAME variable
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
