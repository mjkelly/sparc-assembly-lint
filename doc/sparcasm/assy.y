%{
/*
$Log: assy.y,v $
Revision 1.9  1997/03/14 05:42:02  bediger
improve ability to handle floating point constants, add a hack to
handle st2 and ld2 synthetics, reflect changes to struct expr_node.

Revision 1.8  1997/02/27 07:43:24  bediger
support for SunOS-style local labels (single digits)

Revision 1.7  1997/02/14 06:22:56  bediger
add a hack to one production to make a distinction between
'clr  %rd' and 'clr [%rd]': distinguish on basis of invalid ASI.
Many changes to account for allowing general arithmetic expressions
as immediates in '%r + imm' type instructions.  Remove some dead
code.

Revision 1.6  1997/01/15 01:27:42  bediger
reflect the "directives as part of grammar" changes

Revision 1.5  1996/12/29 01:14:48  bediger
added support for cmd-line specification of symbol table debugging

Revision 1.4  1996/12/19 07:00:30  bediger
modified a production from "s2 -> identifier_expression TK_COLON assy_stmnt"
to "s2 -> identifier_expression TK_COLON".  Simplified the semantic
action of the production.  Seems to still work.

Revision 1.3  1996/12/17 06:40:28  bediger
Add many productions to do operator precedence in the C style
to accomodate the unary and binary operators that SunOS assembler uses.

Revision 1.2  1996/12/16 06:45:54  bediger
change a production slightly

Revision 1.1  1996/12/14 19:59:54  bediger
Initial revision

*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#include <a.out.h>
#include <nlist.h>
#include <string.h>

#include <assy.h>
#include <assembler.h>  /* for asm_set_size() prototype */
#include <io.h>
#include <symtable.h>
#include <digit_label.h>
#include <expr.h>       /* for struct expr_node parse trees */

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

#define ASSEMBLE(p) do{if((p)&&((p)->mnemonic)&&(p)->mnemonic->asm_fn)((p)->mnemonic->asm_fn)(p);}while(0)

extern int lineno;   /* input line number */
extern int pass;     /* pass 1 or pass 2 */

int yywrap(void);
void yyerror(char *s1);

static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/assy.y,v 1.9 1997/03/14 05:42:02 bediger Exp bediger $";
%}

%token INTEGER_CONSTANT CHARACTER_CONSTANT FLOATING_CONSTANT CHARACTER_CONSTANT
%token STRING_CONSTANT IDENTIFIER DIRECTIVE
%token MNEMONIC REGISTER_NAME

%token TK_HI TK_LO

%token TK_LBRACK TK_RBRACK
%token TK_LPAREN TK_RPAREN
%token TK_COLON TK_COMMA TK_EQUALS TK_EOSTMNT

%token TK_PLUS TK_MINUS
%token TK_STAR TK_SLASH TK_TILDE TK_MODULO
%token TK_BIT_OR TK_BIT_AND TK_BIT_XOR TK_LEFT_SHIFT TK_RIGHT_SHIFT

%union {
	enum ExprNodeT          unary_op;
	unsigned int            val;
	double                  dbl_val;
	char                   *string;
	struct register_rep    *reg;
	struct asm_stmnt       *stmnt;
	struct expr_node       *expr;
	struct mnm             *mnemonic;
	struct expr_list       *expr_list;
	struct bzx             *directive;
}

%%

listing
	: s2
	| listing s2
	;

s2
	: assy_stmnt
		{
			if (NULL != $1.stmnt)
			{
				if (1 == pass)
				{
					extern struct mnm *set_dummy, *st2_dummy, *ld2_dummy;

					if ($1.stmnt->mnemonic == set_dummy)
						CURROFFSET += asm_set_size($1.stmnt);
					else if ($1.stmnt->mnemonic == ld2_dummy || $1.stmnt->mnemonic == st2_dummy)
						CURROFFSET += 8;
					else
						CURROFFSET += 4;

				} else
					ASSEMBLE($1.stmnt);

				free_stmnt($1.stmnt);
			}
		}
	| identifier_expression TK_COLON
		{
			if (NULL != $1.expr)
			{
				struct nlist *nl;

				if (1 == pass)
				{
					switch ($1.expr->kind)
					{
					case ExprCon:
					case ExprSym:
						nl = assemble_label($1.expr);

						nl->n_value = CURROFFSET;
						nl->n_type |= ((TEXT_SEG == current_segment) ? N_TEXT : N_DATA);

						if (sym_debug)
						{
							printf("pass 1, assembled label \"%s\" at 0x%x, type %s, line %d\n",
								nl->n_un.n_name,
								nl->n_value,
								print_n_type(nl->n_type), lineno);
						}
						break;
					default:
						internal_problem(__FILE__, __LINE__, "Bad expression tree: ");
						print_expr(stderr, $1.expr);  fputc('\n', stderr);
					}

				} else {
					switch ($1.expr->kind)
					{
					case ExprCon:
						if (NULL == local_symbol_named($1.expr->u.val))
							internal_problem(__FILE__, __LINE__,
								"2nd Pass, no symbol for local label \"%d\"\n", $1.expr->u.val);
						passed_local($1.expr->u.val);
						break;
					case ExprSym:
						if (NULL == symbol_named($1.expr->u.id))
							internal_problem(__FILE__, __LINE__,
								"2nd Pass, no symbol for label named \"%s\"\n", $1.expr->u.id);
						break;
					default:
						internal_problem(__FILE__, __LINE__, "Bad expression tree: ");
						print_expr(stderr, $1.expr);  fputc('\n', stderr);
					}
				}

				free_expr($1.expr);
			}
		}
	;

