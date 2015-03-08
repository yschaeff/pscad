#!/usr/bin/env python3

import curses, re, urwid
from sys import argv

import importer
from Datastruct import Node
from clipboard import Clippy
from undo import Undo

UNDO_CAP = 1000
SPACE_PER_INDENT = 4
HELP_STRING = "yYxXpPgGzZaA *!#%/ dDuUiItTrRsS"

palette = [
    ('default', 'white', ''),
    ('edit', 'black', 'yellow'),
    ('error', 'white', 'dark red'),
    ('error_select', 'white', 'dark magenta'),
    ('select', 'white', 'dark blue'),
    ('status', 'black', 'white'),
    ('bg', 'white', ''),]

exps = [
    re.compile(r"\s*//.*"),                                 ## commment
    re.compile(r"[!#%*\s]*\s*[$\w]+\s*=\s*.+"),             ## assignment
    re.compile(r"[!#%*\s]*\s*\w+\s*\(.*\)\s*"),             ## call
    re.compile(r"[!#%*\s]*\s*function(?:\s+\w+)?\s*\(.*\)\s*=\s*"),  ## func
    re.compile(r"[!#%*\s]*\s*module\s+\w+\s*\([^;\)]*\)"),  ## block
    re.compile(r"[!#%*\s]*\s*include\s+<[\.\w/]+>\s*"),     ## include
    re.compile(r"[!#%*\s]*\s*use\s+<[\.\w/]+>\s*"),         ## use
]

# TODO
# fix fablous for function defs
# tab completion
# contect help 
# think about open new file/load file etc

def is_balanced(text):
    pair = {")":"(", "]":"[", "}":"{"}
    stack = []
    for c in text:
        if c in pair.values():
            stack.append(c)
        elif c in pair.keys():
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

class SelectText(urwid.Widget):
    def __init__(self, node, treelist, buf):
        super(urwid.Widget, self).__init__()
        self.edit = urwid.Edit("", node.content)
        self.text = urwid.Text(node.content)
        # do not wrap
        self.text.set_layout('left', 'clip')
        self.edit.set_layout('left', 'clip')
        key = urwid.connect_signal(self.edit, 'change', SelectText.handler, user_args=[self])
        self.showedit = 0
        self.node = node
        self.treelist = treelist
        self.indent = node.depth()
        self.buf = buf
        self.valid = is_valid(node.content)

    def rows(self, size, focus=False):
        return 1

    def sizing(self):
        if self.showedit:
            return self.edit.sizing()
        return self.text.sizing()

    def selectable(self):
        return True

    def handler(self, widget, newtext):
        self.node.content = newtext.strip()

    def get_cursor_coords(self, size):
        if self.showedit:
            return self.edit.get_cursor_coords(size)
        return None

    def keypress(self, size, key):
        if key == 'enter':
            self.showedit ^= 1
            self._invalidate() # mark widget as changed
            ## update so an undo can be saved
            if self.showedit == 0:
                self.treelist.update()
            return None
            
        if self.showedit:
            return self.edit.keypress(size, key)
            
        ## in Text mode
        if key == 'g':              ## Be siblings parent
            self.node.gobble()
        elif key == 'G':            ## Be childs sibling
            self.node.degobble()
        elif key == 'tab':          ## Be sibling child
            self.node.cling()
        elif key == 'shift tab':    ## Be parents sibling
            self.node.decling()
        elif key == 'P':            ## Be next sibling
            self.node.merge_after(self.buf.load())
        elif key == 'p':            ## Be previous sibling
            self.node.merge_before(self.buf.load())
        elif key == 'Y':            ## Cut node, transfer children to parent
            self.buf.store(self.node.detach())
        elif key == 'y':            ## Cut subtree
            self.buf.store(self.node.split())
        elif key == 'X':            ## Delete node, transfer children to parent
            self.node.detach()
        elif key == 'x':            ## Delete subtree
            self.node.split()
        elif key == '*':
            self.toggle_modifier("*")
        elif key == '!':
            self.toggle_modifier("!")
        elif key == '#':
            self.toggle_modifier("#")
        elif key == '%':
            self.toggle_modifier("%")
        elif key == '/':
            self.toggle_comment()
        elif key == 'd':
            self.node.merge_outer(Node("difference()"))
        elif key == 'D':
            self.node.merge_inner(Node("difference()"))
        elif key == 'u':
            self.node.merge_outer(Node("union()"))
        elif key == 'U':
            self.node.merge_inner(Node("union()"))
        elif key == 'i':
            self.node.merge_outer(Node("intersection()"))
        elif key == 'I':
            self.node.merge_inner(Node("intersection()"))
        elif key == 't':
            self.node.merge_outer(Node("translate([0, 0, 0])"))
        elif key == 'T':
            self.node.merge_inner(Node("translate([0, 0, 0])"))
        elif key == 'r':
            self.node.merge_outer(Node("rotate([0, 0, 0])"))
        elif key == 'R':
            self.node.merge_inner(Node("rotate([0, 0, 0])"))
        elif key == 's':
            self.node.merge_outer(Node("scale([0, 0, 0])"))
        elif key == 'S':
            self.node.merge_inner(Node("scale([0, 0, 0])"))
        elif key == 'a':
            self.node.merge_before(Node("//", True))
        elif key == 'A':
            self.node.merge_after(Node("//", True))
        else:
            return key

        self.treelist.update()
        return None

    def render(self, size, focus=False):
        if self.showedit:
            map2 = urwid.AttrMap(self.edit, 'edit')
        elif focus and self.valid:
            map2 = urwid.AttrMap(self.text, 'select')
        elif focus:
            map2 = urwid.AttrMap(self.text, 'error_select')
        elif not self.valid:
            map2 = urwid.AttrMap(self.text, 'error')
        else:
            map2 = urwid.AttrMap(self.text, 'default')
        return map2.render(size, focus)

    def toggle_modifier(self, char):
        mods = "*!#%"
        if char not in mods:
            return
        t = self.node.content
        for c in t:
            if c not in mods:
                self.node.content = char+t
                return
            elif c == char:
                 self.node.content = t.replace(char, "", 1)
                 return

    def toggle_comment(self):
        t = self.node.content
        if t.startswith("//"):
            self.node.content = t[2:]
        else:
            self.node.content = "//"+t
                 
