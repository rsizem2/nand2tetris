"""
A Jack source code analyzer based on the implementaton contract from Chapter 10 of 'The Elements of Computing Systems'.

The JackAnalyzer class communicates between the tokenizer and compilation engine. 

To use the compiler run  'python JackCompiler.py <filename>' where <filename> is a .jack file or a directory containing .jack files.

"""

import os, sys
from tokenizer import JackTokenizer
from engine import CompilationEngine

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



if __name__ == '__main__':
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ""
    JackAnalyzer(filename)
