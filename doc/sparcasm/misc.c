/*
$Log: misc.c,v $
Revision 1.7  1997/03/14 05:40:07  bediger
make code reflect changes to struct expr_node (minimize size of that struct)

Revision 1.6  1997/02/14 06:31:11  bediger
fix a few memory leaks.

Revision 1.5  1997/02/04 04:01:36  bediger
support for changed assembly statement representation,
which basically means a vastly enlarged construct_stmnt() function

Revision 1.4  1997/01/15 01:30:37  bediger
use the shortcut memory alloc to do some debugging

Revision 1.3  1996/12/13 15:20:42  bediger
remove vestigial reference to old macro

Revision 1.2  1996/12/13 14:32:52  bediger
Switched to ALLOC_DECL macro and added deallocation for dynamically-
allocated register representations.

Revision 1.1  1996/12/12 20:55:47  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/misc.c,v 1.7 1997/03/14 05:40:07 bediger Exp bediger $";

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <nlist.h>
#include <a.out.h>

#include <assy.h>
#include <io.h>
#include <expr.h>
#include <shortcut_alloc.h>

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif


ALLOC_DECL(stmnt_alloc, 1);
ALLOC_DECL(addr_alloc, 5);

/* 3 registers in any given instruction, 1 extra for synthetic
 * instruction composition */
ALLOC_DECL(register_alloc, 4);

extern struct mem_stack int_alloc;

/* function construct_stmnt() looms large.  It centralizes the
 * work done to make an internal rep of the "3 register" SPARC
 * isntructions.  Some synthetic instructions will need to be
 * assembled through different functions to account for the
 * assumptions made in construct_stmnt()
 */
struct asm_stmnt *
construct_stmnt(
	struct mnm       *mnemonic,
	struct expr_node *r1,
	struct expr_node *r2,
	struct expr_node *r3,
	struct expr_node *asi
)
{
	struct asm_stmnt *r;
	struct nlist *sym = NULL;
	struct relocation_info *reloc = NULL;
	struct register_address reg;
	int *value;

	assert(NULL != mnemonic);

	ASM_ALLOC(r, stmnt_alloc, struct asm_stmnt);

	r->mnemonic = mnemonic;
	r->asi = -1;
	r->rs1 = r->rs2 = r->rd = NULL;
	r->symbol = NULL;
	r->reloc = NULL;
	r->immediate = NULL;

	/* irregular, but construct_stmnt() only gets called this way for
	 * an instruction with no operands.  It doesn't make sense to
	 * allocate stuff only to very shortly later free it */

	if (NULL == r1 && NULL == r2 && NULL == r3)
		return r;

	if (NULL != asi)
	{
		if (ExprCon != asi->kind)
			internal_problem(__FILE__, __LINE__, "ASI not an integer between 0 and 255\n");
		else if (0 < asi->u.val && asi->u.val > 255)
			input_problem("ASI allowable range 0-255, given as %d\n", asi);
		else
			r->asi = asi->u.val;

		free_expr(asi);
	}

	if (NULL != r1)
	{
		expr_to_imm(r1, &sym, &reloc, &value, &reg);
		r->symbol = sym;
		r->reloc = reloc;
		if (reg.reg1)
			r->rs1 = reg.reg1;
		if (reg.reg2)
			r->rs2 = reg.reg2;
		r->immediate = value;

		free_expr(r1);
	}

	if (NULL != r2)
	{
		expr_to_imm(r2, &sym, &reloc, &value, &reg);

		if (sym)
		{
			if (r->symbol)
			{
				input_problem("At least two symbols: ");
				print_expr(stderr, r1);
				fprintf(stderr, ", ");
				print_expr(stderr, r2);
				putc('\n', stderr);
			}
			r->symbol = sym;
			r->reloc = reloc;
		}

		if (reg.reg1)
			r->rs2 = reg.reg1;

		if (reg.reg2)
		{
			input_problem("2nd register goofy (shouldn't be %r1 + %r2): ");
			print_expr(stderr, r2); putc('\n', stderr);
		}

		if (value)
		{
			if (r->immediate)
				input_problem("At least two immediates\n");
			r->immediate = value;
		}

		free_expr(r2);
	} 

	if (NULL != r3)
	{
		expr_to_imm(r3, &sym, &reloc, &value, &reg);

		if (sym)
		{
			if (r->symbol)
			{
				input_problem("At least two symbols: ");
				if (r1) { print_expr(stderr, r1); fprintf(stderr, ", "); }
				if (r2) { print_expr(stderr, r2); fprintf(stderr, ", "); }
				print_expr(stderr, r3);
				putc('\n', stderr);
				ASM_ALLOC(r->rd, register_alloc, struct register_rep);
				r->rd->type = REGULAR;
				r->rd->regno = 0;
			}
			r->symbol = sym;
			r->reloc = reloc;
		}

		if (reg.reg1)
			r->rd = reg.reg1;

		if (reg.reg2)
		{
			input_problem("3rd register goofy (shouldn't be %r1 + %r2): ");
			print_expr(stderr, r3); putc('\n', stderr);
		}

		if (value)
		{
			if (r->immediate)
			{
				if (strcmp(mnemonic->op_mnm, "call"))
				{	/* ugly special case */
					input_problem("%s opcode: 3rd register goofy (shouldn't have an immediate):", mnemonic->op_mnm);
					print_expr(stderr, r3); putc('\n', stderr);
				} else {
					ASM_DEALLOC(value, int_alloc);
					value = NULL;
				}
			} else
				r->immediate = value;
		}

		free_expr(r3);
	}

	return r;
}

void
free_stmnt(struct asm_stmnt *p)
{
	extern int pass;

	assert(NULL != p);

	if (p->rs1)
		ASM_DEALLOC(p->rs1, register_alloc);
	if (p->rs2)
		ASM_DEALLOC(p->rs2, register_alloc);
	if (p->rd)
		ASM_DEALLOC(p->rd, register_alloc);

	if (p->immediate) ASM_DEALLOC(p->immediate, int_alloc);

	/* can't free p->reloc on 2nd pass, or p->symbol on any pass:
	 * they should be in the symbol table or relocation info arrays. */

	if (1 == pass && p->reloc)
		free(p->reloc);

	ASM_DEALLOC(p, stmnt_alloc);
}