class TreeListBox(urwid.ListBox):
    def __init__(self, manager, indent_width):
        self.manager = manager
        body = urwid.SimpleFocusListWalker([])
        self.indent = indent_width;
        self.d = 0
        self.update()
        self.buf = Clippy()
        super(TreeListBox, self).__init__(body)

    def update(self):
        self.manager.checkpoint()
        self.update_tree = True
        self._invalidate()

    def render(self, size, focus=False):
        if self.update_tree:
            self.update_tree = False
            tree_text = []
            for node in self.manager.get_tree():
                t = SelectText(node, self, self.buf)
                p = urwid.Padding(t, align='left', width='pack', min_width=None, left=node.depth()*self.indent)
                tree_text.append(p)
            if len(self.body) > 0: 
                pos = self.focus_position
            else:
                pos = 0
            self.body.clear()
            self.body.extend(tree_text)
            if pos < len(self.body):
                self.focus_position = pos
            self.d+=1
        canvas = super(TreeListBox, self).render(size, focus)
        return canvas

    def keypress(self, size, key):
        global status
        key = super(TreeListBox, self).keypress(size, key)
        if key == 'esc':
            for n in self.body:
                w = n._original_widget
                if w.showedit:
                    w.showedit = 0
                    w._invalidate()
            return None
        elif key == 'z':
            if self.manager.undo():
                self.update_tree = True
                self._invalidate()
            return None
        elif key == 'Z':
            if self.manager.redo():
                self.update_tree = True
                self._invalidate()
            return None
        return key

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

class Manager():
    def __init__(self, argv):
        self.undoer = Undo(UNDO_CAP)
        if len(argv) == 1:
            self.tree = Node("Document root")
            self.exportfile = None
        elif len(argv) == 2:
            self.tree = importer.import_scad(argv[1])
            self.exportfile = None
        else:
            self.tree = importer.import_scad(argv[1])
            self.exportfile = argv[2]

    def checkpoint(self, undo=True):
        if undo:
            self.undoer.store(self.tree)
        if self.exportfile:
            if importer.export_scad(self.exportfile, self.tree):
                error("failed to export")

    def undo(self):
        r = self.undoer.undo()
        if r:
            self.tree = r
            self.checkpoint(undo=False)
            return True
        return False
        
    def redo(self):
        r = self.undoer.redo()
        if r:
            self.tree = r
            self.checkpoint(undo=False)
            return True
        return False

    def get_tree(self):
        return self.tree

if __name__ == "__main__":
    status = urwid.Text("")
    helptext = urwid.Text(HELP_STRING)
    footer = urwid.Pile([status, helptext])
    footer_pretty = urwid.AttrMap(footer, 'status')

    manager = Manager(argv)
    tree_list = TreeListBox(manager, SPACE_PER_INDENT)
    body = urwid.AttrMap(tree_list, 'bg')

    frame = urwid.Frame(body, footer=footer_pretty, focus_part='body')

    main = urwid.MainLoop(frame, palette, unhandled_input=show_or_exit)
    main.run()
