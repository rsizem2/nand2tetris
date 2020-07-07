'''
Module implementing the SymbolTable component of the JACK compiler.
'''

from collections import namedtuple

Symbol = namedtuple('Symbol', ['type','kind','number'])

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
