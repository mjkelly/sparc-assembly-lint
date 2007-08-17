#!/usr/bin/python
# -----------------------------------------------------------------------------
# asm_parser.py -- Parse SPARC assembly files.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sat Aug 11 22:40:30 PDT 2007
# -----------------------------------------------------------------------------

from optparse import OptionParser, OptionGroup
import sys
import pprint

import ply.lex as lex
import ply.yacc as yacc


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def print_token(t):
	debug("%s=%s" % (t.type, t.value))

def error(msg):
	if verbosity >= 0:
		log('ERROR', msg)
	
def warn(msg):
	if verbosity >= 0:
		log('WARNING', msg)

def debug(msg):
	if verbosity >= 1:
		log('DEBUG', msg)

def info(msg):
	if verbosity >= 0:
		print msg

def log(label, msg):
	'''Print the given message, prefixed with the given label (DEBUG,
	WARNING, etc) to stderr.'''
	sys.stderr.write("%s: %s\n" % (label, msg))

def func_name(level=2):
	'''Get the name of a function on the call stack.
		@param level 1 = func_name's calling function, 2 caller's
		caller, etc.'''
	return sys._getframe(level).f_code.co_name

def debug_fname():
	'''Print the name of the calling function as debug output.'''
	debug(func_name())

def plist(p):
	'''Make a list from the calling function (assumed to the the left side
	of a production) and the given production list.
		@param p list of entities on the right side of a production.'''
	ret_list = [func_name(2)]
	for item in p[1:]:
		ret_list.append(item)
	pp = pprint.PrettyPrinter(indent=2)
	if verbosity >= 2:
		pp.pprint(ret_list)
	return ret_list

def lex_error():
	'''Register a lex error.'''
	global lex_errors
	lex_errors += 1

def yacc_error():
	'''Register a yacc error.'''
	global yacc_errors
	yacc_errors += 1

def get_num_errors():
	'''Get the number of lex errors + yacc errors.'''
	return lex_errors + yacc_errors

# -----------------------------------------------------------------------------
# Tokens
# -----------------------------------------------------------------------------

tokens = (
	'ANNULLED',
	'BLOCK_COMMENT',
	'CHARACTER',
	'COMMA',
	'EQUALS',
	'FLOAT',
	'IDENTIFIER',
	'INTEGER',
	'LABEL',
	'LINE_COMMENT',
	'NAME',
	'REGISTER',
	'STRING',
)

# comments are the only multi-line things we have to deal with
states = (
	('INCOMMENT', 'exclusive'),
)

identifier_regex = r'\.?[a-zA-Z_][a-zA-Z0-9_]*'
label_regex      = identifier_regex + r':'
# TODO(mkelly): allow hex, octal
int_regex        = r'-?[0-9]+'
float_regex      = r'-?((\d+(\.\d*)?)|(\.\d+))([eE]-?\d+)?'
string_regex     = r'"([^"\\]|(\\.))*"'
char_regex       = r"'(([^'\\])|(\\.))'"
reg_regex        = r'%([gilo][0-9]|fp|sp|hi|lo)'

def t_LINE_COMMENT(t):
	r'![^\n]*'
	print_token(t)
	#debug("<block comment line>")
	return t

def t_COMMA(t):
	r','
	print_token(t)
	return t

def t_begincomment(t):
	r'/\*'
	t.lexer.block_comment_data = t.value
	t.lexer.begin('INCOMMENT')
	pass

# endcomment needs to be first to take precedence over continue
def t_INCOMMENT_endcomment(t):
	r'\*/'
	t.lexer.block_comment_data += t.value
	t.value = t.lexer.block_comment_data
	t.type = 'BLOCK_COMMENT'
	print_token(t)
	t.lexer.begin('INITIAL')
	return t

def t_INCOMMENT_newline(t):
	r'\n+'
	t.lexer.block_comment_data += t.value
	t.lexer.lineno += t.value.count("\n")
	#debug("<newline>")

def t_INCOMMENT_continue(t):
	r'.'
	t.lexer.block_comment_data += t.value
	pass

