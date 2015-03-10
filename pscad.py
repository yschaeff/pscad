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
NEW_LINE_CONTENT = ""

palette = [
    #~ ('default', 'white', ''), #bgs
    ## selections
    ('edit', 'white,underline', ''),
    ('edit_select', 'white,underline', 'dark blue'),
    ('error', 'white', 'dark red'),
    ('error_select', 'white', 'dark magenta'),
    ('select', 'white', 'dark blue'),
    ## misc
    ('status', 'white,standout', 'black'),
    ('bg', 'white', ''),
    ## text
    ('comment', 'dark cyan', ''),
    ('modifier', 'brown,bold', ''),
    ('var', 'white', ''),
    ('=', 'dark red', ''),
    ('stat', 'default', ''),
    ('name', 'default,bold', ''),
    ('keyword', 'dark blue,bold', ''),
    ]

rp = re.compile(r"^\s*$")
rc = re.compile(r"(\s*//.*$)")
ra = re.compile(r"([!#%*\s]*\s*)([$\w]+\s*)(=\s*)(.+$)")
rb = re.compile(r"([!#%*\s]*\s*)(\w+\s*)(\()(.*)(\)\s*$)")
rf = re.compile(r"([!#%*\s]*\s*)(function)((?:\s+\w+)?\s*)(\()(.*)(\)\s*)(=\s*)(.*$)")
rm = re.compile(r"([!#%*\s]*\s*)(module\s+)(\w+\s*)(\()([^;\)]*)(\)\s*$)")
ri = re.compile(r"([!#%*\s]*\s*)(include\s+)(<)([\.\w/]+)(>\s*$)")
ru = re.compile(r"([!#%*\s]*\s*)(use\s+)(<)([\.\w/]+)(>\s*$)")

exps = {
    rp: None,
    rc: ['comment'],
    ra: ['modifier', 'var', '=', 'stat'],
    rb: ['modifier', 'name', '=', 'stat', '='],
    rf: ['modifier', 'keyword', 'name', '=', 'stat', '=', '=', 'stat'],
    rm: ['modifier', 'keyword', 'name', '=', 'stat', '='],
    ri: ['modifier', 'keyword', '=', 'stat', '='],
    ru: ['modifier', 'keyword', '=', 'stat', '=']
}

# TODO
# commandline help
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
    for e in exps.keys():
        if e.match(text):
            return True
    return False

class ColorText(urwid.Text):
    global exps
    def set_text(self, input_text):
        text = input_text
        for r,c in exps.items():
            m = r.match(input_text)
            if not m: continue
            if not c: break
            text = []
            for i,g in enumerate(m.groups()):
                if g: text.append((c[i], g))
            break
        return super(ColorText, self).set_text(text)
    
    def render(self, size, focus=False):
        if focus:
            text = [('select', self.text)]
            w = urwid.Text(text)
            w.set_layout('left', 'clip')
            return w.render(size, focus)
        return super(ColorText, self).render(size, focus)
        
class SelectText(urwid.Widget):
    def __init__(self, node, treelist, buf):
        super(urwid.Widget, self).__init__()
        self.edit = urwid.Edit("", node.content)
        self.text = ColorText(node.content)
        self.text.set_layout('left', 'clip') # do not wrap
        self.edit.set_layout('left', 'clip')
        key = urwid.connect_signal(self.edit, 'change',
            SelectText.handler, user_args=[self])
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
        # in case we don't rebuild tree:
        self.text.set_text(self.node.content)

    def reset(self):
        if self.showedit:
            self.showedit = 0
            self._invalidate()

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
            self.node.merge_before(Node(NEW_LINE_CONTENT, True))
        elif key == 'A':
            self.node.merge_after(Node(NEW_LINE_CONTENT, True))
        else:
            return key

        self.treelist.update()
        return None

    def render(self, size, focus=False):
        if self.showedit:
            map2 = urwid.AttrMap(self.edit, 'edit', 'edit_select')
        elif self.valid:
            map2 = urwid.AttrMap(self.text, 'default', 'select')
        else:
            map2 = urwid.AttrMap(self.text, 'error', 'error_select')
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
        canvas = super(TreeListBox, self).render(size, focus)
        return canvas

    def keypress(self, size, key):
        key = super(TreeListBox, self).keypress(size, key)
        manager.status(".")
        if key == 'esc':
            [n._original_widget.reset() for n in self.body]
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
        elif key == 'w':
            ## TODO if no outfile display new window ask for path
            ## then set outfile. Else just write.
            ## on W always ask path
            if self.manager.write():
                manager.saved = True
                manager.status("File written")
            else:
                manager.status("Error writing file, no output file set?")
            return None
        elif key == 'q':
            if self.manager.saved:
                raise urwid.ExitMainLoop()
            else:
                manager.status("Unsaved document, use Q to force quit.")
            return None
        return key

def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

class Manager():
    def __init__(self, infile, outfile, status_text):
        self.undoer = Undo(UNDO_CAP)
        self.saved = False
        self.status_text = status_text
        self.infile = infile
        self.exportfile = outfile
        self.autosave = (outfile != None)
        self.tree = importer.import_scad(infile)

    def status(self, text):
        self.status_text.set_text(text)

    def write(self):
        if self.exportfile:
            if not importer.export_scad(self.exportfile, self.tree):
                return True
        else:
            if not importer.export_scad(self.infile, self.tree):
                return True
        return False

    def checkpoint(self, undo=True):
        if undo:
            self.undoer.store(self.tree)
        if self.autosave:
            if self.write():
                self.saved = True
            else:
                error("failed to export")
        else:
            self.saved = False

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

def handle_commandline():
    import argparse
    parser = argparse.ArgumentParser(
            description="Python OpenSCAD thingy",
            epilog="Yuri Schaeffer - MIT License")
    parser.add_argument('infile', metavar='IN_FILE', 
            help="File to read")
    parser.add_argument('-o', '--outfile', metavar='OUT_FILE',
            default=None,
            help="File to keep up to date")
    return parser.parse_args()

if __name__ == "__main__":
    ##parse cmdline
    args = handle_commandline()
    #~ print(a)

    status = urwid.Text("")
    helptext = urwid.Text(HELP_STRING)
    footer = urwid.Pile([status, helptext])
    footer_pretty = urwid.AttrMap(footer, 'status')

    manager = Manager(args.infile, args.outfile, status)
    tree_list = TreeListBox(manager, SPACE_PER_INDENT)
    body = urwid.AttrMap(tree_list, 'bg')

    frame = urwid.Frame(body, footer=footer_pretty, focus_part='body')

    main = urwid.MainLoop(frame, palette, unhandled_input=show_or_exit)
    main.run()
