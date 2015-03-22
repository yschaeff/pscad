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


Keyword = namedtuple('Keyword', 'word args args_cursor_offset desr usage help')


keywords = ['module', 'function', 'include', 'use', 'circle', 'square', 'polygon', 'text', 'sphere', 'cube', 'cylinder', 'polyhedron', 'Transformations', 'translate', 'rotate', 'scale', 'resize', 'mirror', 'multmatrix', 'color', 'offset', 'hull', 'minkowski', 'union', 'difference', 'intersection', 'abs', 'sign', 'sin', 'cos', 'tan', 'acos', 'asin', 'atan', 'atan2', 'floor', 'round', 'ceil', 'ln', 'len', 'let', 'log', 'pow', 'sqrt', 'exp', 'rands', 'min', 'max', 'concat', 'lookup', 'str', 'chr', 'search', 'version', 'version_num', 'norm', 'cross', 'parent_module', 'echo', 'for ', 'intersection_for', 'if ', 'assign ', 'import', 'linear_extrude', 'rotate_extrude', 'surface', 'projection', 'render', 'children', '$fa', '$fs', '$fn', '$t', '$vpr', '$vpt', '$vpd', '$children']
keywords.sort()

kw = [Keyword('module', ' ()', 2, "Defines procedure", "module modname(args", None)
]
lu = {}
for k in kw:
    lu[k.word] = k

#~ default_args = {
    #~ 'include': " <>",
    #~ 'circle': "(r=1)",
    #~ 'square': "([2,2], center = true)",
    #~ 'polygon': "(points = [ [x, y], ... ], paths = [ [p1, p2, p3..], ...], convexity = N)",
    #~ 'text': '("")',
    #~ 'sphere': '()',
    #~ 'cube': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ '': '()',
    #~ 
#~ }
#~ 
#~ 
#~ def suggest_args(text):
    #~ space = text.rfind(" ")
    #~ if space != -1:
        #~ prefix = text[space+1:]
    #~ else:
        #~ prefix = text
    #~ if prefix in default_args:
        #~ return default_args[prefix]
    #~ return ""

def suggest(text):
    space = text.rfind(" ")
    if space != -1:
        prefix = text[space+1:]
    else:
        prefix = text
    r = []
    for word in keywords:
        if word.startswith(prefix):
            r.append(word.strip())
    return r

def common(s1, s2):
    i = 0
    while i < len(s1) and i < len(s2):
        if s1[i] != s2[i]: return i
        i += 1
    return i

def complete(text):
    space = text.rfind(" ")
    if space != -1:
        postfix = text[:space+1]
        prefix = text[space+1:]
    else:
        postfix = ""
        prefix = text
        
    s = suggest(prefix)
    if prefix in s:
        s.remove(prefix)
    if len(s) == 0:
        return text
    elif len(s) == 1:
        return postfix + s[0] +lu[s[0]].args
    a = s[0]
    b = s[1:]
    c = [common(a, d) for d in b]
    m = min(c)
    return postfix + a[:m]
    
