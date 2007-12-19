/*
$Log: expr.c,v $
Revision 1.15  1997/03/21 07:42:54  bediger
remove the part where previously unreferenced symbols get marked N_EXT.
This now gets done just before symbol table gets written out.

Revision 1.14  1997/03/14 05:36:29  bediger
make code reflect changes to struct expr_node (minimize size of that struct)
make handling of floating point stuff more complete.

Revision 1.13  1997/03/10 01:07:24  bediger
fix a bug relating to calculation of "value" and relocation information
of symbols in algebraic calcs.  "symbol+expression" did stuff wrong.
Test cases didn't expose this.

Revision 1.12  1997/03/09 21:44:19  bediger
some changes to handle N_ABS symbols

Revision 1.11  1997/02/27 07:42:10  bediger
ditch some commented-out code

Revision 1.10  1997/02/14 06:29:05  bediger
become a bit more parsimonious when allocating structs and stuff.
this derives from trying to track down a memory leak.  Fix a few
bugs that cause previous allocations to be smashed and forgotten.

Revision 1.9  1997/02/13 07:29:31  bediger
code cleanup: remove a few allocations and deletions that could
be coalesced into previous allocaions.

Revision 1.8  1997/02/13 07:03:34  bediger
make print_expr() more robust; remove unused function expr_size();
fix a bug relating to rearranging 'immediate + register' expressions
to 'register + immediate'; make expression evaluation more robust
in face of semantic errors in input.

Revision 1.7  1997/02/04 04:00:12  bediger
support for changed assembly statement representation

Revision 1.6  1997/01/15 01:29:37  bediger
make it do "symbol = expression" stuff

Revision 1.5  1997/01/05 08:53:48  bediger
cleanup so that calculation of r_addend "looks right"

Revision 1.4  1996/12/29 01:18:41  bediger
broke up a huge function into many small ones, driven by a switch in
the replacement for the old, huge function

Revision 1.3  1996/12/28 17:44:51  bediger
check in a buggy version to get at an older one

Revision 1.2  1996/12/17 06:32:10  bediger
addition of a whole bunch of stuff to cover all the possible binary
and unary operators that supporting SunOS assembler syntax requires.

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/expr.c,v 1.15 1997/03/21 07:42:54 bediger Exp bediger $";
 
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <a.out.h>
#include <string.h>

#include <assy.h>
#include <io.h>
#include <expr.h>
#include <symtable.h>  /* symbol_named() prototype */
#include <shortcut_alloc.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

typedef enum ExprType (*NodeEvalFunction)(
	struct expr_node *, struct nlist **, struct relocation_info **, int **, struct register_address *);

enum ExprType real_eval(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);

enum ExprType expr_arith_op(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);
enum ExprType expr_sym(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);
enum ExprType expr_bit(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);
enum ExprType expr_comp(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);
enum ExprType expr_con(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);
enum ExprType expr_reg(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra);

ALLOC_DECL(expr_alloc, 256);
ALLOC_DECL(int_alloc, 32);

extern struct mem_stack register_alloc;

#define EXTERN_SYMBOL(sym) (N_UNDF==(((sym)->n_type&N_TYPE)&(~N_EXT)))

#define STRING(a) #a
#define STRINGIFY(a) STRING(a)

#define TABLE_ENTRY(x) {x, #x}

struct {enum ExprNodeT op; char *op_name;} op_name_ary[] = {
	TABLE_ENTRY(ExprAdd),
	TABLE_ENTRY(ExprSub),
	TABLE_ENTRY(ExprMul),
	TABLE_ENTRY(ExprDiv),
	TABLE_ENTRY(ExprSym),
	TABLE_ENTRY(ExprHiBit),
	TABLE_ENTRY(ExprLoBit),
	TABLE_ENTRY(ExprCon),
	TABLE_ENTRY(ExprComp),
	TABLE_ENTRY(ExprLShift),
	TABLE_ENTRY(ExprRShift),
	TABLE_ENTRY(ExprBitOr),
	TABLE_ENTRY(ExprBitXor),
	TABLE_ENTRY(ExprBitAnd),
	TABLE_ENTRY(ExprMod),
};

