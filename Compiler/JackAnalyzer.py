"""
A Jack source code analyzer based on the implementaton contract from Chapter 10 of 'The Elements of Computing Systems'.

This script defines 5 classes:

    - JackAnalyzer - communicates between the tokenizer and compilation engine
    - JackTokenizer - tokenizes a JACK source file, ignoring comments and whitespace
    - CompilationEngine - compiles the tokens into VM code
    - VMWriter - 
    - SymbolTable

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
        self._input = self.remove_comments(filename)
        # REGEX to check if string begins with symbol
        self._symbol = re.compile('^[\{\}\(\)\[\]\.,;\+\-\*/&\|<>=~]')
        # REGEX to check if string begins with integer
        self._integer = re.compile('^[0-9]+')
        # REGEX to check for keyword
        self._keyword = re.compile('^(class|constructor|function|method|field|static|var|int|char|boolean|void|true|false|null|this|let|do|if|else|while|return)(?=[\W]+)')
        # REGEX to check for string constant
        self._string = re.compile('^["][^"]+["]')
        # REGEX to check for identifier, also flags keywords
        self._identifier = re.compile('^[a-zA-Z0-9_]+')
        self._xmlsymbol = {'<':'&lt;','>':'&gt;','&':'&amp;'}
        self._tokens = None
        self._backup = None
        self._finished = True
        self.tokenize(self._input)
        #self.write_tokens()
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
                # next token is integer
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('integerConstant')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._keyword.match(string)
            if match:
                # next token is keyword
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('keyword')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._string.match(string)
            if match:
                # next token is string
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

    def debug(self):
        # only called in the case of an AssertionError
        print(self._tokens)

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
        self._class = None
        self._subroutine = None
        self._counter = 0
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
        self._writer.close()

    def compile_class(self):
        # 'class' className '{' classVarDec* subroutineDec* '}'
        # keyword - class
        assert self._tokenizer.keyword() == 'class'
        self._tokenizer.advance()
        # identifier - className
        assert self._tokenizer.identifier()
        self._class = self._tokenizer.identifier()
        self._tokenizer.advance()
        # sybmol - '{'
        assert self._tokenizer.symbol() == '{', "expected '{' but got " + self.get_token()
        self._tokenizer.advance()
        # classVarDec*
        while self._tokenizer.is_valid_class_variable():
            self.compile_class_var()
        # subroutineBody*
        while self._tokenizer.is_valid_subroutine():
            self.compile_subroutine()
        # sybmol - '}'
        assert self._tokenizer.symbol() == '}', "expected '}' but got " + self.get_token()
        self._tokenizer.advance()
        # assuming .jack file is properly formatted, there should be no more tokens
        assert not self._tokenizer.has_more_tokens()


    def compile_class_var(self):
        # ('static'|'field') type varName (',' varName)* ';'
        assert self._tokenizer.is_valid_class_variable()
        # keyword - 'static' or 'field'
        temp_kind = self._tokenizer.get_token()
        self._tokenizer.advance()
        # type - 'int' or 'char' or 'boolean' or className
        assert self._tokenizer.is_valid_type()
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # identifier - varName
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, temp_kind)
        self._tokenizer.advance()
        # recursively check for (',' varName)*  structure
        while self._tokenizer.symbol() == ',':
            self._tokenizer.advance()
            # identifier - varName
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, temp_kind)
            # symbol - ',' or ';'
            self._tokenizer.advance()
        # next token should be a ';'
        assert self._tokenizer.symbol() == ';', "expected ';' but got " + self.get_token()
        self._tokenizer.advance()


    def compile_subroutine(self):
        # ('constructor'|'method'|'function') ('void'| type) subroutineName '(' parameterList ')' subroutineBody
        assert self._tokenizer.is_valid_subroutine()
        self._symbols.start_subroutine()
        # keyword - constructor or method or function
        self._subroutine = self._tokenizer.get_token()
        if self._subroutine == 'method':
            # in the case of method, add 'this' to symbol table
            self._symbols.define('this', self._class, 'argument')
        self._tokenizer.advance()
        # keyword - type or void
        assert self._tokenizer.is_valid_subroutine_type()
        self._tokenizer.advance()
        # identifier - subroutineName
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.identifier()
        self._tokenizer.advance()
        # symbol - '('
        assert self._tokenizer.symbol() == '('
        self._tokenizer.advance()
        # parameterList
        if self._tokenizer.is_valid_type():
            self.compile_parameter_list()
        # symbol - '('
        assert self._tokenizer.symbol() == ')'
        self._tokenizer.advance()
        temp_name = self._class + '.' + temp_name
        # symbol - '{'
        assert self._tokenizer.symbol() == '{'
        # subroutineBody
        self.compile_subroutine_body(temp_name)
        self._writer.write_comment('end subroutine ' + temp_name)


    def compile_parameter_list(self):
        # ( (type varName) (',' type varName)* )?
        # only called if non-empty parameter list
        assert self._tokenizer.is_valid_type()
        # type - int or char or boolean or className
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # identifier - varName
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, 'argument')
        self._tokenizer.advance()
        while self._tokenizer.symbol() == ',':
            # symbol - ','
            self._tokenizer.advance()
            assert self._tokenizer.is_valid_type()
            # type - int or char or boolean or className
            temp_type = self._tokenizer.get_token()
            self._tokenizer.advance()
            # identifier - varName
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, 'argument')
            self._tokenizer.advance()
        # symbol - ')'
        assert self._tokenizer.symbol() == ')'


    def compile_subroutine_body(self, name):
        # '{' varDec* statements '}'
        # symbol - '{'
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        # varDec
        num_locals = 0
        while self._tokenizer.keyword() == 'var':
            # remember that compiling variables writes NO vm code
            num_locals += self.compile_var()
        self._writer.write_function(name, num_locals)
        if self._subroutine == 'method':
            # set this, in the case of a method
            self._writer.write_push('argument',0)
            self._writer.write_pop('pointer',0)
        elif self._subroutine == 'constructor':
            # allocate object
            self._writer.write_object_alloc(self._symbols.var_count('field'))
        # statements
        self.compile_statements()
        # symbol - '{'
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()


    def compile_var(self):
        # 'var' type varName (',' varName)* ';'
        assert self._tokenizer.is_valid_variable()
        # keyword - 'var'
        self._tokenizer.advance()
        # type - int or char or boolean or className
        assert self._tokenizer.is_valid_type()
        temp_type = self._tokenizer.get_token()
        self._tokenizer.advance()
        # identifier - varName
        assert self._tokenizer.identifier()
        temp_name = self._tokenizer.get_token()
        self._symbols.define(temp_name, temp_type, 'local')
        num_locals = 1
        self._tokenizer.advance()
        while self._tokenizer.symbol() == ',':
            # symbol - ','
            self._tokenizer.advance()
            # identifier - varName
            assert self._tokenizer.identifier()
            temp_name = self._tokenizer.get_token()
            self._symbols.define(temp_name, temp_type, 'local')
            num_locals += 1
            self._tokenizer.advance()
        # symbol - ';'
        assert self._tokenizer.symbol() == ';'
        self._tokenizer.advance()
        return num_locals


    def compile_statements(self):
        # statement*
        while self._tokenizer.is_valid_statement():
            if self._tokenizer.keyword() == 'let':
                # letStatement
                self.compile_let()
            elif self._tokenizer.keyword() == 'if':
                # ifStatement
                self.compile_if()
            elif self._tokenizer.keyword() == 'while':
                # whileStatement
                self.compile_while()
            elif self._tokenizer.keyword() == 'do':
                # doStatement
                self.compile_do()
            elif self._tokenizer.keyword() == 'return':
                # returnStatement
                self.compile_return()
        # symbol - '}'
        assert self._tokenizer.symbol() == '}'

    def compile_let(self):
        # 'let' varName ('[' expression ']')? '=' expression ';'
        # keyword - 'let'
        assert self._tokenizer.keyword() == 'let'
        self._tokenizer.advance()
        # identifier - varName
        assert self._tokenizer.identifier()
        if self._tokenizer.peek() == '=':
            # varName '=' expression ';'
            var_kind = self._symbols.kind_of(self._tokenizer.identifier())
            var_index = self._symbols.index_of(self._tokenizer.identifier())
            self._tokenizer.advance()
            # next token is '='
            self._tokenizer.advance()
            # evaluate RHS expression, pop into variable
            self.compile_expression()
            if var_kind == 'field':
                self._writer.write_pop('this', var_index)
            else:
                self._writer.write_pop(var_kind, var_index)
            # expression ends with a ';'
            assert self._tokenizer.symbol() == ';', "expected ';' but got " + self.get_token()
            self._tokenizer.advance()
        elif self._tokenizer.peek() == '[':
            # varName '[' expression ']' '=' expression ';'
            # write base address to stack
            self._writer.write_push(self._symbols.kind_of(self._tokenizer.identifier()),
                                    self._symbols.index_of(self._tokenizer.identifier()))
            self._tokenizer.advance()
            # symbol - '['
            self._tokenizer.advance()
            # expression - represents array index
            self.compile_expression()
            # base address + array index
            self._writer.write_arithmetic('add')
            # symbol - '['
            assert self._tokenizer.symbol() == ']'
            self._tokenizer.advance()
            # symbol - '='
            assert self._tokenizer.symbol() == '='
            self._tokenizer.advance()
            # expression
            self.compile_expression()
            # pop RHS value into temp segment
            self._writer.write_pop('temp', 1)
            # align that with array[i]
            self._writer.write_pop('pointer', 1)
            # push value of RHS expression onto stack
            self._writer.write_push('temp', 1)
            # pop value into correct array index
            self._writer.write_pop('that', 0)
            # symbol - ';'
            assert self._tokenizer.symbol() == ';', "expected ';' but got " + self.get_token()
            self._tokenizer.advance()


    def compile_if(self):
        # 'if' '(' expression ')' ('else' '{' statements '}')?
        # keyword - if
        assert self._tokenizer.keyword() == 'if'
        self._writer.write_comment('if statement')
        self._tokenizer.advance()
        # symbol - (
        assert self._tokenizer.symbol() == '(', "expected '(' but got " + self.get_token()
        self._tokenizer.advance()
        # expression
        self.compile_expression()
        self._writer.write_arithmetic('not')
        label_num = str(self._counter)
        self._counter += 1
        self._writer.write_if('ELSE'+label_num)
        # symbol - )
        assert self._tokenizer.symbol() == ')', "expected '(' but got " + self.get_token()
        self._tokenizer.advance()
        # symbol - '{'
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        # statements
        self.compile_statements()
        # symbol - '}'
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()
        self._writer.write_goto('IF'+label_num)
        self._writer.write_label('ELSE'+label_num)
        # check for else
        if self._tokenizer.keyword() == 'else':
            # 'else' '{' statements '}'
            # keyword - 'else'
            self._tokenizer.advance()
            # symbol - '{'
            assert self._tokenizer.symbol() == '{', "expected '{' but got " + self.get_token()
            self._tokenizer.advance()
            # statements
            self.compile_statements()
            # symbol - '}'
            assert self._tokenizer.symbol() == '}', "expected '}' but got " + self.get_token()
            self._tokenizer.advance()
        self._writer.write_label('IF'+label_num)


    def compile_while(self):
        # 'while' '(' expression ')' '{' statements '}'
        # keyword - 'while'
        assert self._tokenizer.keyword() == 'while'
        # labels for ifgoto and goto vm commands
        label_num = str(self._counter)
        self._counter += 1
        self._tokenizer.advance()
        # symbol - '('
        assert self._tokenizer.symbol() == '('
        self._tokenizer.advance()
        self._writer.write_label('WHILE'+label_num)
        # expression
        self.compile_expression()
        self._writer.write_arithmetic('not')
        self._writer.write_if('ELSE'+label_num)
        # symbol - ')'
        assert self._tokenizer.symbol() == ')'
        self._tokenizer.advance()
        # symbol - '{'
        assert self._tokenizer.symbol() == '{'
        self._tokenizer.advance()
        # statements
        self.compile_statements()
        self._writer.write_goto('WHILE'+label_num)
        self._writer.write_label('ELSE'+label_num)
        # symbol - '}'
        assert self._tokenizer.symbol() == '}'
        self._tokenizer.advance()

    def compile_do(self):
        # 'do' subroutineCall ';'
        assert self._tokenizer.keyword() == 'do'
        # keyword - 'do'
        self._tokenizer.advance()
        # identifier - subroutineCall
        assert self._tokenizer.identifier()
        # outer subroutine must be void function
        self.compile_subroutine_call()
        # symbol - ';'
        assert self._tokenizer.symbol() == ';'
        # discard void function default return value
        self._writer.write_pop('temp',0)
        self._tokenizer.advance()



    def compile_return(self):
        # 'return' expression? ';'
        # keyword - 'return'
        assert self._tokenizer.keyword() == 'return'
        self._writer.write_comment('return statement')
        self._tokenizer.advance()
        # expression?
        if self._tokenizer.symbol() == ';':
            # symbol - ';' (void function)
            self._writer.write_push('constant', 0)
            self._tokenizer.advance()
        else:
            # expression (not void)
            self.compile_expression()
            # symbol - ';'
            assert self._tokenizer.symbol() == ';'
            self._tokenizer.advance()
        self._writer.write_return()


    def compile_expression(self):
        # term (op term)*
        # term
        self.compile_term()
        # check for op
        while self._tokenizer.is_valid_operator():
            # op
            temp_op = self._tokenizer.symbol()
            self._tokenizer.advance()
            # term
            self.compile_term()
            # write operator vm command, postfix order
            self._writer.write_operator(temp_op)


    def compile_term(self):
        # integerConstant | stringConstant | keywordConstant | varName |
        # varName '[' expression']' | subroutineCall | '(' expression ')' | unaryOp term
        if self._tokenizer.int_value() is not None:
            # integerConstant
            self._writer.write_push('constant', self._tokenizer.int_value())
            self._tokenizer.advance()
        elif self._tokenizer.string_value() is not None:
            # stringConstant
            self._writer.write_string_constant(self._tokenizer.string_value())
            self._tokenizer.advance()
        elif self._tokenizer.keyword() is not None:
            # keywordConstant
            self._writer.write_keyword_constant(self._tokenizer.keyword())
            self._tokenizer.advance()
        elif self._tokenizer.symbol() == '(':
            # '(' expression ')'
            self._tokenizer.advance()
            self.compile_expression()
            assert self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.is_valid_unary():
            # unaryOp term
            temp_op = self._tokenizer.symbol()
            self._tokenizer.advance()
            # term
            self.compile_term()
            # write operator vm command, postfix order
            self._writer.write_unary(temp_op)
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '[':
            # varName '[' expression']'
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
            # push array value onto stack
            self._writer.write_push('that', 0)
            # expects closing square bracket
            assert self._tokenizer.symbol() == ']'
            self._tokenizer.advance()
        elif self._tokenizer.identifier() and self._tokenizer.peek() in ['(','.']:
            # subroutineCall
            self.compile_subroutine_call()
        elif self._symbols.exists(self._tokenizer.identifier()):
            # varName
            var_name = self._tokenizer.identifier()
            var_kind = self._symbols.kind_of(var_name)
            var_index = self._symbols.index_of(var_name)
            if var_kind == 'field':
                # push field var onto stack
                self._writer.write_push('this', var_index)
            else:
                self._writer.write_push(var_kind, var_index)
            self._tokenizer.advance()
        else:
            assert False, "unknown token: " + self.get_token() + " with type " + self.get_type()

    def compile_subroutine_call(self):
        # subroutineName '(' expressionList ')'| (className | varName) '.' subroutineName '(' expressionList ')'
        assert self._tokenizer.identifier() and self._tokenizer.peek() in ['(','.']
        if self._tokenizer.identifier() and self._tokenizer.peek() == '(':
            # subroutineName '(' expressionList ')'
            # method (in current class)
            temp_name = self._class + '.' + self._tokenizer.identifier()
            self._tokenizer.advance()
            # symbol - '('
            self._tokenizer.advance()
            # push this onto the stack
            self._writer.write_push('pointer',0)
            temp_nargs = 1
            # expressionList
            temp_nargs += self.compile_expression_list()
            self._writer.write_call(temp_name, temp_nargs)
            # symbol - ')'
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._symbols.exists(self._tokenizer.identifier()) and self._tokenizer.peek() == '.':
            # varName '.' subroutineName '(' expressionList ')'
            # varName (object)
            temp_name = self._tokenizer.identifier()
            # push object address onto stack, this is an implicit argument
            if self._symbols.kind_of(temp_name) == 'field':
                self._writer.write_push('this',
                                        self._symbols.index_of(temp_name))
            else: 
                self._writer.write_push(self._symbols.kind_of(temp_name),
                                        self._symbols.index_of(temp_name))
            # change name to class name
            temp_name = self._symbols.type_of(temp_name)
            temp_nargs = 1
            self._tokenizer.advance()
            # symbol - '.'
            temp_name += self._tokenizer.get_token()
            self._tokenizer.advance()
            # subroutineName
            assert self._tokenizer.identifier()
            temp_name += self._tokenizer.identifier()
            self._tokenizer.advance()
            # symbol - '('
            assert self._tokenizer.symbol() == '('
            self._tokenizer.advance()
            # expressionList
            temp_nargs += self.compile_expression_list()
            self._writer.write_call(temp_name, temp_nargs)
            # symbol - '('
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()
        elif self._tokenizer.identifier() and self._tokenizer.peek() == '.':
            # className . subroutineName '(' expressionList ')'
            # className
            temp_name = self._tokenizer.identifier()
            self._tokenizer.advance()
            # symbol - '.'
            temp_name += self._tokenizer.get_token()
            self._tokenizer.advance()
            # subroutineName
            assert self._tokenizer.identifier(), print(self._tokenizer._tokens)
            temp_name += self._tokenizer.identifier()
            self._tokenizer.advance()
            # symbol - '('
            assert self._tokenizer.symbol() == '('
            self._tokenizer.advance()
            # expressionList
            temp_nargs = self.compile_expression_list()
            self._writer.write_call(temp_name, temp_nargs)
            # symbol - ')'
            assert  self._tokenizer.symbol() == ')'
            self._tokenizer.advance()

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
        self._local = 0
        self._arg = 0


    def start_subroutine(self):
        # clears the old subroutine dictionary, if it exis
        self._subroutine = dict()
        self._arg = 0
        self._local = 0

    def print_class_table(self, class_name):
        # for debugging the symbol tables
        print('class scope symbol table for', class_name, ':\n')
        for key, value in self._class.items():
            print(key, value)
        print('\n')

    def print_subroutine_table(self, subroutine_name):
        # for debugging the symbol tables
        print('subroutine scope symbol table for', subroutine_name, ':\n')
        for key, value in self._subroutine.items():
            print(key, value)
        print('\n')

    def define(self, var_name, var_type, kind):
        if kind == 'static':
            self._class[var_name] = Symbol(var_type, kind, self._static)
            self._static += 1
        elif kind == 'field':
            self._class[var_name] = Symbol(var_type, kind, self._field)
            self._field += 1
        elif kind == 'local':
            self._subroutine[var_name] = Symbol(var_type, kind, self._local)
            self._local += 1
        elif kind == 'argument':
            self._subroutine[var_name] = Symbol(var_type, kind, self._arg)
            self._arg += 1
        else:
            assert False, "invalid var_type given: " + kind


    def var_count(self, kind):
        if kind == 'static':
            return self._static
        elif kind == 'field':
            return self._field
        elif kind == 'local':
            return self._local
        elif kind == 'argument':
            return self._arg
        else:
            assert False, "invalid var_type given."

    def exists(self, var_name):
        # check if variable with this name exists
        return var_name in self._class or var_name in self._subroutine


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
    
    def write_object_alloc(self, size):
        # allocate space for object on heap, sets pointer to 'this'
        self.write_push('constant', size)
        self.write_call('Memory.alloc', 1)
        self.write_pop('pointer',0)
        
    def write_array_alloc(self, size):
        # puts base address of array on heap
        self.write_push('constant', size)
        self.write_call('Memory.alloc', 1)

    def write_string_constant(self, string):
        # push length of string
        self.write_push('constant',len(string))
        # call String.new, which returns 'this'
        self.write_call('String.new', 1)
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
        elif op == '*':
            self.write_call('Math.multiply', 2)
        elif op == '/':
            self.write_call('Math.divide', 2)
        elif op == '&':
            self._file.writelines(['and\n'])
        elif op == '|':
            self._file.writelines(['or\n'])
        elif op == '<':
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

    def write_comment(self, string):
        self._file.writelines(['// '+string+'\n'])

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