assy_stmnt
	: mnemonic identifier_expression TK_EOSTMNT 
		{ 
			$$.stmnt = construct_stmnt($1.mnemonic, $2.expr, NULL, NULL, NULL);
			if (!strcmp($1.mnemonic->op_mnm, "clr"))
				$$.stmnt->asi = 0;  /* to distinguish beteween 'clr %rd' and 'clr [%rd]', neither has ASI */
		}
	| mnemonic identifier_expression TK_COMMA identifier_expression TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $2.expr, NULL, $4.expr, NULL); }
	| mnemonic identifier_expression TK_COMMA identifier_expression TK_COMMA identifier_expression TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $2.expr, $4.expr, $6.expr, NULL); }
	| mnemonic identifier_expression TK_COMMA TK_LBRACK identifier_expression TK_RBRACK TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $5.expr, NULL, $2.expr, NULL); }
	| mnemonic identifier_expression TK_COMMA TK_LBRACK identifier_expression TK_RBRACK identifier_expression TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $5.expr, NULL, $2.expr, $7.expr); }
	| mnemonic TK_LBRACK identifier_expression TK_RBRACK TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $3.expr, NULL, NULL, NULL); }
	| mnemonic TK_LBRACK identifier_expression TK_RBRACK TK_COMMA identifier_expression TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $3.expr, NULL, $6.expr, NULL); }
	| mnemonic TK_LBRACK identifier_expression TK_RBRACK identifier_expression TK_COMMA identifier_expression TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, $3.expr, NULL, $7.expr, $5.expr); }
	| mnemonic TK_EOSTMNT 
		{ $$.stmnt = construct_stmnt($1.mnemonic, NULL, NULL, NULL, NULL); }
	| identifier_expression TK_EQUALS identifier_expression TK_EOSTMNT
		{ 
			symbol_equals_expr($1.expr, $3.expr);
			free_expr($1.expr);
			free_expr($3.expr);
			$$.stmnt = NULL;
		}
	| expr_list TK_EOSTMNT
		{
			assert(NULL != $1.expr_list);

			if (1 == pass)
			{
				if ($1.expr_list->directive->p1sz >= 0)
					CURROFFSET += $1.expr_list->directive->p1sz;
				else if ($1.expr_list->directive->size_fn)
					CURROFFSET += ($1.expr_list->directive->size_fn)(
										$1.expr_list->directive->directive,
										$1.expr_list->head);
				/* else, ignore unimplemented directives */

			} else if ($1.expr_list->directive->fp) {

				($1.expr_list->directive->fp)(
					$1.expr_list->directive->directive, 
					$1.expr_list->head);
			}

			free_expr_list($1.expr_list->head);
			free($1.expr_list);

			$$.stmnt = NULL;
		}
	| TK_EOSTMNT { $$.stmnt = NULL; }
	;

expr_list
	: DIRECTIVE
		{
			STRUCT_ALLOC($$.expr_list, struct expr_list);
			$$.expr_list->directive = $1.directive;
			$$.expr_list->head = $$.expr_list->tail = NULL;
		}
	| DIRECTIVE identifier_expression
		{
			STRUCT_ALLOC($$.expr_list, struct expr_list);
			$$.expr_list->directive = $1.directive;

			STRUCT_ALLOC($$.expr_list->tail, struct expr_list_node);
			$$.expr_list->head = $$.expr_list->tail;
			$$.expr_list->tail->next = NULL;
			$$.expr_list->tail->expression = $2.expr;
		}
	| expr_list TK_COMMA identifier_expression
		{
			assert($1.expr_list->head);

			STRUCT_ALLOC($1.expr_list->tail->next, struct expr_list_node);

			$1.expr_list->tail = $1.expr_list->tail->next;
			$1.expr_list->tail->expression = $3.expr;
			$1.expr_list->tail->next = NULL;

			$$.expr_list = $1.expr_list;
		}
	;

