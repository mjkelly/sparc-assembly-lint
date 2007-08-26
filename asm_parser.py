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
#	'ANNULLED',
	'BLOCK_COMMENT',
#	'CHARACTER',
	'COMMA',
	'SEMICOLON',
	'EQUALS',
	'IDENTIFIER',
	'INTEGER',
	'FLOAT',
	'LABEL',
	'LINE_COMMENT',
	'REGISTER',
#	'STRING',
	'MOV',
	'SET',
	'CALL',
	'NEWLINE',
	'FORMAT3_OPCODE',
	'SYNTHETIC_ZERO_ARG_OPCODE',
	'CLEAR_MEM_OPCODE'
)

# comments are the only multi-line things we have to deal with
states = (
	('INCOMMENT', 'exclusive'),
)

reserved = {
	# specials
	'call' : 'CALL',

	# Synthetic (no args)
	'ret'		:	'SYNTHETIC_ZERO_ARG_OPCODE',
	'retl'		:	'SYNTHETIC_ZERO_ARG_OPCODE',
	'nop'		:	'SYNTHETIC_ZERO_ARG_OPCODE',

	'clr'		:	'CLEAR_MEM_OPCODE',
	'clrb'		:	'CLEAR_MEM_OPCODE',
	'clrh'		:	'CLEAR_MEM_OPCODE',

	'mov'		:	'MOV',
	'set'		:	'SET',

	# format3 opcodes
	'add'           :       'FORMAT3_OPCODE',
	'addcc'         :       'FORMAT3_OPCODE',
	'addx'          :       'FORMAT3_OPCODE',
	'addxcc'        :       'FORMAT3_OPCODE',
	'and'           :       'FORMAT3_OPCODE',
	'restore'       :       'FORMAT3_OPCODE',
	'save'          :       'FORMAT3_OPCODE',
	'sdiv'          :       'FORMAT3_OPCODE',
	'sdivcc'        :       'FORMAT3_OPCODE',
	'sll'           :       'FORMAT3_OPCODE',
	'smul'          :       'FORMAT3_OPCODE',
	'smulcc'        :       'FORMAT3_OPCODE',
	'sra'           :       'FORMAT3_OPCODE',
	'srl'           :       'FORMAT3_OPCODE',
	'sub'           :       'FORMAT3_OPCODE',
	'subcc'         :       'FORMAT3_OPCODE',
	'subx'          :       'FORMAT3_OPCODE',
	'subxcc'        :       'FORMAT3_OPCODE',
	'taddcc'        :       'FORMAT3_OPCODE',
	'taddcctv'      :       'FORMAT3_OPCODE',
	'tsubcc'        :       'FORMAT3_OPCODE',
	'tsubcctv'      :       'FORMAT3_OPCODE',
	'udiv'          :       'FORMAT3_OPCODE',
	'udivcc'        :       'FORMAT3_OPCODE',
	'umul'          :       'FORMAT3_OPCODE',
	'umulcc'        :       'FORMAT3_OPCODE',
	'xnor'          :       'FORMAT3_OPCODE',
	'xnorcc'        :       'FORMAT3_OPCODE',
	'xor'           :       'FORMAT3_OPCODE',

}

identifier_regex = r'\.?[a-zA-Z_$\.][a-zA-Z_$\.0-9]*'
label_regex      = r'((' + identifier_regex + r')|\d):'
int_regex        = r'-?(0x)?[0-9]+'
float_regex      = r'0r-?((\d+(\.\d*)?)|(\.\d+))([eE]-?\d+)?'
string_regex     = r'"([^"\\]|(\\.))*"'
char_regex       = r"'(([^'\\])|(\\.))'"
reg_regex        = r'%[\w]+'	# very permissive; screen after matching
operator_regex   = r'(+|-|\*|/|%|^|<<|>>|&|\||%hi|%lo)'

def t_LINE_COMMENT(t):
	r'![^\n]*'
	print_token(t)
	return t

def t_COMMA(t):
	r','
	print_token(t)
	return t

def t_SEMICOLON(t):
	r';'
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
	t.type = reserved.get(t.value, 'IDENTIFIER')
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

