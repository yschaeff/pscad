#!/usr/bin/env python3

import curses
import urwid
from Datastruct import Node
import importer
from copy import deepcopy
from undo import Undo
from pretty import fabulous, addstr
from sys import argv

UNDO_CAP = 100
# TODO
# hotkeys for diff etc
# fix fablous for function defs

def print_buffer(win, buffer):
    if not buffer:
        text = "Buffer empty"
    else:
        #~ buffer = buffer.children[0]
        if buffer.children:
            text = "Buffer: %s {...}" % str(buffer) 
        else:
            text = "Buffer: " + str(buffer)
    
    my, mx = win.getmaxyx()
    win.move(my-2, 0)
    win.clrtoeol()
    addstr(win, my-2, 0, text, curses.A_REVERSE)

def paste_before(sel_node, buffer, stdscr):
    if not buffer:
        status(stdscr, "Could not paste buffer empty")
    elif not sel_node:
        status(stdscr, "no target")
    elif sel_node.parent:
        i = sel_node.parent.children.index(sel_node)
        root = deepcopy(buffer)
        sel_node.parent.merge(i, root)
    else:
        root = deepcopy(buffer)
        sel_node.merge(0, root)

def paste_after(sel_node, buffer, stdscr):
    if not buffer:
        status(stdscr, "Could not paste buffer empty")
    elif not sel_node:
        status(stdscr, "no target")
    elif sel_node.parent:
        i = sel_node.parent.children.index(sel_node)+1
        root = deepcopy(buffer)
        sel_node.parent.merge(i, root)
    else:
        root = deepcopy(buffer)
        sel_node.merge(0, root)

def main(stdscr, infile=None, outfile=None):
    init_colors()
    buffer = None
    undo = Undo(UNDO_CAP)

    if infile:
        tree = importer.import_scad(infile)
        if not tree:
            raise(Exception("Error importing from file %s"%infile))
    else:
        tree = Node("Document root")
    undo.store(tree)
    sel_node = tree
    scroll = 0
    stdscr.refresh()
    while 1:
        y,x = stdscr.getmaxyx()
        sel_idx = tree.offset(sel_node)
        tree_h = tree.descendants + 1
        sel_h = sel_node.descendants + 1
        pad = curses.newpad(tree_h, x)
        render(tree, pad, sel_node)
        if sel_idx < scroll:
            while sel_idx < scroll:
                scroll -= (y//2)
            scroll = max(0, scroll)
        elif sel_idx-scroll >= y-2:
            while sel_idx-scroll >= y-2:
                scroll += y//2
        elif (sel_idx-scroll)+sel_h > y and sel_h<y:
            d = (sel_idx-scroll+sel_h+1) - y
            scroll += d

        # paint screen
        pad.refresh(0+scroll,0, 0,0, y-3, x-1)
        # clear unpainted screen
        if tree_h-scroll < y:
            stdscr.move(tree_h-scroll, 0)
            stdscr.clrtobot()

        print_buffer(stdscr, buffer)
        usage(stdscr)
        status(stdscr)

        changes = F_STAT_CLEAR

        c = stdscr.getch()
        if c == ord('i'): #import
            fn = '/home/yuri/Documents/pscad/headphon0.scad'
            t = importer.import_scad(fn)
            if not t:
                status(stdscr, "Error importing file %s"%(fn))
            else:
                tree = t
                changes = F_STAT_EXPORT|F_STAT_UNDO
                sel_node = tree
                status(stdscr, "imported file %s"%(fn))
        elif c == ord('e'): #export
            r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)
        elif c == ord('P'):
            paste_before(sel_node, buffer, stdscr)
            changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('p'):
            paste_after(sel_node, buffer, stdscr)
            changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == curses.KEY_SLEFT:
            if sel_node and sel_node.parent:
                pidx = sel_node.parent.children.index(sel_node)
                if pidx > 0:
                    sel_node = sel_node.parent.children[pidx-1]

        elif c == curses.KEY_SRIGHT:
            if sel_node and sel_node.parent:
                pidx = sel_node.parent.children.index(sel_node)
                if pidx < len(sel_node.parent.children)-1:
                    sel_node = sel_node.parent.children[pidx+1]

        elif c == curses.KEY_RIGHT:
            if sel_node and sel_node.children:
                sel_node = sel_node.children[0]

        elif c == curses.KEY_LEFT:
            if sel_node and sel_node.parent:
                sel_node = sel_node.parent

        if changes & F_STAT_UNDO:
            undo.store(tree)
        if changes & F_STAT_EXPORT and outfile:
            r = importer.export_scad(outfile, tree)