char *
print_expr_kind(enum ExprNodeT op)
{
	char *r = NULL;
	int i;

	for (i = 0; !r && i < sizeof(op_name_ary)/sizeof(op_name_ary[0]); ++i)
		if (op == op_name_ary[i].op)
			r = op_name_ary[i].op_name;

	return r;
}

struct {enum ExprType ty; char *ty_name;} ty_name_ary[] = {
	TABLE_ENTRY(VALUE),
	TABLE_ENTRY(SYMBOL),
	TABLE_ENTRY(REGISTER),
};

char *
print_expr_ty(enum ExprType ty)
{
	char *r = NULL;
	int i;

	for (i = 0; !r && i < sizeof(ty_name_ary)/sizeof(ty_name_ary[0]); ++i)
		if (ty == ty_name_ary[i].ty)
			r = ty_name_ary[i].ty_name;

	return r;
}

struct expr_node *
construct_expr(
    enum ExprNodeT op,
    struct expr_node *left,
    struct expr_node *right,
    char *id,
	int   val,
	double fltval,
	struct register_rep *reg
)
{
	struct expr_node *r;

	/* do any obvious arithmetic right on the spot */

	if (left && ExprCon == left->kind  && right && ExprCon == right->kind)
	{
		r = left;

		r->kind = ExprCon;

		switch (op)
		{
		case ExprAdd:    r->u.val +=  right->u.val; break;
		case ExprSub:    r->u.val -=  right->u.val; break;
		case ExprMul:    r->u.val *=  right->u.val; break;
		case ExprDiv:    r->u.val /=  right->u.val; break;
		case ExprMod:    r->u.val %=  right->u.val; break;
		case ExprLShift: r->u.val <<= right->u.val; break;
		case ExprRShift: r->u.val >>= right->u.val; break;
		case ExprBitOr:  r->u.val |=  right->u.val; break;
		case ExprBitAnd: r->u.val &=  right->u.val; break;
		case ExprBitXor: r->u.val ^=  right->u.val; break;

		default:
			/* op is Not Right. */
			internal_problem(__FILE__, __LINE__,
				"Constructing expression node, op %s not applicable\n",
				print_expr_kind(op));
			assert(0);
			break;
		}

		free_expr(right);

	} else if ((ExprLoBit == op || ExprHiBit == op || ExprComp == op) && right && ExprCon == right->kind) {

		r = right;

		switch (op)
		{
		case ExprLoBit:  r->u.val &= 0x3ff;                     break;
		case ExprHiBit:  r->u.val =  (r->u.val >> 10) & 0x3fffff; break;
		case ExprComp:   r->u.val = ~(r->u.val);                  break;
		default:
			/* op is Not Right. */
			internal_problem(__FILE__, __LINE__,
				"Constructing expression node, unary op %s not applicable\n",
				print_expr_kind(op));
			assert(0);
			break;
		}

	} else {

		/* defer anything other than obvious arithmetic */

		ASM_ALLOC(r, expr_alloc, struct expr_node);

		r->kind = op;
		r->lft = left;
		r->rgt = right;

		/* fill in the appropriate ones */
		switch (op)
		{
		case ExprStr:
		case ExprSym: r->u.id     = id;     break;
		case ExprCon: r->u.val    = val;    break;
		case ExprReg: r->u.reg    = reg;    break;
		case ExprFlt: r->u.fltval = fltval; break;
		default:
			/* what to do here?  Check for a left and right? */
			break;
		}
	}

	return r;
}

void
free_expr(struct expr_node *expr)
{
	assert(NULL != expr);

	if (NULL != expr->lft) free_expr(expr->lft);
	if (NULL != expr->rgt) free_expr(expr->rgt);
	switch (expr->kind)
	{
	case ExprStr: case ExprSym:
		if (NULL != expr->u.id)  free(expr->u.id);
		break;
	case ExprReg:
		if (NULL != expr->u.reg) ASM_DEALLOC(expr->u.reg, register_alloc);
		break;
	default:
		break;
	}

	ASM_DEALLOC(expr, expr_alloc);
}

/* printing an ExprCon constant is a hard one.  It might be a bitpattern,
 * it might be a float, it might be a signed or unsigned int. */