def t_NEWLINE(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")
	t.lexer.seen_label = 0
	t.lexer.seen_opcode = 0

def t_error(t):
	error("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)
	lex_error()

    
# -----------------------------------------------------------------------------
# Parsing rules
# -----------------------------------------------------------------------------

def p_file(p):
	'''file : line
		| line NEWLINE file'''
	debug_fname()
	p[0] = plist(p)

def p_line(p):
	'''line : 
		| comment
		| statementlist
		| statementlist comment'''
	debug_fname()
	p[0] = plist(p)

def p_statementlist(p):
	'''statementlist : statement
		| statement SEMICOLON statementlist'''
	debug_fname()
	p[0] = plist(p)

def p_statement(p):
	'''statement : label
		| instruction 
		| label instruction
		| varassign'''
	debug_fname()
	p[0] = plist(p)

def p_label(p):
	'''label : LABEL'''
	debug_fname()
	p[0] = plist(p)

def p_instruction(p):
	'''instruction : format1
		| format3
		| syntheticzeroargs
		| clear_mem
		| mov_instr
		| set_instr'''
#		| inc_dec
#		| jump
#		| load
#		| compare
#		| format3c
#		| branch
#		| synth
#		| btest
#		| mov
#		| neg
#		| not
#		| sethi
#		| test'''
	debug_fname()
	p[0] = plist(p)

def p_format1(p):
	'''format1 : CALL IDENTIFIER'''
	debug_fname()
	p[0] = plist(p)

def p_format3(p):
	'''format3 : FORMAT3_OPCODE reg COMMA reg_or_imm COMMA reg'''
	debug_fname()
	p[0] = plist(p)

def p_syntheticzeroargs(p):
	'''syntheticzeroargs : SYNTHETIC_ZERO_ARG_OPCODE'''
	debug_fname()
	p[0] = plist(p)

#TODO(dlindqui) We need to handle case CLEAR_MEM_OPCODE address
def p_clear_mem(p):
	'''clear_mem : CLEAR_MEM_OPCODE reg'''
	debug_fname()
	p[0] = plist(p)

def p_mov_istr(p):
	'''mov_instr : MOV reg_or_imm COMMA reg'''
	debug_fname()
	p[0] = plist(p)

def p_set_instr(p):
	'''set_instr : SET integer_expr COMMA reg'''
	debug_fname()
	p[0] = plist(p)


# TODO(mkelly): expand to include non-trivial expressions
#def p_character_expr(p):
#	'''character : CHARACTER'''
#	debug_fname()
#	p[0] = plist(p)

#def p_string(p):
#	'''string : STRING'''
#	debug_fname()
#	p[0] = plist(p)

#def p_name(p):
#	'''name : NAME'''
#	debug_fname()
#	p[0] = plist(p)

def p_comment(p):
	'''comment : BLOCK_COMMENT
	           | LINE_COMMENT'''
	debug_fname()
	p[0] = plist(p)

def p_varassign(p):
	'''varassign : IDENTIFIER EQUALS integer_expr
	             | IDENTIFIER EQUALS float_expr
		     | IDENTIFIER EQUALS IDENTIFIER'''
	debug_fname()
	p[0] = plist(p)

# ----------
# Arguments
# ----------

# TODO(dlindqui): An address can also be formed by adding or subtracting registers and constants.
#
# e.g:
# regrs1 + regrs2
# regrs1 + const13
# regrs1 - const13
# const13 + regrs1
# const13 
def p_address(p):
	'''address : reg_or_imm'''

def p_reg_or_imm(p):
	'''reg_or_imm : const13 
	             | reg'''
	debug_fname()
	p[0] = plist(p)

# TODO(dlindqui): These should be floating point registers (f0-f31) only.
def freq(p):
	'''freq : REGISTER'''
	debug_fname()
	p[0] = plist(p)
	

# TODO(dlindqui): These should be general purpose (r, g, o, l, i) only.
def p_reg(p):
	'''reg : REGISTER'''
	debug_fname()
	p[0] = plist(p)

# A signed constant which fits in 13 bits. It can be the result of the evaluation of a symbol expression. 
#TODO(dlindqui): We need to be able to handle evaluations here and optionally check range (must fit in 13 bits).
def p_const13(p):
	'''const13 : integer_expr 
	             | IDENTIFIER'''

# A constant which fits in 22 bits. It can be the result of the evaluation of a symbol expression. 
#TODO(dlindqui): We need to be able to handle evaluations here and optionally check range (must fit in 13 bits).
# Note: this is only used by sethi.
#def p_const22(p):
#	'''const22 : integer_expr 
#	             | IDENTIFIER'''


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

# ----------
# Misc.
# ----------
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
