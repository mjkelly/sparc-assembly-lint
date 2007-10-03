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

def other_error():
	'''Register an error that's neither due to lex or yacc, or is
	indeterminate.'''
	global other_errors
	other_errors += 1

def get_num_errors():
	'''Get the number of lex errors + yacc errors + other_errors.'''
	return lex_errors + yacc_errors + other_errors

# -----------------------------------------------------------------------------
# Tokens
# -----------------------------------------------------------------------------

tokens = (
	'BINARY_OPERATOR',
	'BLOCK_COMMENT',
	'CALL',
	'CLEAR_MEM_OPCODE',
	'CLOSE_BRACKET',
	'CLOSE_PAREN',
	'COMMA',
	'EQUALS',
	'FLOAT',
	'FORMAT3_OPCODE',
	'IDENTIFIER',
	'INTEGER',
	'LABEL',
	'LINE_COMMENT',
	'LOAD',
	'MINUS',
	'MOV',
	'NEWLINE',
	'OPEN_BRACKET',
	'OPEN_PAREN',
	'PLUS',
	'PSEUDO_OP_0',
	'PSEUDO_OP_INT',
	'PSEUDO_OP_STR',
	'PSEUDO_OP_STRS',
	'PSEUDO_OP_SYMS',
	'REGISTER',
	'SEMICOLON',
	'SET',
	'STRING',
	'SYNTHETIC_ZERO_ARG_OPCODE',
	'UNARY_OPERATOR',
#	'ANNULLED',
#	'CHARACTER',
#	'STORE',
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

	'ld'            :       'LOAD',
	'ldsb'          :       'LOAD',
	'ldsh'          :       'LOAD',
	'ldstub'        :       'LOAD',
	'ldub'          :       'LOAD',
	'lduh'          :       'LOAD',
	'ld'            :       'LOAD',
	'ldd'           :       'LOAD',
# these are also loads, but have different formats:
#	'ldf'           :       'LOAD',
#	'ldfsr'         :       'LOAD',
#	'lddf'          :       'LOAD',
#	'ldc'           :       'LOAD',
#	'ldcsr'         :       'LOAD',
#	'lddc'          :       'LOAD',
#	'ldsba'         :       'LOAD',
#	'ldsha'         :       'LOAD',
#	'lduba'         :       'LOAD',
#	'lduha'         :       'LOAD',
#	'lda'           :       'LOAD',
#	'ldda'          :       'LOAD',
#	'ldstuba'       :       'LOAD',

	# pseudo-ops
	# Those marked 'todo' don't have the right format specified (because it's complicated).
	'.alias'        :       'PSEUDO_OP_0',		# compiler-generated only
	'.align'        :       'PSEUDO_OP_INT',
	'.ascii'        :       'PSEUDO_OP_STRS',
	'.asciz'        :       'PSEUDO_OP_STRS',
	'.byte'         :       'PSEUDO_OP_INT',
	'.common'       :       'PSEUDO_OP_0',		# TODO
	'.double'       :       'PSEUDO_OP_INT',
	'.empty'        :       'PSEUDO_OP_0',
	'.file'         :       'PSEUDO_OP_STR',
	'.global'       :       'PSEUDO_OP_SYMS',
	'.globl'        :       'PSEUDO_OP_SYMS',
	'.half'         :       'PSEUDO_OP_INT',
	'.ident'        :       'PSEUDO_OP_STR',
	'.local'        :       'PSEUDO_OP_SYMS',
	'.noalias'      :       'PSEUDO_OP_0',		# compiler-generated only; TODO
	'.nonvolatile'  :       'PSEUDO_OP_0',
	'.nword'        :       'PSEUDO_OP_INT',
	'.optimstring'  :       'PSEUDO_OP_0',		# compiler-generated only
	'.popsection'   :       'PSEUDO_OP_0',
	'.proc'         :       'PSEUDO_OP_0',		# compiler-generated only; TODO
	'.pushsection'  :       'PSEUDO_OP_0',		# TODO
	'.quad'         :       'PSEUDO_OP_INT',
	'.reserve'      :       'PSEUDO_OP_0',		# TODO
	'.section'      :       'PSEUDO_OP_STR',	# TODO; need second arg
	'.seg'          :       'PSEUDO_OP_SEG',
	'.single'       :       'PSEUDO_OP_INT',
	'.size'         :       'PSEUDO_OP_0',		# TODO
	'.skip'         :       'PSEUDO_OP_INT',
	'.stabn'        :       'PSEUDO_OP_0',		# TODO
	'.stabs'        :       'PSEUDO_OP_0',		# TODO
	'.type'         :       'PSEUDO_OP_0',		# TODO
	'.uahalf'       :       'PSEUDO_OP_INT',
	'.uaword'       :       'PSEUDO_OP_INT',
	'.version'      :       'PSEUDO_OP_STR',
	'.volatile'     :       'PSEUDO_OP_0',
	'.weak'         :       'PSEUDO_OP_SYMS',	# does this take any # of args?
	'.word'         :       'PSEUDO_OP_INT',
	'.xword'        :       'PSEUDO_OP_INT',
	'.xstabs'       :       'PSEUDO_OP_0',		# TODO
}

identifier_regex = r'\.?[a-zA-Z_$\.][a-zA-Z_$\.0-9]*'
label_regex      = r'((' + identifier_regex + r')|\d):'
int_regex        = r'-?(0x)?[0-9]+'
float_regex      = r'0r-?((\d+(\.\d*)?)|(\.\d+))([eE]-?\d+)?'
string_regex     = r'"([^"\\]|(\\.))*"'
char_regex       = r"'(([^'\\])|(\\.))'"
reg_regex        = r'%[\w]+'	# very permissive; screen after matching

