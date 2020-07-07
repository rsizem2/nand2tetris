'''
Module implementing the CompilationEngine component of the JACK compiler.

The CompilationEngine parses Jack code assuming that the input follows valid grammar rules 

'''

from symboltable import SymbolTable 
from vmwriter import VMWriter

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
