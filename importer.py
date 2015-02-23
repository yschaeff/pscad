from Datastruct import Node
import re

def canonicalize(t_str, t_type):
    if t_type == 0:
        r = re.compile(r"\s*([$\w]+)\s*(=)\s*([^;\n]+);")
        m = r.match(t_str)
        res = " ".join(m.groups())
    elif t_type == 1:
        r = re.compile(r"\s*(\w+)\s*(\(.*\))\s*;")
        m = r.match(t_str)
        res = "".join(m.groups())
    elif t_type == 2:
        r = re.compile(r"\s*(\w+(?:\s+\w+)?)\s*(\(.*\))")
        m = r.match(t_str)
        res = "".join(m.groups())
    else:
        ## we don't want to process comments further
        return t_str.strip()

    ## remove duplicate whitespaces
    r = re.compile(r"\s+")
    res = r.sub(" ", res)
    ## every comma should be followed by space
    r = re.compile(r",[^\s]")
    res = r.sub(", ", res)
    return res


def import_scad(filename):
    f = open(filename)
    raw = f.read()
    tree = Node("Document Root")

    re_comment = re.compile(r"//.*\n")
    re_whitespace = re.compile(r"\s+")
    re_assignment = re.compile(r"\s*[$\w]+\s*=\s*[^;\n]+;")
    re_call = re.compile(r"\s*\w+\s*\(.*\)\s*;")
    re_func = re.compile(r"\s*\w+(?:\s+\w+)?\s*\(.*\)")
    re_open = re.compile(r"\s*{")
    re_close = re.compile(r"\s*}")

    ####
    ## Strip the file of all comments, parsing is *much* easier
    ## without. Remember the comments and their position in the file
    comments = []
    while True:
        m = re_comment.search(raw)
        if not m: break
        s = m.group(0)
        raw = raw[:m.start()] +" "+ raw[m.end():]
        comments.append((s, m.start()))

    ####
    ## Every single piece of file should be covered by one of these
    ## regular expressions. If not bail out
    regexps = [re_assignment, re_call, re_func, re_open, re_close, re_whitespace, re_comment]
    T_ASS = 0; T_CAL = 1; T_FUN = 2; T_OPN = 3; T_CLS = 4; T_WHT = 5; T_COM = 6
    matches = []
    i = 0
    while i<len(raw):
        match = False
        for mtype, r in enumerate(regexps):
            m = r.match(raw, i)
            if m:
                s = m.group(0)
                i += len(s)
                match = True

                ####
                ##
                while comments and i > comments[0][1]:
                    c,p = comments.pop(0)
                    c = canonicalize(c, T_COM)
                    matches.append((c, T_COM))

                s = canonicalize(s, mtype)
                matches.append((s, mtype))
                break
                

        if not match:
            print("\"%s\""%raw[i:])
            print("no match, import error")
            return None


    p = [[tree, 1]]
    for m,t in matches:
        if not p:
            print("Error parsing tree")
            return None
        parent = p[-1][0]
        if t == T_OPN:
            p[-1][1] += 1
        elif t == T_CLS:
            p[-1][1] -= 1
            assert(p[-1][1] >= 0)
            #~ if (p[-1][1] < 0):
                #~ for x in p:
                    #~ print "DBG: " + str(x[0])
                #~ break
            if p[-1][1] == 0:
                p.pop()
        elif t == T_ASS or t == T_CAL:
            n = Node(m.strip())
            n.parent = p[-1][0]
            n.parent.children.append(n)
            if p[-1][1] == 0:
                p.pop()
        elif t == T_FUN:
            n = Node(m.strip())
            n.parent = p[-1][0]
            n.parent.children.append(n)
            if p[-1][1] == 0:
                p.pop()
            p.append([n, 0])
        elif t == T_COM:
            n = Node(m.strip())
            n.parent = p[-1][0]
            n.parent.children.append(n)
        else:
            #whitespace, ignore
            pass
            
    tree.fix_descendants()
    return tree


def export_scad(filename, tree):
    if not tree:
        return 1
    f = open(filename, 'w')
    parent_stack = []
    n = tree.depth_first_walk()
    l = 0
    while n and n != tree:
        while parent_stack and parent_stack[-1] != n.parent:
            l -= 1
            #~ print "  "*l + "}"
            f.write("  "*l + "}\n")
            parent_stack.pop()
        prefix =  "  "*l + str(n)
        if n.children:
            f.write("%s {\n"%prefix)
            l += 1
            parent_stack.append(n)
        else:
            f.write("%s;\n"%prefix)

        n = n.depth_first_walk()
    while parent_stack:
        n = parent_stack.pop()
        l -= 1
        f.write("  "*l + "}\n")
    return 0
