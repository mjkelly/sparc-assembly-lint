/* requires #inclusion of stdlib.h and assy.h first */
/* $Id: shortcut_alloc.h,v 1.4 1997/02/14 06:33:35 bediger Exp bediger $
$Log: shortcut_alloc.h,v $
Revision 1.4  1997/02/14 06:33:35  bediger
correct a bug that caused it to not count allocations correctly.

Revision 1.3  1997/02/04 04:24:21  bediger
fill deallocated memory with rubbish

Revision 1.2  1996/12/13 14:36:37  bediger
macros for type-specific memory allocation and managment

*/


/*
 * Shortcut allocation: struct mem_stack defines a stack on which to
 * keep "max" entries of a dynamically allocated chuck of memory.
 *
 * ASM_ALLOC(pointer, stack, type_pointed_to) fills in "pointer" with
 * memory from struct mem_stack "stack" of type "type_pointed_to".
 * If "stack" is already empty, it uses macro STRUCT_ALLOC from
 * assy.h to malloc the memory.
 *
 * ASM_DEALLOC(pointer, stack) puts the memory pointed to by "pointer"
 * back on the struct mem_stack "stack".  This prevents expensive
 * calls to the general purpose free() deallocation.
 *
 * ALLOC_DECL(stack name, size) is the macro to use to declare
 * a stack of a particular name (stack name) and size (size).
 */

/* $Header: /home/ediger/src/csrc/sparc_assembler10/RCS/shortcut_alloc.h,v 1.4 1997/02/14 06:33:35 bediger Exp bediger $
$Log: shortcut_alloc.h,v $
Revision 1.4  1997/02/14 06:33:35  bediger
correct a bug that caused it to not count allocations correctly.

Revision 1.3  1997/02/04 04:24:21  bediger
fill deallocated memory with rubbish

Revision 1.2  1996/12/13 14:36:37  bediger
macros for type-specific memory allocation and managment

Revision 1.1  1996/12/12 21:00:57  bediger
Initial revision

*/

struct mem_stack {
    int cnt;
    int max;
    void **stack;
	int allocations;
};

#define ALLOC_DECL(basename, N) \
	void *basename##_stack[N+1]; struct mem_stack basename = {0, N, &basename##_stack[0], 0}

#define ASM_ALLOC(r, STK, T) \
	if ((STK).cnt){ \
		(r)=((STK).stack[--((STK).cnt)]); \
	}else{ \
		STRUCT_ALLOC(r,T); ++STK.allocations; \
	}

#define ASM_DEALLOC(r, STK) \
	if ((STK).cnt < (STK).max){\
			memset((r), 0xc5, sizeof *(r));\
			(STK).stack[(STK).cnt++]=(r);\
		}else{\
			internal_problem(__FILE__, __LINE__,\
				"freeing a struct for good, cnt %d, max %d\n",\
				(STK).cnt, (STK).max); assert(0); \
			free(r); --STK.allocations;\
		}
