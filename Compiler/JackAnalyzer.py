"""
A Jack source code analyzer based on the implementaton contract from Chapter 10 of 'The Elements of Computing Systems'.

This script defines 3 classes:

    - JackAnalyzer - communicates between the tokenizer and compilation engine
    - JackTokenizer - tokenizes a JACK source file, ignoring commens and
    - CompilationEngine - compiles the tokens into VM code

"""

import sys, os, re
from collections import deque, namedtuple

Symbol = namedtuple('Symbol', ['type','kind','number'])
Subroutine = namedtuple('Subroutine', ['type', 'nargs'])

class JackAnalyzer():
    '''
    Top-level driver that sets up and invokes the other modules.
    '''

    def __init__(self, filename):
        if os.path.isdir(filename):
            # directory input
            self._files = [filename + '/' + x for x in os.listdir(filename) if x.endswith(".jack")]
            self._isdir = True
            self._name = filename + '/' + filename.split('/')[-1] + '.vm'
        elif os.path.isfile(filename) and filename.endswith('.jack'):
            # jack file input
            self._files = [filename]
            self._isdir = False
            self._name = filename.replace('.jack','.vm')
        else:
            # bad input, do nothing
            self._files = list()
            self._isdir = False
            return
        self._output = []
        for file in self._files:
            self._tokenizer = JackTokenizer(file)
            self._code = CompilationEngine(self._tokenizer)


class JackTokenizer():
    '''
    Tokenizes input .jack file using regular expressions
    '''

    def __init__(self, filename):
        self._name = filename
        print(self._name)
        self._input = self.remove_comments(filename)
        # REGEX to check if string begins with symbol
        self._symbol = re.compile('^[\{\}\(\)\[\]\.,;\+\-\*/&\|<>=~]')
        # REGEX to check if string begins with integer
        self._integer = re.compile('^[0-9]+')
        # REGEX to check for keyword
        self._keyword = re.compile('^(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)')
        # REGEX to check for string constant
        self._string = re.compile('^["][^"]+["]')
        # REGEX to check for identifier, also flags keywords
        self._identifier = re.compile('^[a-zA-Z0-9_]+')
        self._xmlsymbol = {'<':'&lt;','>':'&gt;','&':'&amp;'}
        self._tokens = None
        self._backup = None
        self._finished = True
        self.tokenize(self._input)
        self.write_tokens()
        self._token = None
        self._type = None
        self._labels = dict()


    def tokenize(self, string):
        tokens = []
        types = []
        while string:
            match = self._symbol.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('symbol')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._integer.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('integerConstant')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._keyword.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('keyword')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._string.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start+1:end-1]) # drop the enclosing double quotes
                types.append('stringConstant')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._identifier.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('identifier')
                string = re.sub('^[\s]+','', string[end:])
                continue
            print('invalid next token')
            print(string)
            return
        self._backup = list(zip(tokens,types))
        self._tokens = deque(self._backup)
        self._finished = (len(self._tokens) == 0)
        return None


    def remove_comments(self, filename):
        with open(filename, 'r') as temp:
            raw = temp.read()
        # removes comments, using regex
        raw = re.sub('//.*?\n|/\*.*?\*/', '', raw, flags=re.S)
        # replace multiple successive whitespace characters with single space
        raw = re.sub('[\s]+',' ', raw)
        return re.sub('^[\s]+','', raw)


    def has_more_tokens(self):
        return not self._finished


    def get_filename(self):
        return self._name


    def write_tokens(self):
        with open(self._name.replace('.jack','Tokens.xml'),'w') as temp:
            temp.writelines(['<tokens>\n'])
            for tokens, types in self._backup:
                if tokens in ['<','>','&']:
                    temp.writelines(['<'+types+'> '+self._xmlsymbol[tokens]+' </'+types+'>\n'])
                else:
                    temp.writelines(['<'+types+'> '+tokens+' </'+types+'>\n'])
            temp.writelines(['</tokens>\n'])


    def advance(self):
        try:
            temp = self._tokens.popleft()
        except:
            temp = None
        if self._finished:
            self._token = None
            self._type = None
        elif temp is None:
            self._finished = True
            self._token = None
            self._type = None
        else:
            self._token, self._type = temp


    def peek(self):
        try:
            temp, _ = self._tokens[0]
        except:
            temp = None
        return temp


    def xml_token(self):
        if self._token in ['<','>','&']:
            return '<' + self._type + '> ' + self._xmlsymbol[self._token] + ' </' + self._type + '>\n'
        else:
            return '<' + self._type + '> ' + self._token + ' </' + self._type + '>\n'


    def is_valid_type(self):
        return self._type == 'identifier' or self._token in ['int','char','boolean']


    def is_valid_operator(self):
        return self._type == 'symbol' and self._token in ['+','-','*','/','&','|','<','>','=']


    def is_valid_unary(self):
        return self._type == 'symbol' and self._token in ['-','~']


    def is_valid_subroutine(self):
        return self._type == 'keyword' and self._token in ['constructor','function','method']


    def is_valid_subroutine_type(self):
        return self._type == 'identifier' or self._token in ['int','char','boolean','void']


    def is_valid_statement(self):
        return self._type == 'keyword' or self._token in ['let','if','while','do','return']


    def is_valid_class_variable(self):
        return self._type == 'keyword' and self._token in ['static','field']


    def is_valid_variable(self):
        return self._token == 'var'


    def is_valid_keyword_constant(self):
        return self._type == 'keyword' and self._token in ['true','false', 'null','this']


    def get_token(self):
        return str(self._token)

    def keyword(self):
        if self._type != 'keyword':
            return None
        else:
            return str(self._token)


    def symbol(self):
        if self._type != 'symbol':
            return None
        else:
            return str(self._token)


    def identifier(self):
        if self._type != 'identifier':
            return None
        else:
            return str(self._token)


    def int_value(self):
        if self._type != 'integerConstant' or int(self._token) > 32767:
            return None
        else:
            return str(self._token)


    def string_value(self):
        if self._type != 'stringConstant':
            return None
        else:
            return str(self._token)