void
print_expr(FILE *stream, struct expr_node *expr)
{
	/* don't want to assert in this ... */
	if (NULL == expr)
		fputs(" NULL expression", stream);

	if (expr->lft) print_expr(stream, expr->lft);

	switch (expr->kind)
	{
	case ExprAdd: fputs(" +", stream); break;
	case ExprSub: fputs(" -", stream); break;
	case ExprMul: fputs(" *", stream); break;
	case ExprDiv: fputs(" /", stream); break;
	case ExprMod: fputs(" %", stream); break;
	case ExprComp: fputs(" ~", stream); break;

	case ExprLShift: fputs(" <<", stream); break;
	case ExprRShift: fputs(" >>", stream); break;

	case ExprBitOr:  fputs(" |", stream); break;
	case ExprBitAnd: fputs(" &", stream); break;
	case ExprBitXor: fputs(" ^", stream); break;

	case ExprLoBit: fprintf(stream, " %%lo("); break;
	case ExprHiBit: fprintf(stream, " %%hi("); break;

	case ExprSym: fprintf(stream, " \"%s\"", expr->u.id); break;
	case ExprCon: fprintf(stream, " %d", expr->u.val); break;

	case ExprReg:
		if (NULL == expr->u.reg)
			fputs(" NULL register rep", stream);
		else switch (expr->u.reg->type)
		{
		case REGULAR: fprintf(stream, "%%r%d", expr->u.reg->regno); break;
		case FP:      fprintf(stream, "%%f%d", expr->u.reg->regno); break;
		case COPROC:  fprintf(stream, "%%c%d", expr->u.reg->regno); break;
		case Y:       fprintf(stream, " %%y"); break;
		case ASR:     fprintf(stream, " %%asr%d", expr->u.reg->regno); break;
		case PSR:     fprintf(stream, " %%psr"); break;
		case WIM:     fprintf(stream, " %%wim"); break;
		case TBR:     fprintf(stream, " %%tbr"); break;
		case FSR:     fprintf(stream, " %%fsr"); break;
		case CSR:     fprintf(stream, " %%csr"); break;
		case FQ:      fprintf(stream, " %%fq"); break;
		default:      fprintf(stream, " bad type: %d", expr->u.reg->type); break;
		}
		break;

	case ExprStr: 
		if (NULL == expr->u.id)
			fputs(" NULL string", stream);
		else
			fprintf(stream, " \"%s\"", expr->u.id);
		break;

	case ExprFlt:
		fprintf(stream, " %f", expr->u.fltval); break;
	}

	if (expr->rgt) print_expr(stream, expr->rgt);

	if (ExprLoBit == expr->kind || ExprHiBit == expr->kind) putc(')', stream);
}

enum ExprType
expr_to_imm(
	struct expr_node *expr,
	struct nlist **nl,
	struct relocation_info **reloc,
	int **value,
	struct register_address *regaddr
)
{
	assert(NULL != expr);
	assert(NULL != nl);
	assert(NULL != reloc);
	assert(NULL != value);
	assert(NULL != regaddr);

	*nl    = NULL;
	*reloc = NULL;
	*value = NULL;
	regaddr->reg1 = regaddr->reg2 = NULL;

	return real_eval(expr, nl, reloc, value, regaddr);
}

/* evaluates the struct expr_node binary tree - does not free it */
enum ExprType
real_eval(
	struct expr_node *expr,
	struct nlist **nl,
	struct relocation_info **reloc,
	int **value,
	struct register_address *regaddr
)
{
	NodeEvalFunction fptr;
	
	assert(NULL != expr);

	switch (expr->kind)
	{
	case ExprAdd: case ExprSub: case ExprMul: case ExprDiv:
	case ExprMod: case ExprLShift: case ExprRShift: case ExprBitOr:
	case ExprBitXor: case ExprBitAnd:
		fptr = expr_arith_op;
		break;

	case ExprSym:
		fptr = expr_sym;
		break;

	case ExprLoBit: case ExprHiBit:
		fptr = expr_bit;
		break;

	case ExprComp:
		fptr = expr_comp;
		break;
		
	case ExprCon:
		fptr = expr_con;
		break;

	case ExprReg:
		fptr = expr_reg;
		break;

	default:
		internal_problem(__FILE__, __LINE__, "Float or string in parse tree\n");
		break;
	}

	return (*fptr)(expr, nl, reloc, value, regaddr);
}