# we're skipping %lo, %hi, etc for now, because they look like registers, and +
# and - because they're already defined as PLUS and MINUS.
unary_operator_regex    = r'~'
binary_operator_regex   = r'(\*|/|%|\^|<<|>>|&|\|)'
# these are the canonical lists, but they cause ambiguities:
#unary_operator_regex    = r'(\+|-|~|%lo|%hi|%r_disp32|%r_disp64|%r_plt32|%r_plt64)'
#binary_operator_regex   = r'(\+|-|\*|/|%|\^|<<|>>|&|\|)'

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

def t_PLUS(t):
	r'\+'
	print_token(t)
	return t

def t_MINUS(t):
	r'-'
	print_token(t)
	return t

def t_OPEN_BRACKET(t):
	r'\['
	print_token(t)
	return t

def t_CLOSE_BRACKET(t):
	r'\]'
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
	if not lexer.seen_opcode:
		t.type = reserved.get(t.value, 'IDENTIFIER')
	else:
		t.type = 'IDENTIFIER'
	lexer.seen_opcode = 1
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

def t_OPEN_PAREN(t):
	r'\('
	print_token(t)
	return t

def t_CLOSE_PAREN(t):
	r'\)'
	print_token(t)
	return t

# We probably need this later to do some error reporting. It will make all the
# rules more complex...
#def t_WHITESPACE(t):
#	r'[ \t]+'
#	return t

t_ignore = " \t"

def t_UNARY_OPERATOR(t):
	print_token(t)
	return t
t_UNARY_OPERATOR.__doc__ = unary_operator_regex

def t_BINARY_OPERATOR(t):
	print_token(t)
	return t
t_BINARY_OPERATOR.__doc__ = binary_operator_regex

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
		| macro'''
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
		| set_instr
		| pseudo_op
		| load'''
#		| inc_dec
#		| jump
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

# TODO(mkelly): make the arg lists right
def p_pseudo_op(p):
	'''pseudo_op : PSEUDO_OP_0
	             | PSEUDO_OP_INT integer_expr
	             | PSEUDO_OP_STR STRING
	             | PSEUDO_OP_STRS strings
	             | PSEUDO_OP_SYMS syms'''
	debug_fname()
	p[0] = plist(p)

def p_load(p):
	'''load : LOAD address COMMA reg'''
	debug_fname()
	p[0] = plist(p)

def p_comment(p):
	'''comment : BLOCK_COMMENT
	           | LINE_COMMENT'''
	debug_fname()
	p[0] = plist(p)

def p_macro(p):
	'''macro : IDENTIFIER EQUALS integer_expr
	             | IDENTIFIER EQUALS float_expr
		     | IDENTIFIER EQUALS IDENTIFIER'''
	debug_fname()
	p[0] = plist(p)

# ----------
# Arguments
# ----------

# TODO(dlindqui): An address can also be formed by adding or subtracting registers and constants.
def p_address(p):
	'''address : OPEN_BRACKET reg CLOSE_BRACKET
	           | OPEN_BRACKET reg PLUS reg CLOSE_BRACKET
	           | OPEN_BRACKET reg PLUS integer_expr CLOSE_BRACKET
		   | OPEN_BRACKET reg MINUS integer_expr CLOSE_BRACKET'''
	debug_fname()
	p[0] = plist(p)

def p_reg_or_imm(p):
	'''reg_or_imm : const13 
	             | reg'''
	debug_fname()
	p[0] = plist(p)

# TODO(dlindqui): These should be floating point registers (f0-f31) only.
#def p_freq(p):
#	'''freq : REGISTER'''
#	debug_fname()
#	p[0] = plist(p)
#(unused; suppressing warnings)
	

# TODO(dlindqui): These should be general purpose (r, g, o, l, i) only.
def p_reg(p):
	'''reg : REGISTER'''
	debug_fname()
	p[0] = plist(p)

# A signed constant which fits in 13 bits. It can be the result of the evaluation of a symbol expression. 
#TODO(dlindqui): We need to be able to handle evaluations here and optionally check range (must fit in 13 bits).
def p_const13(p):
	'''const13 : integer_expr'''
	debug_fname()
	p[0] = plist(p)

# A constant which fits in 22 bits. It can be the result of the evaluation of a symbol expression. 
#TODO(dlindqui): We need to be able to handle evaluations here and optionally check range (must fit in 13 bits).
# Note: this is only used by sethi.
#def p_const22(p):
#	'''const22 : integer_expr 
#	             | IDENTIFIER'''
#	debug_fname()
#	p[0] = plist(p)


# Note: We don't even consider precedence here, because we don't calculate the
# expressions.
def p_integer_expr(p):
	'''integer_expr : INTEGER
			| IDENTIFIER
	                | MINUS integer_expr
			| PLUS integer_expr
			| UNARY_OPERATOR integer_expr
			| integer_expr BINARY_OPERATOR integer_expr
			| integer_expr PLUS integer_expr
			| integer_expr MINUS integer_expr
			| OPEN_PAREN integer_expr CLOSE_PAREN'''
	debug_fname()
	p[0] = plist(p)

# TODO(mkelly): expand to include non-trivial expressions
def p_float_expr(p):
	'''float_expr : FLOAT'''
	debug_fname()
	p[0] = plist(p)

def p_strings(p):
	'''strings : STRING
	           | STRING COMMA strings'''
	debug_fname()
	p[0] = plist(p)

def p_syms(p):
	'''syms : IDENTIFIER
	        | IDENTIFIER COMMA syms'''
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
	global other_errors 
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
	other_errors = 0
	verbosity = verbosity_level
