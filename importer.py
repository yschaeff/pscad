from Datastruct import Node

def tokenize(raw):
    b = 0;
    i = 0
    e = len(raw)
    tokens = []
    inblock = False
    opencount = 0;

    while i<e:
        if inblock:
            if raw[i] == '{':
                opencount += 1
            if raw[i] == '}':
                opencount -= 1
                if opencount == 0:
                    tokens.append(raw[b:i+1])
                    b = i+1
                    inblock = False
        elif raw[i] == '{':
            inblock = True
            opencount = 1
            #~ b = i+1
        elif raw[i] == '}':
            b = i+1
        elif raw[i] == ';':
            tokens.append(raw[b:i])
            b = i+1
        else:
            pass
        i += 1
    if i > b:
        tokens.append(raw[b:e])
    return tokens

def split(raw):
    #search for ( and than )
    #if we encounter = first abort
    b = 0;
    i = 0
    e = len(raw)
    inargs = False
    opencount = 0
    seekingclosure = 0
    
    while i<e:
        if seekingclosure:
            if raw[i] == '{':
                opencount += 1
            elif raw[i] == '}':
                opencount -= 1
                if opencount == 0:
                    return None, raw[b:i]
        
        elif inargs:
            if raw[i] == '(':
                opencount += 1
            elif raw[i] == ')':
                opencount -= 1
                if opencount == 0:
                    #~ tokens.append(raw[b:i+1])
                    return raw[b:i+1], raw[i+1:e]
        elif raw[i] == '{':
            #there is no parent, these are all children!
            b = i+1
            seekingclosure = 1
            opencount = 1
        elif raw[i] == '(':
            inargs = True
            opencount = 1
        elif raw[i] == '=':
            return raw, None
        i += 1
    return raw, None
    

def subtree(parent_node, raw):
    queue = [(raw, parent_node)]

    while queue:
        #~ print "\nQUEUE:", queue
        qitem, parent = queue.pop(0)
        #~ print "POPPED:", qitem, "<%s>"%parent
        tokens = tokenize(qitem)
        #~ print "TOKENS:", tokens
        if len(tokens) == 1:
            p,c = split(tokens[0])
            if not p:
                if c:
                    queue.insert(0, (c, parent))
            else:
                n = Node(str(p).strip())
                parent.push_child(n)
                if c:
                    queue.insert(0, (c, n))
        else:
            tokens.reverse()
            for token in tokens:
                queue.insert(0, (token, parent))

def import_scad(filename):
    f = open(filename)
    raw = f.read()
    ## TODO strip comments
    cooked = raw.translate(None, "\t\n")

    tree = Node("Document Root")

    subtree(tree, cooked)
    
    return tree

def export_scad(filename, tree):
    
    f = open(filename, 'w')
    parent_stack = []
    n = tree.depth_first_walk()
    l = 0
    while n:
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
