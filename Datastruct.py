import curses
from copy import deepcopy


class Node():
    def __init__(self, content):
        self.content = content
        self.parent = None
        self.children = []
        self.descendants = 0

    def fix_descendants(self):
        """The number of descendants"""
        d = sum([c.fix_descendants() for c in self.children])
        d += len(self.children)
        self.descendants = d
        return self.descendants

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

    def node_at_offset(self, index):
        """Find the node closest to index"""
        if index <= 0 or not self.children:
            return self
        d = 1
        for c in self.children:
            if d + c.descendants >= index:
                return c.node_at_offset(index - d)
            d += c.descendants + 1
        return self.children[-1].node_at_offset(index)

    def merge(self, index, source):
        if not source:
            return self
        assert(source.parent == None)
        assert(index >= 0 and index <= len(self.children))

        for i, c in enumerate(source.children):
            self.descendants += 1 + c.descendants
            p = self.parent
            while p:
                p.descendants += 1 + c.descendants
                p = p.parent
            c.parent = self
            self.children.insert(index + i, c)
        source.children = []
        source.descendants = 0
            
    def split(self):
        root = Node("Root")
        if self.parent == None:
            root.children = self.children
            root.descendants = self.descendants
            for c in root.children:
                c.parent = root
            self.children = []
            self.descendants = 0
        else:
            root.descendants = 1 + self.descendants
            p = self.parent
            while p:
                p.descendants -= root.descendants
                p = p.parent
            root.children = [self]
            self.parent.children.remove(self)
            self.parent = root
        return root

    def detach(self):
        root = Node("Root")
        if self.parent == None:
            return root
        pidx = self.parent.children.index(self)
        self.parent.children.pop(pidx)
        for i, c in enumerate(self.children):
            c.parent = self.parent
            self.parent.children.insert(pidx + i, c)

        self.parent.descendants -= 1
        root.descendants = 1
        self.descendants = 0
        self.children = []

        self.parent = root
        root.children = [self]
        return root

    def gobble(self):
        if self.parent == None:
            return
        pidx = self.parent.children.index(self)
        if len(self.parent.children) < pidx + 2:
            return
        sibling = self.parent.children.pop(pidx + 1)
        self.children.append(sibling)
        self.descendants += 1 + sibling.descendants
        sibling.parent = self

    def degobble(self):
        if self.parent == None:
            return
        pidx = self.parent.children.index(self)
        if not self.children:
            return
        child = self.children.pop()
        self.descendants -= 1 + child.descendants
        child.parent = self.parent
        self.parent.children.insert(pidx+1, child)

    def cling(self):
        """Become a child of your smaller sibling"""
        if self.parent == None:
            return
        pidx = self.parent.children.index(self)
        if pidx <= 0:
            return
        self.parent.children.pop(pidx)
        self.parent = self.parent.children[pidx-1]
        self.parent.children.append(self)
        self.parent.descendants += 1 + self.descendants

    def decling(self):
        """Become a child of your grandparent"""
        if self.parent == None:
            return
        if self.parent.parent == None:
            return
        pidx = self.parent.children.index(self)
        if pidx +1 != len(self.parent.children):
            return
        self.parent.children.pop()
        self.parent.descendants -= 1 + self.descendants
        pidx = self.parent.parent.children.index(self.parent)
        self.parent = self.parent.parent
        self.parent.children.insert(pidx+1, self)

    def is_subnode(self, subnode):
        """Check if node is in fact a sub node of this node"""
        while subnode:
            if subnode == self: return True
            subnode = subnode.parent
        return False


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
        #~ return "(%d) "%self.descendants + str(self.content)
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

    