class CompilationEngine():
    '''
    Parses a stream of jack tokens recursively.
    '''

    def __init__(self, tokenizer):
        self._name = tokenizer.get_filename().replace('.jack','')
        # tokenizer for input
        self._tokenizer = tokenizer
        # symbol table
        self._symbols = SymbolTable()
        # vm output fiole
        self._writer = VMWriter(self._name + '.vm')
        # Input should be a tokenized .jack file containing one class
        assert self._tokenizer.has_more_tokens()
        self._tokenizer.advance()
        self.compile_class()
        self.close()


    def change_name(self, name):
        self._name = name

    def get_name(self, name):
        return self._name

    def get_token(self):
        return self._tokenizer._token

    def get_type(self):
        return self._tokenizer._type

    def close(self):
        # close the output file at the end
        self._vmfile.close()

    def compile_class(self):
        # assumes first token is keyword 'class'
        assert self._tokenizer.keyword() == 'class'
        self._tokenizer.advance()
        # assumes next token is an identifier, the class name
        assert self._tokenizer.identifier()
        self._tokenizer.advance()
        # assumes next token is opening bracket
        assert self._tokenizer.symbol() == '{', "expected '{' but got " + self.get_token()
        self._tokenizer.advance()
        # recursively checks for static/field variables, runs corresponding methods
        while self._tokenizer.is_valid_class_variable():
            self.compile_class_var()
        while self._tokenizer.is_valid_subroutine():
            self.compile_subroutine()
        # after processing class variables/methods, assumes closing bracket
        assert self._tokenizer.symbol() == '}', "expected '}' but got " + self.get_token()
        self._tokenizer.advance()
        # assuming .jack file is properly formatted, there should be no more tokens
        assert not self._tokenizer.has_more_tokens()


    def compile_class_var(self):
        # this method should not be called if the following assertion isn't true
        assert self._tokenizer.is_valid_class_variable()
        # next token indicates the kind of class variable: static/field
        temp_kind = self._tokenizer.get_token()
        self._tokenizer.advance()
        # next token should be int/char/boolean or class name
        assert self._tokenizer.is_valid_type()
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # next token should be an identifier
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, temp_kind)
        self._tokenizer.advance()
        # recursively check for another variable of the same type, separated by ','
        while self._tokenizer.symbol() == ',':
            self._tokenizer.advance()
            # next token should be an identifier for a variable name
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, temp_kind)
            self._tokenizer.advance()
        # next token should be a ';'
        assert self._tokenizer.symbol() == ';', "expected ';' but got " + self.get_token()
        self._tokenizer.advance()


    def compile_subroutine(self):
        # first token should be a kind of subroutine: constructor, method, function
        assert self._tokenizer.is_valid_subroutine()
        self._tokenizer.advance()
        # next token should be return type of subroutine
        assert self._tokenizer.is_valid_subroutine_type()
        self._tokenizer.advance()
        # next token is identifier for the subroutine name
        assert self._tokenizer.identifier()
        self._tokenizer.advance()
        # next token should be opening parenthesis
        assert self._tokenizer.symbol() == '('
        self._tokenizer.advance()
        # add parameter list, if next token indicated a parameter type
        if self._tokenizer.is_valid_type():
            self.compile_parameter_list()
        # next token should be closing parenthesis
        assert self._tokenizer.symbol() == ')'
        self._tokenizer.advance()
        # next token should be opening bracket
        assert self._tokenizer.symbol() == '{'
        # compile the subroutine body
        self.compile_subroutine_body()
        # last token should be closing parenthesis, indicating end of subroutine body
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()


    def compile_subroutine_body(self):
        # should only be called within subroutine declation, current token is '{'
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        # next token should be a keyword
        assert self._tokenizer.keyword()
        # check for zero or more variable declarations
        while self._tokenizer.keyword() == 'var':
            self.compile_var()
        # next token doesn't indicate a variable declarion, must be a statement
        self.compile_statements()
        # next token must be closing bracket, ending the subroutine body
        assert self._tokenizer.symbol() == '}'


    def compile_parameter_list(self):
        # should only be called if next symbol is a type
        assert self._tokenizer.is_valid_type()
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # next token is identifier, the variable name
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, 'argument')
        self._tokenizer.advance()
        while self._tokenizer.symbol() == ',':
            self._tokenizer.advance()
            assert self._tokenizer.is_valid_type()
            temp_type = self._tokenizer.get_token()
            self._tokenizer.advance()
            # next token is identifier, the variable name
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, 'argument')
            self._tokenizer.advance()
        # parameter list ends when closing parenthesis encountered
        assert self._tokenizer.symbol() == ')'

    def compile_var(self):
        assert self._tokenizer.is_valid_variable()
        self._tokenizer.advance()
        # next token should be a type or class name
        assert self._tokenizer.is_valid_type()
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # next token should be an identifier
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, 'local')
        self._tokenizer.advance()
        # recursively check for other variable of the same time, separated by ','
        while self._tokenizer.symbol() == ',':
            self._tokenizer.advance()
            # next token should be an identifier for a variable name
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, 'local')
            self._tokenizer.advance()
        # next token should be a ';'
        assert self._tokenizer.symbol() == ';'
        self._tokenizer.advance()


    def compile_statements(self):
        while self._tokenizer.is_valid_statement():
            if self._tokenizer.keyword() == 'let':
                self.compile_let()
            elif self._tokenizer.keyword() == 'if':
                self.compile_if()
            elif self._tokenizer.keyword() == 'while':
                self.compile_while()
            elif self._tokenizer.keyword() == 'do':
                self.compile_do()
            elif self._tokenizer.keyword() == 'return':
                self.compile_return()
        # block of statements ends with a closing bracket
        assert self._tokenizer.symbol() == '}'


    def compile_do(self):
        assert self._tokenizer.keyword() == 'do'
        self._tokenizer.advance()
        # next token should be a subroutine name
        assert self._tokenizer.identifier()
        if self._tokenizer.identifier() and self._tokenizer.peek() == '(':
            # subroutine_name ( expression_list )
            temp_name = self._tokenizer.get_token()
            self._tokenizer.advance()
            # next token is '('
            self._tokenizer.advance()
            self.compile_expression_list()
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '.':
            # class . subroutine ( expression_list )
            temp_name = self._tokenizer.get_token()
            # look up name in symbol table, get type (should be a class)
            temp_class = self._symbols.get_type(temp_name)
            if temp_class is None:
                # function or constructor
                temp_class = temp_name
                temp_nargs = 0
            else:
                # method
                temp_nargs = 1
            self._tokenizer.advance()
            # next token is '.'
            self._tokenizer.advance()
            assert self._tokenizer.identifier()
            # next token is subroutine name
            temp_name += ('.' + self._tokenizer.get_token())
            self._tokenizer.advance()
            assert  self._tokenizer.symbol() == '('
            self._tokenizer.advance()
            temp_nargs += self.compile_expression_list()
            self._writer.write_call(temp_name, temp_nargs)
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        # next token should be a ';'
        assert self._tokenizer.symbol() == ';'
        self._tokenizer.advance()


    def compile_let(self):
        assert self._tokenizer.keyword() == 'let'
        self._tokenizer.advance()
        # next token should be a variable name
        assert self._tokenizer.identifier()
        self._tokenizer.advance()
        # check if array
        if self._tokenizer.symbol() == '[':
            self._tokenizer.advance()
            self.compile_expression()
            # expression ends with closing square bracket
            assert self._tokenizer.symbol() == ']', "expected ']' but got " + self.get_token()
            self._tokenizer.advance()
        assert self._tokenizer.symbol() == '='
        self._tokenizer.advance()
        # next set of tokens should represent an expression
        self.compile_expression()
        # expression ends with a ';'
        assert self._tokenizer.symbol() == ';', "expected ';' but got " + self.get_token()
        self._tokenizer.advance()


    def compile_while(self):
        assert self._tokenizer.keyword() == 'while'
        self._tokenizer.advance()
        # expects ( expression )
        assert self._tokenizer.symbol() == '('
        self._tokenizer.advance()
        self.compile_expression()
        assert self._tokenizer.symbol() == ')'
        self._tokenizer.advance()
        # expects { statements }
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        self.compile_statements()
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()


    def compile_return(self):
        assert self._tokenizer.keyword() == 'return'
        self._tokenizer.advance()
        # check for optional expression
        if self._tokenizer.symbol() == ';':
            # no expression
            self._writer.write_push('constant', 0)
            self._tokenizer.advance()
        else:
            # has expression
            self.compile_expression()
            assert self._tokenizer.symbol() == ';'
            self._tokenizer.advance()
        self._writer.write_return()


    def compile_if(self):
        assert self._tokenizer.keyword() == 'if'
        self._tokenizer.advance()
        # expects ( expression )
        assert self._tokenizer.symbol() == '(', "expected '(' but got " + self.get_token()
        self._tokenizer.advance()
        self.compile_expression()
        assert self._tokenizer.symbol() == ')', "expected '(' but got " + self.get_token()
        self._tokenizer.advance()
        # expects { statements }
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        self.compile_statements()
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()
        # check for optional else block
        if self._tokenizer.keyword() == 'else':
            self._tokenizer.advance()
            # expects { statements }
            assert self._tokenizer.symbol() == '{', "expected '{' but got " + self.get_token()
            self._tokenizer.advance()
            self.compile_statements()
            assert self._tokenizer.symbol() == '}', "expected '}' but got " + self.get_token()
            self._tokenizer.advance()


    def compile_expression(self):
        # term (op term)*
        self.compile_term()
        # 'recursive' check for optional (op term)*
        while self._tokenizer.is_valid_operator():
            # op token
            temp_op = self._tokenizer.symbol()
            self._tokenizer.advance()
            # process term
            self.compile_term()
            # write operator vm command, postfix order
            self._writer.write_operator(temp_op)


    def compile_term(self):
        if self._tokenizer.int_value() is not None:
            # integer constant
            self._writer.write_pop('constant', self._tokenizer.int_value())
            self._tokenizer.advance()
        elif self._tokenizer.string_value() is not None:
            # string constant
            self._writer.write_string_constant(self._tokenizer.string_value())
            self._tokenizer.advance()
        elif self._tokenizer.keyword() is not None:
            # keyword constant
            self._writer.write_keyword_constant(self._tokenizer.keyword())
            self._tokenizer.advance()
        elif self._tokenizer.symbol() == '(':
            # ( expression )
            self._tokenizer.advance()
            self.compile_expression()
            assert self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.is_valid_unary():
            # unary operator
            temp_op = self._tokenizer.symbol()
            self._tokenizer.advance()
            self.compile_term()
            # write operator vm command, postfix order
            self._writer.write_operator(temp_op)
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '[':
            # array [ expression ]
            # process array name, push associated value onto stack
            self._writer.write_push(self._symbols.kind_of(self._tokenizer.identifier()),
                                    self._symbols.index_of(self._tokenizer.identifier()))
            self._tokenizer.advance()
            # process [ symbol
            self._tokenizer.advance()
            # expects expression, value is pushed onto the stack
            self.compile_expression()
            # setup pointer to array element
            self._writer.write_operator('+')
            self._writer.write_pop('pointer', 1)
            # expects closing square bracket
            assert self._tokenizer.symbol() == ']'
            self._tokenizer.advance()
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '(':
            # subroutine_name ( expression_list )
            self._tokenizer.advance()
            self._tokenizer.advance()
            self.compile_expression_list()
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '.':
            # class . subroutine ( expression_list )
            self._tokenizer.advance()
            self._tokenizer.advance()
            assert self._tokenizer.identifier()
            self._tokenizer.advance()
            assert  self._tokenizer.symbol() == '('
            self._tokenizer.advance()
            self.compile_expression_list()
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.identifier():
            # variable_name
            self._writer.write_push(self._symbols.kind_of(self._tokenizer.identifier()),
                                    self._symbols.index_of(self._tokenizer.identifier()))
            self._tokenizer.advance()
        else:
            assert False, "unknown token: " + self.get_token() + " with type " + self.get_type()


    def compile_expression_list(self):
        # (expression ( ',' expression)* )?
        temp_nargs = 0
        while self._tokenizer.symbol() != ')':
            self.compile_expression()
            temp_nargs += 1
            if self._tokenizer.symbol() == ',':
                # there is another expression in the list
                self._tokenizer.advance()
        return temp_nargs


