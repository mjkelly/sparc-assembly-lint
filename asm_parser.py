# -----------------------------------------------------------------------------
# asm_parser.py -- Parse SPARC assembly files.
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Wed Nov 14 20:34:57 PST 2007
# -----------------------------------------------------------------------------

from symbols import reserved, section_declarations
import ast

from optparse import OptionParser, OptionGroup

import ply.lex as lex
import ply.yacc as yacc

import sys
import logging
import pprint
import re

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

class ParseError(RuntimeError): pass

def print_token(t):
	debug("%s=%s" % (t.type, t.value))

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
		if item not in plist_ignore_tokens:
			ret_list.append(item)
	if loglevel == logging.DEBUG:
		pp = pprint.PrettyPrinter(indent=2)
		pp.pprint(ret_list)
	return ret_list

def flatlist(p):
	vals = []
	for item in p[1:]:
		if type(item) == list:
			vals.extend(item)
		else:
			vals.append(item)
	return vals

def init_parser(parse_result):
	'''Initialize lex and yacc. You can call asm_lint.yacc.parse() after you call this.
		@param opts_ Program options, from command-line.
	'''
	# build lexer and parser
	global lexer
	global yacc
	lexer = lex.lex()
	yacc.yacc()

	# Add loggers to file
	global debug
	global info
	global warn
	global error
	global loglevel
	debug = parse_result.debug
	info = parse_result.info
	warn = parse_result.warn
	error = parse_result.error
	loglevel = parse_result.logger.level

# -----------------------------------------------------------------------------
# Global data structures
# -----------------------------------------------------------------------------

# flex tokens
tokens = (
	'ID',
	'REG',
	'COMMA',
	'INT',
	'FLOAT',
	'NEWLINE',
	'COLON',
	'STRING',
	'CHAR',
	'EQUALS',
	'SEMI',
	'LBRACKET',
	'RBRACKET',
	'PLUS',
	'MINUS',
	'MUL',
	'DIV',
	'MOD',
	'XOR',
	'LSHIFT',
	'RSHIFT',
	'AND',
	'OR',
	'NOT',
	'LPAREN',
	'RPAREN',
	'LINECOMMENT',
	'BLOCKCOMMENT',
	'HASH',
	'LO',
	'HI',
	'UNARYNOP',
) + tuple(dict.fromkeys([ x['type'] for x in reserved.values() ]).keys())

# comments are the only multi-line things we have to deal with
states = (
	('INCOMMENT', 'exclusive'),
)

precedence = (
	('left', 'OR'),
	('left', 'XOR'),
	('left', 'AND'),
	('left', 'LSHIFT', 'RSHIFT'),
	('left', 'PLUS', 'MINUS'),
	('left', 'MUL', 'DIV', 'MOD'),
	('right', 'NOT', 'LO', 'HI', 'UNARYNOP'),
)

# These tokens are ignored by plist() because they're leftover syntactic
# elements that have no real meaning.
plist_ignore_tokens = (
	',',
)

id_regex         = r'\.?[a-zA-Z_$\.][a-zA-Z_$\.0-9]*'
int_regex        = r'-?((0x[0-9a-fA-F]+)|([0-9]+))'
float_regex      = r'0r-?((\d+(\.\d*)?)|(\.\d+))([eE]-?\d+)?'
string_regex     = r'"([^"\\]|(\\.))*"'
char_regex       = r"'(([^'\\])|(\\.))'"
reg_regex        = r'%([ilog][0-7]|[rfc][0-9]|[rfc][12][0-9]|[rfc]30|[rfc]31|sp|fp|fsr|fq|csr|cq|psr|tbr|wim|y)'

t_ignore = " \t"

def t_LINECOMMENT(t):
	r'![^\n]*'
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
	t.type = 'BLOCKCOMMENT'
	print_token(t)
	t.lexer.begin('INITIAL')
	return t

def t_INCOMMENT_newline(t):
	r'\n+'
	t.lexer.block_comment_data += t.value
	t.lexer.lineno += len(t.value)

def t_INCOMMENT_continue(t):
	r'.'
	t.lexer.block_comment_data += t.value
	pass

