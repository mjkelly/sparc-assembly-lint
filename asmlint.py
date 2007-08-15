#!/usr/bin/python
# -----------------------------------------------------------------------------
# asmlint.py -- lint for SPARC assembly
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Sat Aug 11 22:40:30 PDT 2007
#
# Errors to catch:
# - no save instruction
# - no ret/restore
# - suspicious save offsets
# - no nop in delay slot
# - strange registers (including %lo)
# - mention broken gcc behavior on labels without leading .L?
# - no label with same name as filename
# - check alignment
# - check for correct .section
# - check for .global
# - ...?
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
def print_token(t):
	debug("%s=%s" % (t.type, t.value))
	
def warn(msg):
	log('WARNING', msg)

def debug(msg):
	log('DEBUG', msg)

def log(level, msg):
	sys.stderr.write("%s: %s\n" % (level, msg))

def func_name(level=2):
	return sys._getframe(level).f_code.co_name

def debug_fname():
	debug(func_name())

def plist(p):
	ret_list = [func_name(2)]
	for item in p[1:]:
		ret_list.append(item)
	print "\t" + str(ret_list)
	return ret_list

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
	r'\![^\n]*'
	#print_token(t)
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
	print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)

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
	print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)
    
# -----------------------------------------------------------------------------
# Parsing rules
# -----------------------------------------------------------------------------

# top-level element
def p_lines(p):
	'''lines : lines line
 	           | '''
	debug_fname()
	p[0] = plist(p)

# NOTE: These are _not_ lines. They may be more than one line. I cannot think
# of a good name.
def p_line(p):
	'''line : label
	        | comment
		| command
		| varassign'''
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

def p_operand_list_nonempty(p):
	'''operand_list_nonempty : operand
	                         | operand COMMA operand_list_nonempty'''
	debug_fname()
	p[0] = plist(p)

def p_operand_list(p):
	'''operand_list : operand_list_nonempty
	                | '''
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
	'''command : opcode operand_list'''
	debug_fname()
	p[0] = plist(p)

def p_error(t):
    print "Syntax error at '%s'" % t.value

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

lexer = None
yacc = None

def main():
	global lexer
	global yacc

	# build lexer and parser
	lexer = lex.lex()
	yacc.yacc()

	lexer.seen_label = 0
	lexer.seen_opcode = 0

	opt_parser = OptionParser(usage="%prog [OPTIONS] [FILENAME]")

	opt_parser.add_option("--check-line-length", action="store_true", dest="check_line_length",
		help="Check line length.")
	opt_parser.add_option("--max-line-length", action="store", dest="max_line_length",
		type="int", help="Maximum acceptable line length when --check-line-length is on.")

	opt_parser.set_defaults(max_line_length=80)
	opt_parser.set_defaults(check_line_length=False)

	lineno = 0
	input_filename = '<STDIN>'
	input_file = sys.stdin

	(opts, args) = opt_parser.parse_args()

	if len(args) > 1:
		opt_parser.print_help()
		sys.exit(2)
	elif len(args) > 0:
		input_filename = args[0]
		input_file = open(input_filename, 'r')

	while True:
		lineno += 1
		s = input_file.readline()
		debug(">>> " + s.rstrip())

		if opts.check_line_length and len(s.rstrip('\n')) > opts.max_line_length:
			warn("%s:%d exceeds %d chars." % (input_filename, lineno, opts.max_line_length))

		if s == "":
			break
		try:
			yacc.parse(s)
		except Exception, e:
			print 'Exception caught while parsing line %d!\n' % lineno
			raise e

			

	if input_file != sys.stdin:
		input_file.close()

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

import ply.lex as lex
import ply.yacc as yacc

from optparse import OptionParser, OptionGroup
import sys

if __name__ == '__main__':
	main()

