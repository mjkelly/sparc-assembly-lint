/* $Id: digit_label.h,v 1.3 1997/02/27 07:42:35 bediger Exp bediger $
 *
$Log: digit_label.h,v $
Revision 1.3  1997/02/27 07:42:35  bediger
complete re-write

Revision 1.2  1997/02/22 23:49:07  bediger
another wrongish way to do it, but a stab at "textual" nearness

Revision 1.1  1996/12/19 06:49:31  bediger
Initial revision

*/

struct nlist *lookup_digit(char *sym_name);
struct nlist *assemble_digit_label(int digit);
struct nlist *local_symbol_named(int digit);
void passed_local(int digit);
void reset_local_labels(void);