def debug_print_tree(tree, i=0):
    print("  "*i + "< "+str(tree)+" >")
    for c in tree.children:
         debug_print_tree(c, i+1)

            
if 0 and __name__ == "__main__":
    import traceback, sys
    if len(argv) == 1:
        curses.wrapper(main)
    if len(argv) == 3:
        try:
            curses.wrapper(main, argv[1], argv[2])
        except:
            #~ tree = importer.import_scad2(argv[1])
            #~ if tree: debug_print_tree(tree)
            print()
            print(traceback.print_exc(file=sys.stdout))
    if len(argv) == 2:
            tree = importer.import_scad(argv[1])
            if tree: debug_print_tree(tree)


def show_or_exit(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    
class SelectText(urwid.Widget):

    def __init__(self, node, treelist):
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

    def rows(self, size, focus=False):
        return 1

    def sizing(self):
        if self.showedit:
            return self.edit.sizing()
        return self.text.sizing()

    def selectable(self):
        return True

    def handler(self, widget, newtext):
        ## TODO VALIDATE CONTENT, BRIGHT RED ON ERROR
        self.text.set_text(newtext)

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
        if key == 'g':
            self.node.gobble()
        elif key == 'G':
            self.node.degobble()
        elif key == 'tab':
            self.node.cling()
        elif key == 'shift tab':
            self.node.decling()
        elif key == 'y':
            self.node.detach()
        elif key == 'Y':
            self.node.split()
        elif key == 'x':
            self.node.detach()
        elif key == 'X':
            self.node.split()
        elif key == '*':
            self.toggle_modifier("*")
        elif key == '!':
            self.toggle_modifier("!")
        elif key == '#':
            self.toggle_modifier("#")
        elif key == '%':
            self.toggle_modifier("%")
        else:
            return key

        self.treelist.update()
        return None

    def render(self, size, focus=False):
        if self.showedit:
            map2 = urwid.AttrMap(self.edit, 'edit')
        elif focus:
            map2 = urwid.AttrMap(self.text, 'select')
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
                 
class TreeListBox(urwid.ListBox):
    def __init__(self, tree, indent_width):
        self.tree = tree
        body = urwid.SimpleFocusListWalker([])
        self.indent = indent_width;
        self.undo = Undo(UNDO_CAP)
        self.d = 0
        self.update()
        super(TreeListBox, self).__init__(body)

    def update(self):
        global status
        self.undo.store(self.tree)
        self.update_tree = True
        self._invalidate()
        status.set_text("%d undo len %d index %d"%(self.d, len(self.undo.undo_history), self.undo.undo_index))

    def render(self, size, focus=False):
        if self.update_tree:
            self.update_tree = False
            tree_text = []
            for node in self.tree:
                t = SelectText(node, self)
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
        elif key == 'u':
            r = self.undo.undo()
            if r:
                self.tree = r
                self.update_tree = True
                self._invalidate()
                status.set_text("%d undo len %d index %d"%(self.d, len(self.undo.undo_history), self.undo.undo_index))
            return None
        elif key == 'U':
            r = self.undo.redo()
            if r:
                self.tree = r
                self.update_tree = True
                self._invalidate()
                status.set_text("%d undo len %d index %d"%(self.d, len(self.undo.undo_history), self.undo.undo_index))
            return None
        return key

palette = [
    ('default', 'white', ''),
    ('edit', 'black', 'yellow'),
    ('error', 'white', 'dark red'),
    ('select', 'white', 'dark blue'),
    ('status', 'black', 'white'),
    ('bg', 'white', ''),]
    
SPACE_PER_INDENT = 4

status = urwid.Text("Status line")
helptext = urwid.Text("yYxXpPgGuU *!#% (in) [dui trs]")
footer = urwid.Pile([status, helptext])
footer_pretty = urwid.AttrMap(footer, 'status')

tree = importer.import_scad(argv[1])
tree_list = TreeListBox(tree, SPACE_PER_INDENT)
body = urwid.AttrMap(tree_list, 'bg')

frame = urwid.Frame(body, footer=footer_pretty, focus_part='body')

main = urwid.MainLoop(frame, palette, unhandled_input=show_or_exit)
main.run()
