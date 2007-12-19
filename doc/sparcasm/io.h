/* $Id: io.h,v 1.1 1996/12/13 14:36:37 bediger Exp bediger $
$Log: io.h,v $
Revision 1.1  1996/12/13 14:36:37  bediger
Initial revision

*/

void write_instn(int *instn);
void input_problem(char *fmt, ...);
void internal_problem(char *filename, int line_in_file, char *fmt, ...);