mnemonic
	: MNEMONIC
		{
			$$.mnemonic = $1.mnemonic;
			$$.mnemonic->anul_bit = 0;
		}
	| MNEMONIC TK_COMMA IDENTIFIER
		{
			$$.mnemonic = $1.mnemonic;
			$$.mnemonic->anul_bit = 1;

			/* after the fact data verification */
			if (strcmp($3.string, "a"))
				input_problem("annul-bit notation production: mnemonic is \"%s\", annotation is \"%s\"\n",
					$$.mnemonic->op_mnm, $3.string);

			free($3.string);
		}
	;

unary_operator
	: TK_HI       { $$.unary_op = ExprHiBit;}
	| TK_LO       { $$.unary_op = ExprLoBit;}
	| TK_PLUS     { $$.unary_op = ExprAdd;}
	| TK_MINUS    { $$.unary_op = ExprSub;}
	| TK_TILDE    { $$.unary_op = ExprComp;}
	;

identifier_expression
	:                                 XOR_expression { $$.expr = $1.expr;}
	| identifier_expression TK_BIT_OR XOR_expression
		{ $$.expr = construct_expr(ExprBitOr, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	;

XOR_expression
	:                           AND_expression  { $$.expr = $1.expr;}
	| XOR_expression TK_BIT_XOR AND_expression
		{ $$.expr = construct_expr(ExprBitXor, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	;

AND_expression
	:                           shift_expression  { $$.expr = $1.expr;}
	| AND_expression TK_BIT_AND shift_expression
		{ $$.expr = construct_expr(ExprBitAnd, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	;

shift_expression
	:                                 additive_expr { $$.expr = $1.expr; }
	| shift_expression TK_LEFT_SHIFT  additive_expr
		{ $$.expr = construct_expr(ExprLShift, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	| shift_expression TK_RIGHT_SHIFT additive_expr
		{ $$.expr = construct_expr(ExprRShift, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
    ;
	
additive_expr
	:                        multiplicative_expr  { $$.expr = $1.expr; }
	| additive_expr TK_PLUS  multiplicative_expr
		{ $$.expr = construct_expr(ExprAdd, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	| additive_expr TK_MINUS multiplicative_expr
		{ $$.expr = construct_expr(ExprSub, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	;

multiplicative_expr
	:                               value  { $$.expr = $1.expr; }
	| multiplicative_expr TK_STAR   value
		{ $$.expr = construct_expr(ExprMul, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	| multiplicative_expr TK_SLASH  value
		{ $$.expr = construct_expr(ExprDiv, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	| multiplicative_expr TK_MODULO value
		{ $$.expr = construct_expr(ExprMod, $1.expr, $3.expr, NULL, 0, 0.0, NULL); }
	;


value
	: INTEGER_CONSTANT
		{ $$.expr = construct_expr(ExprCon, NULL,    NULL,    NULL,     $1.val, 0.0, NULL); }
	| STRING_CONSTANT
		{ $$.expr = construct_expr(ExprStr, NULL,    NULL,    $1.string, 0,     0.0, NULL); }
	| IDENTIFIER
		{ $$.expr = construct_expr(ExprSym, NULL,    NULL,    $1.string, 0,     0.0, NULL); }
	| unary_operator value
		{
			switch ($1.unary_op)
			{
			case ExprHiBit: case ExprLoBit: case ExprComp:
				$$.expr = construct_expr($1.unary_op, NULL, $2.expr, NULL, 0, 0.0, NULL);
				break;
			case ExprSub:
				$$.expr = construct_expr(
					$1.unary_op,
					construct_expr(ExprCon, NULL, NULL, NULL, 0, 0.0, NULL),
					$2.expr,
					NULL,
					0, 0.0, NULL);
				break;
			case ExprAdd:
				$$.expr = $2.expr;
				break;
			default:
				input_problem("invalid unary operator: %s\n", print_expr_kind($1.unary_op));
				break;
			}
		}
	| TK_LPAREN identifier_expression TK_RPAREN
		{ $$.expr = $2.expr; }
	| FLOATING_CONSTANT
		{ $$.expr = construct_expr(ExprFlt, NULL,    NULL,    NULL, 0, $1.dbl_val, NULL); }
	| REGISTER_NAME
		{ $$.expr = construct_expr(ExprReg, NULL,    NULL,    NULL, 0, 0.0,        $1.reg); }
	;

%%

int
yywrap(void)
{
    return 1;
}

void
yyerror(char *s1)
{
    extern int lineno;
	extern char *working_input_file;

    fprintf(stderr, "%s:%d:parse error: %s\n", working_input_file, lineno, s1);
}
