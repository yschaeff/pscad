import curses

class Node():
    def __init__(self, content):
        self.content = content
        self.parent = None
        self.children = []
        self.descendants = 0

    def fix_descendants(self):
        """The number of descendants"""
        d = sum(map(lambda c: c.fix_descendants(), self.children))
        d += len(self.children)
        self.descendants = d
        return self.descendants

    #~ def update_descendants(self):
        #~ # children
        #~ d = sum(map(lambda c: c.descendants, self.children))
        #~ self.descendants = d + len(self.children)
        #~ p = self.parent
        #~ while p:
            #~ p.update_descendants()
            #~ p = p.parent

    def offset(self, node):
        """Find the distance between self and a subnode"""
        p = node
        offset = 0
        while p.parent:
            for c in p.parent.children:
                if c == node: break
                offset += c.descendants + 1
            offset += 1
            p = p.parent
            node = p
        return offset

    def merge(self, index, source):
        if not source:
            return self
        assert(source.parent == None)
        assert(index >= 0 and index <= len(self.children))

        select = self
        for i, c in enumerate(source.children):
            self.descendants += 1 + c.descendants
            c.parent = self
            select = c
            self.children.insert(index + i, c)
        source.children = []
        source.descendants = 0
        return select
            
    def split(self):
        root = Node("Root")
        if self.parent == None:
            select = self
            root.children = self.children
            root.descendants = self.descendants
            for c in root.children:
                c.parent = root
            self.children = []
            self.descendants = 0
        else:
            select = self.parent
            root.descendants = 1 + self.descendants
            self.parent.descendants -= root.descendants
            root.children = [self]
            self.parent.children.remove(self)
            self.parent = root
        return root, select

    #~ def detach(self):
        


    def pop(self, node):
        assert(self.parent == None)
        root = Node("Root")
        if self == node:
            root.children = node.children
            root.descendants = node.descendants
            for c in root.children:
                c.parent = root
            node.children = []
            node.descendants = 0
        else:
            root.descendants = 1 + node.descendants
            self.descendants -= root.descendants
            root.children = [node]
            self.children.remove(node)
            node.parent = root
        return root
            
            
        
    def add_child(self, index, node):
        node.parent = self
        self.children.insert(index, node)

    def push_child(self, node):
        node.parent = self
        self.children.append(node)

    def __str__(self):
        return str(self.content)
    def __repr__(self):
        return "N()"

    def rnext(self, child):
        l = len(self.children)
        i = self.children.index(child)
        if i+1 < l:
            return self.children[i+1]
        elif self.parent:
            return self.parent.rnext(self)
        return None

    def next(self):
        n = self.depth_first_walk()
        if not n:
            return self
        return n

    def depth_first_walk(self):
        if self.children:
            return self.children[0]
        elif not self.parent:
            return self
        next = self.parent.rnext(self)
        if next:
            return next
        return None

    def left(self):
        if not self.children:
            return self
        return self.children[-1].left()

    def rprev(self, child):
        i = self.children.index(child)        
        if i == 0:
            return self
        return self.children[i-1].left()

    def prev(self):
        if not self.parent:
            return self
        return self.parent.rprev(self)

    
