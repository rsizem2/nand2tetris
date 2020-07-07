from collections import deque
import re

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
