# README

This repository contains my scripts for realizing the JACK software hierarchy as described in "The Elements of Computing Systems". These solutions mostly follow the APIs outlined in the book with some minor changes and additions, all written in Python. Most of this work was done between April and May 2020, however I may clean up some of the files in the future.

# Assembler

Converts HACK .asm files into binary code .hack files. Assumes 'Assembler.py' is ran in a directory with a folder called 'asm' containing the HACK assembly code to be translated. Assembler.py contains the following classes:

* Assembler - takes in input .asm, preprocesses it for Parser
* Parser - parses machine code into it's dest, comp and jump components.
* Symbol Table - manages a symbol table for each input file, includes the default named registers and also handles user-defined variables.
* Code - outputs the binary code corresponding to each dest, comp or jump command.

# VM Translator

Converts intermediate .vm code into HACK .asm code which can then be assembled into binary via the Assembler. The file 'VMTranslator.py' accepts one argument representing either a .vm file or a folder containing multiple .vm files. Will create a file called '.asm' with the resulting translated code. VMTranslator contains the following classes:

* VMTranslator - handles each input files as well as communication between the Parser and CodeWriter.
* Parser - preprocesses input file, outputs each vm command one by one.
* CodeWriter - outputs .asm based on input given by the parser.

# JACK Compiler

Converts JACK source code into the intermediate .vm code, which can then by further using the VM translators and Assembler. Run 'JackCompiler.py' with a single argument denoting either a .jack file or a folder containing multiple .jack files. If given a single file, will create an identically named .vm file with the resulting translated code, otherwise creates one such file for each .jack source file in the given directory. The Compiler contains the following classes:

* JackAnalyzer - handles input files as well as communication between the other objects.
* JackTokenizer - preprocesses and tokenizes input into a stream of individual tokens
* CompilationEngine - compiles the various components of a JACK program using the expected structure of a valid JACK program.
* SymbolTable - tracks the various variables used in a given .jack source file
* VMWriter - handles the writing of the VM code to the output .vm file.

There is also a JACKAnalyzerXML.py which parses the input .jack source into it's corresponding parse tree, visualized in XML.
