from copy import deepcopy


class Node():
    def __init__(self, content, encapsulate=False):
        self.parent = None
        self.children = []
        self.descendants = 0
        if encapsulate:
            self.content = "root"
            n = Node(content)
            self.children = [n]
            n.parent = self
        else:
            self.content = content

    def depth(self):
        """depth in tree of this node. root is at depth 0"""
        if not self.parent:
            return 0
        return self.parent.depth()+1

    def fix_descendants(self):
        """The number of descendants"""
        d = sum([c.fix_descendants() for c in self.children])
        d += len(self.children)
        self.descendants = d
        return self.descendants

    def merge(self, index, source):
        if not source:
            return
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

    def merge_before(self, source):
        if not source:
            return
        if self.parent:
            i = self.parent.children.index(self)
            self.parent.merge(i, source)
        else:
            self.merge(0, source)

    def merge_after(self, source):
        if not source:
            return
        if self.parent:
            i = self.parent.children.index(self)+1
            self.parent.merge(i, source)
        else:
            self.merge(0, source)

    def merge_outer(self, source):
        if not source or not self.parent:
            return
        source.children.append(self)
        source.parent = self.parent
        i = self.parent.children.index(self)
        self.parent.children[i] = source
        source.descendants = self.descendants+1
        self.parent = source
        p = source.parent
        while p:
            p.descendants += 1
            p = p.parent

    def merge_inner(self, source):
        if not source:
            return
        source.children = self.children
        self.children = [source]
        for c in source.children:
            c.parent = source
        source.parent = self
        source.descendants = self.descendants
        p = self
        while p:
            p.descendants += 1
            p = p.parent

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

    def subtree(self):
        root = Node("Root")
        if self.parent != None:
            root.children.append(self)
            root.descendants = self.descendants + 1
            ## leave self.parent unresolved
        return root

    def copy_solo(self):
        root = Node("Root")
        node = Node(self.content)
        if self.parent != None:
            root.children.append(node)
            root.descendants = 1
            node.parent = root
            node.descendants = 0
            node.children = []
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

    def depth_first_walk(self):
        if self.children:
            return self.children[0]
        elif not self.parent:
            return self
        return self.parent.rnext(self)

    def __iter__(self):
        self.__start_iter = True
        self.iter_index = self
        return self

    def __next__(self):
        if self.__start_iter:
            self.__start_iter = False
            return self.iter_index
        n = self.iter_index.depth_first_walk()
        if n and n != self.iter_index:
            self.iter_index = n
            return n
        raise StopIteration