enum ExprType
expr_arith_op(
	struct expr_node *expr,
	struct nlist **nl,
	struct relocation_info **reloc,
	int **value,
	struct register_address *ra
)
{
	enum ExprType typeL, typeR, ret;
	int *valueL = NULL, *valueR = NULL;
	struct nlist *nlR, *nlL;
	struct relocation_info *relocR, *relocL;
	struct register_address raL, raR;

	if (expr->lft)
		typeL = expr_to_imm(expr->lft, &nlL, &relocL, &valueL, &raL);
	if (expr->rgt)
		typeR = expr_to_imm(expr->rgt, &nlR, &relocR, &valueR, &raR);

	if (!expr->lft || !expr->rgt)
	{
		internal_problem(__FILE__, __LINE__,
			"Node of binary op %s, NULL subtree: ", print_expr_kind(expr->kind));
		print_expr(stderr, expr);
		putc('\n', stderr);
	}

	if (VALUE == typeL && VALUE == typeR)
	{
		ret = VALUE;
		*value = valueL;
		valueL = NULL;

		switch (expr->kind)
		{
		case ExprAdd:    **value += *valueR;  break;
		case ExprSub:    **value -= *valueR;  break;
		case ExprMul:    **value *= *valueR;  break;
		case ExprDiv:    **value /= *valueR;  break;
		case ExprMod:    **value %= *valueR;  break;
		case ExprLShift: **value <<= *valueR; break;
		case ExprRShift: **value >>= *valueR; break;
		case ExprBitOr:  **value |= *valueR;  break;
		case ExprBitAnd: **value &= *valueR;  break;
		case ExprBitXor: **value ^= *valueR;  break;

		default:
			internal_problem(__FILE__, __LINE__,
				"children are %s and %s, op is %s\n",
				print_expr_ty(typeL), print_expr_ty(typeR),
				print_expr_kind(expr->kind));
			assert(0);
			break;
		}

	} else if (SYMBOL == typeL && VALUE == typeR) {

		ret = SYMBOL;

		*reloc = relocL;
		*nl = nlL;

		if (valueL)
			*value = valueL;

		switch (expr->kind)
		{
		case ExprAdd: 
			(*reloc)->r_addend += *valueR;
			if (!valueL)
			{
				*value = valueR;
				valueR = NULL;
			}
			break;
		case ExprSub:
			(*reloc)->r_addend -= *valueR;
			if (!valueL) 
			{
				*value = valueR;
				valueR = NULL;
			}
			break;
		default:
			assert(0);
			break;
		}

		valueL = NULL;

	} else if (VALUE == typeL && SYMBOL == typeR) {
		internal_problem(__FILE__, __LINE__,
				"goofy arithmetic, children are %s and %s, kind is %s\n",
				print_expr_ty(typeL), print_expr_ty(typeR),
				print_expr_kind(expr->kind));
		assert(0);
	} else if (REGISTER == typeL || REGISTER == typeR) {

		/* one or the other operand is a register representation */

		if ((VALUE == typeL || VALUE == typeR) || (SYMBOL == typeL || SYMBOL == typeR))
		{
			/* cannonicalize: register on left, value on right */
			if (VALUE == typeL || SYMBOL == typeL)
			{
				int *tmp_val;
				struct register_address tmp_ra;
				struct nlist *tmp_nl;
				struct relocation_info *tmp_rel;

				if (ExprSub == expr->kind)
					input_problem("%s on left of minus sign\n", print_expr_ty(typeL));

				tmp_val = valueL;
				valueL  = valueR;
				valueR  = tmp_val;

				tmp_ra = raL;
				raL = raR;
				raR = tmp_ra;

				tmp_rel = relocL;
				relocL = relocR;
				relocR = tmp_rel;

				tmp_nl = nlL;
				nlL = nlR;
				nlR = tmp_nl;
			}

			ra->reg1 = raL.reg1;
			if (valueL)
			{
				*value = valueL;
				valueL = NULL;
			} else {
				ASM_ALLOC(*value, int_alloc, int);
				**value = 0;
			}

			switch (expr->kind)
			{
			case ExprAdd:    **value += *valueR; break;
			case ExprSub:    **value -= *valueR; break;
			case ExprMul:    **value *= *valueR; break;
			case ExprDiv:    **value /= *valueR; break;
			case ExprMod:    **value %= *valueR; break;
			case ExprLShift: **value <<= *valueR; break;
			case ExprRShift: **value >>= *valueR; break;
			case ExprBitOr:  **value |= *valueR;  break;
			case ExprBitAnd: **value &= *valueR;  break;
			case ExprBitXor: **value ^= *valueR;  break;
			default:
				internal_problem(__FILE__, __LINE__,
					"children are VALUE and VALUE, kind is %s\n",
					print_expr_kind(expr->kind));
			}
			*reloc = relocR;
			*nl    = nlR;
		} else if (REGISTER == typeL && REGISTER == typeR) {
			if (ExprAdd != expr->kind)
				internal_problem(__FILE__, __LINE__, "Weird register arithmetic operation: %s\n", print_expr_kind(expr->kind));
			ra->reg1 = raL.reg1;
			ra->reg2 = raR.reg1;
			if (NULL != raL.reg2 || NULL != raR.reg2)
				internal_problem(__FILE__, __LINE__, "Weird register arithmetic\n");
			*reloc = NULL;
			*nl    = NULL;
			*value = NULL;
		} else {
			/* there's no way this can happen */
			assert(0);
		}

		ret = REGISTER;
	} else {
		/* inobvious arithmetic */

		ret = SYMBOL;
		*reloc = NULL;
		*nl = NULL;

		if (!*value)
			ASM_ALLOC(*value, int_alloc, int);

		switch (expr->kind)
		{
		case ExprAdd: **value = nlL->n_value + nlR->n_value; break;
		case ExprSub: **value = nlL->n_value - nlR->n_value; break;
		case ExprMul: **value = nlL->n_value * nlR->n_value; break;
		case ExprDiv: **value = nlL->n_value / nlR->n_value; break;

		/* I don't think anything else makes sense: * and / are pushing it */

		default:
			internal_problem(__FILE__, __LINE__,
				"children are SYMBOL and SYMBOL, kind is %s\n",
				print_expr_kind(expr->kind));
			assert(0);
			break;
		}
	}

	if (valueL) ASM_DEALLOC(valueL, int_alloc);
	if (valueR) ASM_DEALLOC(valueR, int_alloc);

	return ret;
}

