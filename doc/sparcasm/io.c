/*
$Log: io.c,v $
Revision 1.2  1997/02/05 06:34:45  bediger
removed extraneous #include

Revision 1.1  1996/12/13 14:32:52  bediger
Initial revision

*/
static char rcsident[] = "$Header: /home/ediger/src/csrc/sparc_assembler10/RCS/io.c,v 1.2 1997/02/05 06:34:45 bediger Exp bediger $";

#include <stdio.h>    /* uses fwrite() */
#include <stdarg.h>   /* the variadic functions */
#include <errno.h>    /* errno, arg to strerror() */
#include <string.h>   /* strerror() */
#include <assert.h>

#include <assy.h>    /* globals like CUROFFSET */
#include <io.h>      /* prototypes of functions defined herein */

#ifdef USE_DMALLOC
#include <dmalloc.h>
#endif

/*
 * There's some unavoidable jiggery-pokey here.  Typing the argument
 * to write_instn() as a pointer-to-int is just a way to get "polymorphism"
 * or "function overloading" out of ANSI C.  The real thing pointed to
 * is one of several structs representing SPARC instruction formats
 * as sets of bitfields.
 *
 * And what about SPARC V9?  This explicitly assumes an int is just as
 * wide as an instruction, which is no longer true for V9, I think.
 */

void
write_instn(int *instn)
{
	if (fwrite((void *)instn, 4, 1, a_out) != 1)
	{
		internal_problem(__FILE__, __LINE__,
			"failed to write instruction to %s segment at 0x%x: %s\n",
			lineno, CURSEGNAME, CURROFFSET, strerror(errno));
	} else
		CURROFFSET += 4;
}

/*
 * Supposedly only reports a problem with the input
 */
void
input_problem(char *fmt, ...)
{
	va_list ap;

	assert(NULL != fmt);

	va_start(ap, fmt);

	/* I think this is the GNU way of doing error output */
	fprintf(stderr, "%s:%d: ", working_input_file, lineno);
	vfprintf(stderr, fmt, ap);

	va_end(ap);
}

/*
 * Supposedly only reports a problem internal to the assembler
 * program, but it also reports the input line number, just in
 * case that's the cause.
 */
void
internal_problem(char *filename, int line_in_file, char *fmt, ...)
{
	va_list ap;

	assert(NULL != fmt);

	va_start(ap, fmt);

	fprintf(stderr, "Internal problem, \"%s\", line %d (input line %d in \"%s\"): ",
		filename, line_in_file, lineno, working_input_file);
	vfprintf(stderr, fmt, ap);

	va_end(ap);
}
