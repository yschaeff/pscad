from Datastruct import Node
import re, os.path

ROOT = "Document Root"

def parse_scad(raw):
    tree = Node(ROOT)

    re_comment = re.compile(r"//.*\n")

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

    T_OPEN, T_CLOSE, T_TERM, T_STAT, T_COMM = range(5)

    ####
    ## Parse document, split in logical units
    m = [] #tuples (raw-text, type)
    i = 0; j = 0 # i: index of first char of unprocessed command. j: index of first unprocessed char
    c = 0 # number of opened brackets
    gobble = False # if true consume everything till newline
    gobble_nl = False
    while i < len(raw) and j < len(raw):
        while comments and j > comments[0][1]:
            comment,_ = comments.pop(0)
            m.append((comment, T_COMM))

        ch = raw[j]
        #~ print(ch, end=""),
        if ch == "=" and c == 0:
            #gobble all the way to ;
            gobble = True
        if ch == " " and c == 0 and \
                ((raw[j-3:].startswith("use ") and j-3>=1) or \
                (raw[j-7:].startswith("include ") and i-7>=7)):
            #gobble all the way to ;
            gobble_nl = True
        elif ch == "\n" and gobble_nl:
            if c: raise(Exception("Unclosed bracket"))
            m.append((raw[i:j], T_STAT))
            m.append((raw[j:j+1], T_TERM))
            gobble_nl = False
            i = j+1
        elif ch == ";":
            if c: raise(Exception("Unclosed bracket"))
            if gobble:
                m.append((raw[i:j], T_STAT))
                m.append((raw[j:j+1], T_TERM))
                gobble = False
            else:
                m.append((raw[i:j+1], T_TERM))
            i = j+1
        elif ch == "{":
            if c: raise(Exception("Unclosed bracket"))
            m.append((raw[i:j+1], T_OPEN))
            i = j+1
        elif ch == "}":
            if c: raise(Exception("Unclosed bracket"))
            m.append((raw[j:j+1], T_CLOSE))
            i = j+1
        elif gobble or gobble_nl:
            pass
        elif ch == "(":
            c += 1
        elif ch == ")":
            c -= 1
            r= re.compile(r"\s*=")
            if c == 0:
                if r.match(raw[j+1:]):
                    pass
                else:
                    m.append((raw[i:j+1], T_STAT))
                    i = j+1
        j += 1
    if c:
        raise(Exception("Extra close bracket"))

    tree = Node(ROOT)
    s = [[tree, 0]]
    for i,t in m:
        #~ print("- "+str(i).strip())
        #~ print(len(s))
        if t == T_TERM:
            while s[-1][1] == 0 and len(s) > 1:
                s.pop()
            continue
        elif t == T_OPEN:
            s[-1][1] += 1
        elif t == T_CLOSE:
            s[-1][1] -= 1
            while s and s[-1][1] == 0 and len(s) > 1:
                s.pop()
        elif t == T_STAT:
            n = Node(i)
            n.parent = s[-1][0]
            n.parent.children.append(n)
            s.append([n, 0])
        elif t == T_COMM:
            n = Node(i)
            n.parent = s[-1][0]
            n.parent.children.append(n)
            
    return tree

def import_scad(filename):
    if not os.path.isfile(filename):
        return Node(ROOT)

    r = re.compile(r"\s+")
    f = open(filename)
    raw = f.read()
    f.close()
    tree = parse_scad(raw)

    if tree:
        for node in tree:
            c, _ = r.subn(" ", node.content)
            node.content = c.strip()
        tree.fix_descendants()

    return tree

def export_scad(filename, tree):
    re_comment = re.compile(r"\s*//.*")
    if not tree:
        return 1
    f = open(filename, 'w')
    parent_stack = []
    n = tree.depth_first_walk()
    l = 0
    for i, n in enumerate(tree[1:]):
        if i == 0: continue #our tree doesn't support slicing
        while parent_stack and parent_stack[-1] != n.parent:
            p = parent_stack.pop()
            l -= 1
            f.write("  "*l + "}\n")
        prefix =  "  "*l + str(n)
        if n.children:
            if re_comment.match(str(n)):
                f.write("%s\n"%prefix)
                f.write("  "*l+"{\n")
                l += 1
            else:
                f.write("%s {\n"%prefix)
                l += 1
            parent_stack.append(n)
        elif re_comment.match(str(n)):
            f.write("%s\n"%prefix)
        else:
            f.write("%s;\n"%prefix)

    while parent_stack:
        n = parent_stack.pop()
        l -= 1
        f.write("  "*l + "}\n")
    return 0