enum ExprType expr_sym(struct expr_node *expr, struct nlist **nl,
    struct relocation_info **reloc, int **value, struct register_address *ra)
{
	assert(ExprSym == expr->kind);

	/* check to make sure this is a leaf node */
	if (expr->lft || expr->rgt)
	{
		internal_problem(__FILE__, __LINE__,
			"Node of type ExprSym, non-NULL subtree: ");
		print_expr(stderr, expr);
		putc('\n', stderr);
	}

	*nl = symbol_named(expr->u.id);

	if (NULL == *nl)
	{
		*nl = assemble_label(expr);
		if (sym_debug)
			fprintf(stderr, "inferring externality, marking symbol named \"%s\" as N_EXT\n", expr->u.id);
	}

	if (N_ABS == (((*nl)->n_type&N_TYPE)&(~N_EXT)))
	{
		ASM_ALLOC(*value, int_alloc, int);
		**value = (*nl)->n_value;

		return VALUE;

	} else {
		STRUCT_ALLOC(*reloc, struct relocation_info);
		(*reloc)->r_address = CURROFFSET;
		(*reloc)->r_type    = RELOC_UNUSED3;
		(*reloc)->r_addend  = 0;

		ASM_ALLOC(*value, int_alloc, int);
		**value = (*nl)->n_value;

		return SYMBOL;
	}
}

