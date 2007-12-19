/* requires inclusion of stdio.h, assy.h, a.out.h */
/* $Id: expr.h,v 1.6 1997/03/14 05:40:22 bediger Exp bediger $
$Log: expr.h,v $
Revision 1.6  1997/03/14 05:40:22  bediger
minimize size of struct expr_node, make field names more rational.

Revision 1.5  1997/03/10 01:15:10  bediger
I don't know

Revision 1.4  1997/02/04 04:00:31  bediger
support for changed assembly statement representation

Revision 1.3  1997/01/15 01:29:51  bediger
make it do "symbol = expression" stuff

Revision 1.2  1996/12/17 06:29:40  bediger
Added elements to enum ExprNodeT to handle all the unary and binary
operations that the old SunOS assembler handled

Revision 1.1  1996/12/13 14:36:37  bediger
Initial revision

*/


enum ExprNodeT {
	ExprAdd, ExprSub, ExprMul, ExprDiv, ExprMod,
	ExprLShift, ExprRShift,
	ExprHiBit, ExprLoBit, ExprComp,
	ExprBitOr, ExprBitXor, ExprBitAnd,
	ExprSym, ExprCon, ExprStr, ExprFlt,
	ExprReg
};

struct expr_node {
	enum ExprNodeT    kind;
	struct expr_node *lft;
	struct expr_node *rgt;
	union {
		char                *id;
		int                  val;
		double               fltval;  /* both "float" and "double" */
		struct register_rep *reg;
	} u;
};

struct expr_node *
construct_expr(
	enum ExprNodeT       op,
	struct expr_node    *left,
	struct expr_node    *right,
	char                *id,
	int                  val,
	double               fltval,
	struct register_rep *reg
);

enum ExprType { VALUE, SYMBOL, REGISTER };

void print_expr(FILE *stream, struct expr_node *expr);
char *print_expr_kind(enum ExprNodeT op);
void free_expr(struct expr_node *expr);
enum ExprType expr_to_imm(
	struct expr_node *xpr,
	struct nlist **nl,
	struct relocation_info **reloc,
	int **val,
	struct register_address *regaddr
);
enum ExprType expr_size(
	struct expr_node *xpr,
	int *val
);
void free_expr_list(struct expr_list_node *);