def t_INCOMMENT_error(t):
	error("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)
	lex_error()

t_INCOMMENT_ignore = ""

# this includes labels, opcodes, etc
def t_LABEL(t):
	print_token(t)
	lexer.seen_label = 1
	return t
t_LABEL.__doc__ = label_regex

def t_IDENTIFIER(t):
	if not t.lexer.seen_opcode:
		t.lexer.seen_opcode = 1
		t.type = 'IDENTIFIER'
	else:
		if t.value == 'a':
			t.type = 'ANNULLED'
		else:
			t.type = 'NAME'
	print_token(t)
	return t
t_IDENTIFIER.__doc__ = identifier_regex

def t_REGISTER(t):
	# strip off leading "%"
	t.value = t.value[1:]
	print_token(t)
	return t
t_REGISTER.__doc__ = reg_regex

def t_INTEGER(t):
	print_token(t)
	return t
t_INTEGER.__doc__ = int_regex

def t_FLOAT(t):
	print_token(t)
	return t
t_FLOAT.__doc__ = float_regex

def t_STRING(t):
	print_token(t)
	return t
t_STRING.__doc__ = string_regex

def t_CHARACTER(t):
	print_token(t)
	return t
t_CHARACTER.__doc__ = char_regex

# EQUALS needs to be below anything else that could contain an '='.
def t_EQUALS(t):
	r'='
	print_token(t)
	return t

# We probably need this later to do some error reporting. It will make all the
# rules more complex...
#def t_WHITESPACE(t):
#	r'[ \t]+'
#	return t

t_ignore = " \t"

def t_newline(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")
	t.lexer.seen_label = 0
	t.lexer.seen_opcode = 0
	#debug("<newline>")

def t_error(t):
	error("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)
	lex_error()

    
# -----------------------------------------------------------------------------
# Parsing rules
# -----------------------------------------------------------------------------

# NOTE: These are _not_ lines. They may be more than one line. I cannot think
# of a good name.
def p_line(p):
	'''line : label
	        | comment
		| command
		| varassign
		| line line
		|'''
	debug_fname()
	p[0] = plist(p)

# TODO(mkelly): expand to include non-trivial expressions
def p_integer_expr(p):
	'''integer_expr : INTEGER'''
	debug_fname()
	p[0] = plist(p)

# TODO(mkelly): expand to include non-trivial expressions
def p_float_expr(p):
	'''float_expr : FLOAT'''
	debug_fname()
	p[0] = plist(p)

def p_register(p):
	'''register : REGISTER'''
	debug_fname()
	p[0] = plist(p)

def p_string(p):
	'''string : STRING'''
	debug_fname()
	p[0] = plist(p)

def p_character(p):
	'''character : CHARACTER'''
	debug_fname()
	p[0] = plist(p)

def p_label(p):
	'''label : LABEL'''
	debug_fname()
	p[0] = plist(p)

def p_name(p):
	'''name : NAME'''
	debug_fname()
	p[0] = plist(p)

def p_operand(p):
	'''operand : integer_expr
	           | float_expr
	           | register
		   | string
		   | character
		   | name'''
	debug_fname()
	p[0] = plist(p)

def p_operand_list(p):
	'''operand_list : operand_list COMMA operand_list
	                | operand'''
	debug_fname()
	p[0] = plist(p)


def p_comment(p):
	'''comment : BLOCK_COMMENT
	           | LINE_COMMENT'''
	debug_fname()
	p[0] = plist(p)

def p_varassign(p):
	'''varassign : IDENTIFIER EQUALS operand'''
	debug_fname()
	p[0] = plist(p)

def p_opcode(p):
	'''opcode : IDENTIFIER
	          | IDENTIFIER COMMA ANNULLED'''
	debug_fname()
	p[0] = plist(p)

def p_command(p):
	'''command : opcode operand_list
	           | opcode'''
	debug_fname()
	p[0] = plist(p)

def p_error(p):
	error("Syntax error at token %s" % str(p))
	if p is not None:
		error("\t(type = %s, value = %s)" % (str(p.type), str(p.value)))
	yacc_error()
	

def init_parser(verbosity_level):
	'''Initialize lex and yacc. You can call asm_lint.yacc.parse() after you call this.
		@param verbosity_level Output verbosity: 0, 1, 2 (higher is more).
	'''
	# build lexer and parser
	global lex_errors
	global yacc_errors 
	global lexer
	global yacc
	global verbosity
	lexer = lex.lex()
	yacc.yacc()

	# init globals
	lexer.seen_label = 0
	lexer.seen_opcode = 0
	lex_errors = 0
	yacc_errors = 0
	verbosity = verbosity_level