enum ExprType expr_bit(struct expr_node *expr, struct nlist **nl,
    struct relocation_info **reloc, int **value, struct register_address *ra)
{
	enum ExprType typeR, ret;
	struct nlist *nlR;
	struct relocation_info *relocR;
	struct register_address raR;

	if (!expr->rgt)
	{
		internal_problem(__FILE__, __LINE__, "taking bitness of no args, doesn't make sense\n");
		ASM_ALLOC(*value, int_alloc, int);
		**value = 0;
		return VALUE;
	}

	/* a mistake, but not one we can't live with */
	if (expr->lft)
		internal_problem(__FILE__, __LINE__, "taking bitness of 2 args, doesn't make sense\n");

	typeR = expr_to_imm(expr->rgt, &nlR, &relocR, value, &raR);

	switch (typeR)
	{
	case VALUE:         /* take bitness of a VALUE */
		**value = (ExprLoBit == expr->kind) ? (**value & 0x3ff) : (**value >> 10);
		ret = VALUE;
		break;
		
	case SYMBOL:        /* set bitness of a relocation */
		*nl = nlR;
		if (!EXTERN_SYMBOL(*nl))
			**value = (ExprLoBit == expr->kind) ? (**value & 0x3ff) : (**value >> 10);
		else {
			if (!*value)
				ASM_ALLOC(*value, int_alloc, int);
			**value = 0;
		}
		*reloc = relocR;
		(*reloc)->r_type = (ExprLoBit == expr->kind)? RELOC_LO10 : RELOC_HI22;
		ret = SYMBOL;
		break;

	case REGISTER:
		input_problem("can't take bitness of a register\n");
		ret = REGISTER;
		ra->reg1 = raR.reg1;
		ra->reg2 = raR.reg2;
		break;
	}

	return ret;
}

enum ExprType expr_comp(struct expr_node *expr, struct nlist **nl,
    struct relocation_info **reloc, int **value, struct register_address *ra)
{
	enum ExprType           typeR, ret;
	struct nlist           *nlR;
	struct relocation_info *relocR;
	struct register_address raR;

	assert(NULL != expr);

	if (expr->lft)
		internal_problem(__FILE__, __LINE__, "taking one's complement, 2 args, doesn't make sense\n");
	if (expr->rgt)
		typeR = expr_to_imm(expr->rgt, &nlR, &relocR, value, &raR);

	if (VALUE != typeR)
		internal_problem(__FILE__, __LINE__, "taking one's complement of a %s\n", print_expr_ty(typeR));
	else
		**value = ~(**value);

	ret = VALUE;

	return ret;
}

enum ExprType expr_con(struct expr_node *expr, struct nlist **nl,
    struct relocation_info **reloc, int **value, struct register_address *ra)
{
	assert(ExprCon == expr->kind);

	/* check to make sure this is a leaf node */
	if (expr->lft || expr->rgt)
	{
		internal_problem(__FILE__, __LINE__,
			"Node of type ExprCon, non-NULL subtree: ");
		print_expr(stderr, expr);
		putc('\n', stderr);
	}

	ASM_ALLOC(*value, int_alloc, int);

	**value = expr->u.val;

	return VALUE;
}

enum ExprType expr_reg(struct expr_node *expr, struct nlist **nl,
	struct relocation_info **reloc, int **value, struct register_address *ra)
{
	assert(NULL != expr);
	assert(NULL != ra);
	assert(ExprReg == expr->kind);

	/* check to make sure this is a leaf node */
	if (expr->lft || expr->rgt)
	{
		internal_problem(__FILE__, __LINE__,
			"Node of type ExprReg, non-NULL subtree: ");
		print_expr(stderr, expr);
		putc('\n', stderr);
	}

	if (!ra->reg1)
	{
		ra->reg1 = expr->u.reg;
		expr->u.reg = NULL;
	} else if (!ra->reg2) {
		ra->reg2 = expr->u.reg;
		expr->u.reg = NULL;
	} else {
		internal_problem(__FILE__, __LINE__, "Already filled in 2 registers\n");
	}

	return REGISTER;
}

void
free_expr_list(struct expr_list_node *p)
{
	while (p)
	{
		struct expr_list_node *t = p->next;
		free_expr(p->expression);
		free(p);
		p = t;
	}
}