def t_INCOMMENT_error(t):
	error("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

t_INCOMMENT_ignore = ""

def t_ID(t):
	# Split off any reserved words. They're or'd back into the 'id' production later.
	if t.value in reserved:
		t.type = reserved[t.value]['type']
	print_token(t)
	return t
t_ID.__doc__ = id_regex

# before REG
def t_LO(t):
	r'%lo'
	print_token(t)
	return t

# before REG
def t_HI(t):
	r'%hi'
	print_token(t)
	return t

# before REG
# These are all unary operators we recognize but don't implement.
def t_UNARYNOP(t):
	r'%(r_disp32|r_plt32)'
	print_token(t)
	return t

def t_REG(t):
	print_token(t)
	return t
t_REG.__doc__ = reg_regex

# float must be before int
def t_FLOAT(t):
	print_token(t)
	return t
t_FLOAT.__doc__ = float_regex

def t_INT(t):
	print_token(t)
	return t
t_INT.__doc__ = int_regex

def t_STRING(t):
	t.value = t.value[1:-1]   # Strip off quote marks
	print_token(t)
	return t
t_STRING.__doc__ = string_regex

def t_CHAR(t):
	print_token(t)
	return t
t_CHAR.__doc__ = char_regex

def t_COMMA(t):
	r','
	print_token(t)
	return t

def t_SEMI(t):
	r';'
	print_token(t)
	return t

def t_COLON(t):
	r':'
	print_token(t)
	return t

def t_EQUALS(t):
	r'='
	print_token(t)
	return t

def t_LBRACKET(t):
	r'\['
	print_token(t)
	return t

def t_RBRACKET(t):
	r'\]'
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

def t_MUL(t):
	r'\*'
	print_token(t)
	return t

def t_DIV(t):
	r'/'
	print_token(t)
	return t

def t_MOD(t):
	r'%'
	print_token(t)
	return t

def t_XOR(t):
	r'\^'
	print_token(t)
	return t

def t_LSHIFT(t):
	r'<<'
	print_token(t)
	return t

def t_RSHIFT(t):
	r'>>'
	print_token(t)
	return t

def t_AND(t):
	r'&'
	print_token(t)
	return t

def t_OR(t):
	r'\|'
	print_token(t)
	return t

def t_NOT(t):
	'~'
	print_token(t)
	return t

def t_LPAREN(t):
	r'\('
	print_token(t)
	return t

def t_RPAREN(t):
	r'\)'
	print_token(t)
	return t

def t_HASH(t):
	r'\#'
	print_token(t)
	return t

# We preserve newlines to aid in error recovery. We completely ignore them
# under normal circumstances.
def t_NEWLINE(t):
	r'\n+'
	t.lexer.lineno += len(t.value)
	return t

def t_error(t):
	error("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

def p_file(p):
	'''file : lines'''
	p[0] = ast.File(*p[1], **{'lineno':0})

def p_lines(p):
	'''lines : line
		| line NEWLINE lines'''
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[1] += p[3]
		p[0] = p[1]
	

def p_line(p):
	'''line : 
	        | comment 
	        | statementlist 
		| statementlist comment'''
	p[0] = flatlist(p)
		
def p_statementlist(p):
	'''statementlist : statement
	                 | statementlist SEMI statement'''
	p[0] = flatlist(p)

def p_statement(p):
	'''statement : label
	             | instruction
		     | label instruction
		     | macro'''
	p[0] = flatlist(p)

def p_instruction(p):
	'''instruction : noargs
		       | branch
		       | load
		       | store
		       | restore
		       | onereg
		       | mov
		       | set
		       | cmp
		       | format3
		       | oneint
		       | onestring
		       | stringlist
		       | intlist
		       | call
		       | floatlist
		       | dotcommon
		       | tworeg
		       | dotsection
		       | pushsection
		       | twoints
		       | anythinglist
		       | dottype
		       | threereg
		       | oneaddr
		       | regoptconst
		       | oneregoraddr
		       | oneortworeg'''
	if type(p[1]) == list:	# plist
		# Pull off the first argument of the plist and create an
		# instruction from it
		args = p[1][1:]
		kwargs = { 'lineno' : p.lineno(1) }
		p[0] = ast.GenericInstruction(*args, **kwargs)
	else:
		p[0] = p[1]

def p_noargs(p):
	'''noargs : NOARGS'''
	op = p[1]
	lineno = p.lineno(1)
	if op in section_declarations:
		name = op
		attribute = None
		p[0] = ast.SectionDeclaration(name, attribute, lineno=p.lineno(1))
	elif op == '.popsection':
		p[0] = ast.PopSection(lineno=lineno)
	else:
		p[0] = plist(p)

def p_ibranch(p):
	'''branch : BRANCH intexpr'''
	p[0] = ast.Branch(p[2], lineno=p.lineno(1))

def p_annulled_ibranch(p):
	'''branch : BRANCH COMMA A intexpr'''
	p[0] = ast.AnnulledBranch(p[4], lineno=p.lineno(1))

def p_load(p):
	'''load : LOAD address COMMA reg'''
	p[0] = plist(p)

def p_store(p):
	'''store : STORE reg COMMA address'''
	p[0] = plist(p)

def p_address(p):
	'''address : LBRACKET reg RBRACKET
	           | LBRACKET reg PLUS intexpr RBRACKET
	           | LBRACKET reg MINUS intexpr RBRACKET
	           | LBRACKET reg PLUS reg RBRACKET'''
	if len(p) == 4: # no offset
		p[0] = ast.Address(p[2], lineno=p.lineno(1))
	else:
		p[0] = ast.Address(p[2], p[3], p[4], lineno=p.lineno(1))

def p_restore(p):
	'''restore : RESTORE
	           | RESTORE reg COMMA reg COMMA reg
	           | RESTORE reg COMMA intexpr COMMA reg'''
	p[0] = plist(p)

def p_onereg(p):
	'''onereg : ONEREG reg'''
	p[0] = plist(p)

def p_mov(p):
	'''mov : MOV reg COMMA reg
	       | MOV intexpr COMMA reg'''
	p[0] = plist(p)

def p_set(p):
	'''set : SET intexpr COMMA reg'''
	p[0] = ast.Set(p[2], p[4], lineno=p.lineno(1))

def p_cmp(p):
	'''cmp : CMP reg COMMA reg
	       | CMP reg COMMA intexpr'''
	p[0] = plist(p)

def p_format3(p):
	'''format3 : FORMAT3 reg COMMA reg COMMA reg
	           | FORMAT3 reg COMMA intexpr COMMA reg'''
	if p[1] == 'save':
		p[0] = ast.Save(p[2], p[4], p[6], lineno=p.lineno(1))
	else:
		p[0] = plist(p)

def p_oneint(p):
	'''oneint : ONEINT intexpr'''
	p[0] = plist(p)

def p_onestring(p):
	'''onestring : ONESTRING string'''
	p[0] = plist(p)

def p_stringlist(p):
	'''stringlist : STRINGLIST stringlistarg'''
	p[0] = plist(p[0:2] + p[2])

def p_stringlistarg(p):
	'''stringlistarg : string
	                 | string COMMA stringlistarg'''
	if len(p) == 2:
		p[0] = [p[1]]
	else:
		p[0] = [p[1]] + p[3]

def p_intlist(p):
	'''intlist : INTLIST intlistarg'''
	p[0] = plist(p[0:2] + p[2])

def p_intlistarg(p):
	'''intlistarg : intexpr
	              | intexpr COMMA intlistarg'''
	if len(p) == 2:
		p[0] = [p[1]]
	else:
		p[0] = [p[1]] + p[3]

def p_floatlist(p):
	'''floatlist : FLOATLIST floatlistarg'''
	p[0] = plist(p[0:2] + p[2])

def p_floatlistarg(p):
	'''floatlistarg : float
	                | float COMMA floatlistarg'''
	if len(p) == 2:
		p[0] = [p[1]]
	else:
		p[0] = [p[1]] + p[3]

def p_dotcommon(p):
	'''dotcommon : DOTCOMMON intexpr COMMA intexpr
	             | DOTCOMMON intexpr COMMA intexpr COMMA string
	             | DOTCOMMON intexpr COMMA intexpr COMMA string COMMA intexpr'''
	p[0] = plist(p)

def p_tworeg(p):
	'''tworeg : TWOREG reg COMMA reg'''
	p[0] = plist(p)

def p_call(p):
	'''call : CALL intexpr
	        | CALL intexpr COMMA intexpr'''
	p[0] = plist(p)

def p_dotsection(p):
	'''dotsection : DOTSECTION string
	              | DOTSECTION string COMMA attributelist'''
	name = p[2].getValue()
	attributes = None
	if len(p) == 5:
		attributes = p[4]
	p[0] = ast.SectionDeclaration(name, attributes, lineno=p.lineno(1))

def p_pushsection(p):
	'''pushsection : PUSHSECTION string
	              | PUSHSECTION string COMMA attributelist'''
	name = p[2]
	attributes = None
	if len(p) == 5:
		attributes = p[4]
	p[0] = ast.PushSection(name, attributes, lineno=p.lineno(1))

def p_attribute(p):
	'''attribute : HASH ATTRNAME'''
	p[0] = p[2]

def p_attributelist(p):
	'''attributelist : attribute
	                 | attributelist COMMA attribute'''
        if len(p) == 2:
		p[0] = [p[1]]
	else:
		p[0] = p[1] + [p[3]]
	#p[0] = plist(p)

def p_twoints(p):
	'''twoints : TWOINTS intexpr COMMA intexpr'''
	p[0] = plist(p)

def p_anythinglist(p):
	'''anythinglist : ANYTHINGLIST anythinglistarg'''
	p[0] = plist(p)

# There's no CHAR in here because it causes reduce/reduce conflicts. It's only
# used for stabs entries, anyway.
def p_anythinglistarg(p):
	'''anythinglistarg : intexpr
	                   | string
			   | float
			   | reg
	                   | intexpr COMMA anythinglistarg
	                   | string COMMA anythinglistarg
	                   | float COMMA anythinglistarg
	                   | reg COMMA anythinglistarg'''
	p[0] = plist(p)

def p_dottype(p):
	'''dottype : DOTTYPE intexpr COMMA type'''
	p[0] = plist(p)

def p_type(p):
	'''type : HASH TYPENAME'''
	p[0] = ast.Type(p[2], lineno=p.lineno(1))

def p_threereg(p):
	'''threereg : THREEREG reg COMMA reg COMMA reg'''
	p[0] = plist(p)

def p_oneaddr(p):
	'''oneaddr : ONEADDR address'''
	p[0] = plist(p)

def p_regoptconst(p):
	'''regoptconst : REGOPTCONST reg
	               | REGOPTCONST intexpr COMMA reg'''
	p[0] = plist(p)

def p_oneregoraddr(p):
	'''oneregoraddr : ONEREGORADDR reg
	                | ONEREGORADDR address'''
	p[0] = plist(p)

def p_oneortworeg(p):
	'''oneortworeg : ONEORTWOREG reg
	               | ONEORTWOREG reg COMMA reg'''
	p[0] = plist(p)

def p_label(p):
	'''label : id COLON'''
	p[0] = ast.LabelDeclaration(p[1], lineno=p.lineno(1))

def p_macro(p):
	'''macro : id EQUALS intexpr
	         | id EQUALS string'''
	p[0] = ast.MacroDeclaration(p[1], p[3], lineno=p.lineno(1))

def p_intexpr_int(p):
	'''intexpr : INT'''
	p[0] = ast.Integer(p[1], lineno=p.lineno(1))

def p_intexpr_char(p):
	'''intexpr : CHAR'''
	# Yeah, I know this is cheating.
	p[0] = ast.Char(ord(eval(p[1])), lineno=p.lineno(1))

def p_intexpr_id(p):
	'''intexpr : id'''
	p[0] = p[1]

def p_intexpr_parens(p):
	'''intexpr : LPAREN intexpr RPAREN'''
	p[0] = p[2]

def p_intexpr_binary_ops(p):
	'''intexpr : intexpr PLUS intexpr
	           | intexpr MINUS intexpr
	           | intexpr MUL intexpr
	           | intexpr DIV intexpr
	           | intexpr MOD intexpr
	           | intexpr XOR intexpr
	           | intexpr LSHIFT intexpr
	           | intexpr RSHIFT intexpr
	           | intexpr AND intexpr
	           | intexpr OR intexpr'''
	p[0] = ast.BinaryExpression.from_str(p[2], p[1], p[3], lineno=p.lineno(2))

def p_intexpr_unary_ops(p):
	'''intexpr : NOT intexpr
		   | MINUS intexpr
		   | LO intexpr
		   | HI intexpr
		   | UNARYNOP intexpr'''
	p[0] = ast.UnaryExpression.from_str(p[1], p[2], lineno=p.lineno(1))

def p_reg(p):
	'''reg : REG'''
	p[0] = ast.Reg(p[1], lineno=p.lineno(1))

def p_float(p):
	'''float : FLOAT'''
	p[0] = ast.Float(p[1], lineno=p.lineno(1))

def p_string(p):
	'''string : STRING'''
	p[0] = ast.String(p[1], lineno=p.lineno(1))

def p_id(p):
	'''id : ID
	      | A
	      | BRANCH
	      | NOARGS
	      | RESTORE
	      | ONEREG
	      | LOAD
	      | STORE
	      | MOV
	      | SET
	      | CMP
	      | FORMAT3
	      | ONEINT
	      | ONESTRING
	      | STRINGLIST
	      | INTLIST
	      | CALL
	      | FLOATLIST
	      | DOTCOMMON
	      | TWOREG
	      | ATTRNAME
	      | DOTSECTION
	      | TWOINTS
	      | ANYTHINGLIST
	      | TYPENAME
	      | DOTTYPE
	      | THREEREG
	      | ONEADDR
	      | REGOPTCONST
	      | ONEREGORADDR
	      | ONEORTWOREG'''
	p[0] = ast.Id(p[1], lineno=p.lineno(1))

def p_comment(p):
	'''comment : LINECOMMENT
	           | BLOCKCOMMENT'''
	p[0] = ast.Comment(p[1], lineno=p.lineno(1))

def p_error(token):
	if token is None:
		val = "<NO TOKEN>";
	else:
		val = "'%s' (%s) on line %d" % (token.value, token.type, token.lineno)
	error("Syntax error at token %s." % (val))
	
	raise ParseError()
