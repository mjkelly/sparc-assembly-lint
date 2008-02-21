# -----------------------------------------------------------------
# treechecker.py -- functions to check the parse tree
# Copyright 2007 Michael Kelly (michael@michaelkelly.org)
# Copyright 2007 David Lindquist (DavidEzek@gmail.com)
#
# This program is released under the terms of the GNU General Public
# License as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Mon Dec 24 03:16:38 PST 2007
# -----------------------------------------------------------------

import ast
import symbols

def saveOffset(parse_result):
	warn = parse_result.warn
	def checkSave(saveNode):
		if isinstance(saveNode.children[1], ast.Integer):
			offset = saveNode.children[1].getValue()
			if offset % 8 != 0:
				warn("Save offset, line %d: Offset is %d, not a multiple of 8."
					% (saveNode.getLine(), offset))
			if offset > -92:
				warn("Save offset, line %d: Offset is %d, isn't <= -92."
					% (saveNode.getLine(), offset))
			
	parse_result.reduced_tree.map(checkSave, ast.Save)

def branchDelaySlot(parse_result):
	warn = parse_result.warn
	def checkLabelInDelaySlot(branchNode):
		delaySlotNode = branchNode.next
		if delaySlotNode is None:
			warn("Line %d: branch used as last instruction." %
				branchNode.getLine())

		if isinstance(delaySlotNode, ast.LabelDeclaration):
			warn("Line %d: Label declaration in a branch delay slot." %
				delaySlotNode.getLine())
		elif isinstance(delaySlotNode, ast.Branch):
			warn("Line %d: Branch in a branch delay slot." %
				delaySlotNode.getLine())
		elif isinstance(delaySlotNode, ast.Set):
			warn("Line %d: Synthetic instruction that expands to multiple instructions used in a branch delay slot." %
				delaySlotNode.getLine())
			
	parse_result.reduced_tree.map(checkLabelInDelaySlot, ast.Branch)

def wrongSection(parse_result):
	'''Check for instructions in the wrong section. This is really hacky,
	because Michael wants to go to sleep.'''
	warn = parse_result.warn

	# these should only occur in the BSS section, and nowhere but BSS
	# this is INTLIST -> GenericInstruction
	bss_only = [".skip"]

	# these should only occur in the data section, and nowhere but data
	# these are all INTLIST, FLOATLIST, or STRINGLIST -> GenericInstruction
	data_only = [".ascii", ".asciz", ".byte", ".double", ".half", ".nword",
		".quad", ".single", ".uahalf", ".uaword", ".word", ".xword"]
	
	# list of sections with errors to avoid multiple-reporting
	reported_sections = {}

	# this is a list so we can increment it inside functions
	declared_sections = [0]
	
	def wrongSectionWarning(instrNode):
		section = instrNode._section.getName()
		if not reported_sections.has_key(section):
			reported_sections[section] = True
			warn("Line %d: Suspicious instruction for %s section. (Only one error reported per section.)"
				% (instrNode.getLine(), section))

	def checkWrongSection(instrNode):
		'''Check for instructions in the wrong section. We stop after
		finding the first one, to avoid massive error lists.'''

		#print "%s: section= %s" % (instrNode, instrNode._section)

		if instrNode._section.isText():
			# bss-only or data-only instructions in the text section
			if isinstance(instrNode, ast.GenericInstruction):
				if (instrNode.name in bss_only) or (instrNode.name in data_only):
					wrongSectionWarning(instrNode)
		elif instrNode._section.isData():
			# non-data instructions in data section 
			if isinstance(instrNode, ast.GenericInstruction):
				if not instrNode.name in data_only:
					wrongSectionWarning(instrNode)
			else:
				wrongSectionWarning(instrNode)
		elif instrNode._section.isBSS():
			# non-bss instructions in bss section
			if isinstance(instrNode, ast.GenericInstruction):
				if not instrNode.name in bss_only:
					wrongSectionWarning(instrNode)
			else:
				wrongSectionWarning(instrNode)
	
	def countSectionDecls(instrNode):
		'''This just counts the number of section delcarations in the file.'''
		declared_sections[0] += 1	# hmm, this is a stupid trick

	parse_result.reduced_tree.map(checkWrongSection, ast.Instruction)
	parse_result.reduced_tree.map(countSectionDecls, ast.SectionDeclaration)

	if declared_sections[0] == 0:
		warn("No section declarations! Everything is implicitly in the text section.")

def registers(parse_result):
	'''Check register usage, particularly alternate ways of accessing named
	registers.'''
	warn = parse_result.warn

	def checkRegs(reg):
		name = reg.getName()
		
		if name.lower() == '%i6':
			warn('Line %d: Register %s is better known as %%fp. Do not use as general-purpose register.'
				% (reg.getLine(), name))
		if name.lower() == '%i7':
			warn('Line %d: Register %s is the return address - 8. Do not use as general-purpose register.'
				% (reg.getLine(), name))
		if name.lower() == '%o6':
			warn('Line %d: Register %s is better known as %%sp. Do not use as general-purpose register.'
				% (reg.getLine(), name))
		if name.lower() == '%o7':
			warn('Line %d: Register %s is the function call address. Do not use as general-purpose register.'
				% (reg.getLine(), name))


	parse_result.reduced_tree.map(checkRegs, ast.Reg)

def sections(parse_result):
	'''Check .sections and .pushsections for suspicious section names.'''
	warn = parse_result.warn

	expectedSections = symbols.section_declarations.keys()

	def checkSectionDecls(sec):
		name = sec.getName()
		if not name in expectedSections:
			warn('Line %d: Suspicious section name "%s".' % (sec.getLine(), name))

	parse_result.reduced_tree.map(checkSectionDecls, ast.SectionDeclaration)

allChecks = [saveOffset, branchDelaySlot, wrongSection, registers, sections]