class SymbolTable():

    def __init__(self):
        self._class = dict()
        self._subroutine = dict()
        self._static = 0
        self._field = 0
        self._arg = 0
        self._var = 0


    def start_subroutine(self):
        # clears the old subroutine dictionary, if it exists
        self._subroutine = dict()
        self._arg = 0
        self._var = 0


    def define(self, var_name, var_type, kind):
        if kind == 'static':
            self._class[var_name] = Symbol(var_type, kind, self._static)
            self._static += 1
        elif kind == 'field':
            self._class[var_name] = Symbol(var_type, kind, self._field)
            self._field += 1
        elif kind == 'arg':
            self._subroutine[var_name] = Symbol(var_type, kind, self._arg)
            self._arg += 1
        elif kind == 'var':
            self._subroutine[var_name] = Symbol(var_type, kind, self._var)
            self._var += 1
        else:
            assert False, "invalid var_type given."


    def var_count(self, kind):
        if kind == 'static':
            return self._static
        elif kind == 'field':
            return self._field
        elif kind == 'arg':
            return self._arg
        elif kind == 'var':
            return self._var
        else:
            assert False, "invalid var_type given."


    def kind_of(self, var_name):
        # check subroutine scope, then class scope, if neither returns None
        try:
            return self._subroutine[var_name].kind
        except KeyError:
            try:
                return self._class[var_name].kind
            except KeyError:
                return None


    def type_of(self, var_name):
        # check subroutine scope, then class scope, if neither returns None
        try:
            return self._subroutine[var_name].type
        except KeyError:
            try:
                return self._class[var_name].type
            except KeyError:
                return None


    def index_of(self, var_name):
        # check subroutine scope, then class scope, if neither returns None
        try:
            return self._subroutine[var_name].number
        except KeyError:
            try:
                return self._class[var_name].number
            except KeyError:
                return None


class VMWriter():
    '''
    Simple interface for writing VM code to a file
    '''

    def __init__(self, filename):
        self._name = filename
        self._file = open(filename, 'w')

    # helper functions

    def write_string_constant(self, string):
        # push length of string
        self.write_push('constant',len(string))
        # call String.new, which returns 'this'
        self.write_call('String.new', 2)
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
        if op == '*':
            self._file.writelines(['mult\n'])
        elif op == '/':
            self.write_call('Math.divide', 2)
        if op == '&':
            self._file.writelines(['and\n'])
        elif op == '|':
            self._file.writelines(['or\n'])
        if op == '<':
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


if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    JackAnalyzer(filename)
