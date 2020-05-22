"""
A Jack source code analyzer based on the implementaton contract from Chapter 10 of 'The Elements of Computing Systems'.
"""

import sys, os, re

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
        self._code = CompilationEngine(self._name)
        for file in self._files:
            self._tokenizer = JackTokenizer(file)
            #self._code.filename(file.replace('.vm','').split('/')[-1])
        self._code.close()
    

class JackTokenizer():
    '''
    Tokenizes input .jack file using regular expressions
    '''
    
    def __init__(self, filename):
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
        self._tokens = None
        self.tokenize(self._input)
        self._token = None
        self._type = None
        self._finished = False
        
    def tokenize(self, string):
        tokens = []
        types = []
        while string:
            match = self._symbol.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('SYMBOL')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._integer.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('INT_CONST')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._keyword.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('KEYWORD')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._string.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('STRING_CONST')
                string = re.sub('^[\s]+','', string[end:])
                continue
            match = self._identifier.match(string)
            if match:
                # next token is symbol
                start, end = match.span()
                tokens.append(string[start:end])
                types.append('IDENTIFIER')
                string = re.sub('^[\s]+','', string[end:])
                continue
            print('invalid next token')
            print(string)
            return
        self._tokens = iter(zip(tokens,types))
        for x,y in zip(types, tokens):
            print(x,y)
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
        return self._finished
    
    def advance(self):
        temp = next(self._tokens, None)
        if self._finished:
            self._token = None
            self._type = None
        elif temp is None:
            self._finished = True
            self._token = None
            self._type = None
        else:
            self._token, self._type = temp
        
    
    def keyword(self):
        if self._type != 'KEYWORD':
            return None
        else:
            return self._token
    
    def symbol(self):
        if self._type != 'SYMBOL':
            return None
        else:
            return self._token
    
    def identifier(self):
        if self._type != 'IDENTIFIER':
            return None
        else:
            return self._token
    
    def int_value(self):
        if self._type != 'INT_CONST':
            return None
        else:
            return self._token
    
    def string_value(self):
        if self._type != 'STRING_CONST':
            return None
        else:
            return self._token
    
           
class CompilationEngine():
    '''
    Parses a stream of jack tokens recursively
    '''
    
    def __init__(self, filename):
        pass
    
    def close(self):
        pass
    
    def compile_class(self):
        pass
    
    def compile_class_var_dec(self):
        pass
    
    def compile_subroutine(self):
        pass
    
    def compile_parameter_list(self):
        pass
    
    def compile_var_dec(self):
        pass
    
    def compile_statements(self):
        pass
    
    def compile_do(self):
        pass
    
    def compile_let(self):
        pass
    
    def compile_while(self):
        pass
    
    def compile_return(self):
        pass
    
    def compile_if(self):
        pass
    
    def compile_expression(self):
        pass
    
    def compile_term(self):
        pass
    
    def compile_expression_list(self):
        pass

if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    JackAnalyzer(filename)