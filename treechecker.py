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

def _nodeMap(tree, f, nodeClass):
	'''Call f on all nodes of class nodeClass in parse tree tree. If
	   nodeClass = None, f is called on all nodes.'''
	if tree is None:
		return
	
	if nodeClass is None:
		f(tree)
		for child in tree.children:
			_nodeMap(child, f, nodeClass)
	elif isinstance(tree, nodeClass):
		f(tree)
	else:
		for child in tree.children:
			_nodeMap(child, f, nodeClass)

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
			
	_nodeMap(parse_result.reduced_tree, checkSave, ast.Save)

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
			
	_nodeMap(parse_result.reduced_tree, checkLabelInDelaySlot, ast.Branch)


allChecks = [saveOffset, branchDelaySlot ]
