from collections import namedtuple
import re

NodeType = namedtuple('NodeType', ['name', 'has_children'])

r_empty      = re.compile(r"^\s*$")
r_comment    = re.compile(r"^\s*(//.*$)")
r_assignment = re.compile(r"^\s*([!#%*\s]*)\s*([$\w]+)\s*(=)\s*(.+$)")
r_block      = re.compile(r"^\s*([!#%*\s]*)\s*(\w+)\s*(\()\s*(.*?)\s*(\))\s*$")
r_function   = re.compile(r"^\s*([!#%*\s]*)\s*(function)\s+(\w+)\s*(\()\s*(.*?)\s*(\))\s*(=)\s*(.*$)")
r_module     = re.compile(r"^\s*([!#%*\s]*)\s*(module)\s+(\w+)\s*(\()\s*((?:[^;\)]*[^\s])?)\s*(\)\s*$)")
r_include    = re.compile(r"^\s*([!#%*\s]*)\s*(include)\s+(<)\s*([\.\w/]+)\s*(>\s*$)")
r_use        = re.compile(r"^\s*([!#%*\s]*)\s*(use)\s+(<)\s*([\.\w/]+)\s*(>\s*$)")

exps = [r_empty, r_comment, r_assignment, r_block, r_function, r_module,
    r_include, r_use]

exp_info = {
    r_empty     : NodeType(     "EMPTY", False),
    r_comment   : NodeType(   "COMMENT", False),
    r_assignment: NodeType("ASSIGNMENT", False),
    r_block     : NodeType(     "BLOCK",  True), ## only has children if defined
    r_function  : NodeType(  "FUNCTION", False),
    r_module    : NodeType(    "MODULE",  True),
    r_include   : NodeType(   "INCLUDE", False),
    r_use       : NodeType(       "USE", False)
}

def is_balanced(text):
    pair = {")":"(", "]":"[", "}":"{"}
    stack = []
    for c in text:
        if c in pair.values():
            stack.append(c)
        elif c in pair.keys():
            if not stack:
                return False
            p = stack.pop()
            if p != pair[c]:
                return False
    return (len(stack) == 0)

def is_valid(text):
    global exps
    if not is_balanced(text):
        return False
    for e in exps:
        if e.match(text):
            return True
    return False
