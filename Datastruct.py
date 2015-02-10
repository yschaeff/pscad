import curses

class Node():
    def __init__(self, content):
        self.content = content
        self.parent = None
        self.children = []
        
    def add_child(self, index, node):
        node.parent = self
        self.children.insert(index, node)

    def push_child(self, node):
        node.parent = self
        self.children.append(node)

    def __str__(self):
        #~ if self.parent:
            #~ return str(self.content)+"-"+self.parent.content
        #~ else:
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

    #~ def idxr(self, child):
        #~ i = self.children.index(child)+1
        #~ if not self.parent:
            #~ return i
        #~ else:
            #~ return i+self.parent.idxr(self)
            #~ 
    #~ def tree_index(self):
        #~ if not self.parent:
            #~ return 0
        #~ else:
            #~ return self.parent.idxr(self)
