#!/usr/bin/env python

import curses
from Datastruct import Node
import importer
from copy import deepcopy
from undo import Undo

UNDO_CAP = 100
F_STAT_CLEAR  = 0
F_STAT_UNDO   = 1
F_STAT_EXPORT = 2

# TODO
# Fix comments
# output on every change
# colors
# key_end

def usage(win):
    helptext = "yYxXpPgGuU tab/stab (in) [dui trs]"
    my, mx = win.getmaxyx()
    win.addnstr(my-2, mx-len(helptext)-1, " ", mx-1)
    win.addnstr(my-2, mx-len(helptext), helptext, mx-1, curses.A_REVERSE)

def status(win, text=None):
    global status_string

    if "status_string" not in globals():
        status_string = ""
    
    if text:
        status_string = text
    my, mx = win.getmaxyx()
    win.move(my-1, 0)
    win.clrtoeol()
    win.addnstr(my-1, 0, status_string, mx-1, curses.A_REVERSE)

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
    win.addnstr(my-2, 0, text, mx-1, curses.A_REVERSE)

def render(node, pwin, sel_node, y=0, x=0):
    highlight = 0
    INDENT = 4
    my, mx = pwin.getmaxyx()

    if node == sel_node:
        highlight = curses.A_BOLD|curses.color_pair(3)
    pwin.addnstr(y, x, " "*mx, mx-x-1, highlight)
    pwin.addnstr(y, x, str(node), mx-x-1, highlight)

    h = 1;
    for child in node.children:
        if y+h+1 > my:
            break
        ch = render(child, pwin, sel_node, y+h, x+INDENT)
        for j in range(ch):
            pwin.addnstr(y+h+j, x, " "*INDENT, mx-x-1, highlight)
        h += ch
    return h

def paste_before(sel_node, buffer, stdscr):
    if not buffer:
        status(stdscr, "Could not paste buffer empty")
    elif not sel_node:
        status(stdscr, "no target")
    elif sel_node.parent:
        i = sel_node.parent.children.index(sel_node)
        root = deepcopy(buffer)
        sel_node.parent.merge(i, root)

def paste_after(sel_node, buffer, stdscr):
    if not buffer:
        status(stdscr, "Could not paste buffer empty")
    elif not sel_node:
        status(stdscr, "no target")
    elif sel_node.parent:
        i = sel_node.parent.children.index(sel_node)+1
        root = deepcopy(buffer)
        sel_node.parent.merge(i, root)


def main(stdscr):
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    buffer = None
    undo = Undo(UNDO_CAP)

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
            scroll -= y/2
            scroll = max(0, scroll)
        elif sel_idx-scroll >= y-1:
            scroll += y/2
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
        if c == ord('n'):
            #make child of selected node
            curses.echo()
            s = stdscr.getstr(10,0, 15)
            curses.noecho()
            node = Node(s)
            stdscr.addnstr(10,0, " "*15, 15)
            if not tree or not sel_node:
                tree = node
                sel_node = node
            else:
                sel_node.add_child(0, node)
                sel_node = node
                
        elif c == ord('i'): #import
            fn = '/home/yuri/Documents/headphone/headphon0.scad'
            tree = importer.import_scad(fn)
            changes = F_STAT_EXPORT|F_STAT_UNDO
            sel_node = tree
            status(stdscr, "imported file %s"%(fn))
        elif c == ord('e'): #export
            r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)
            #todo disp error
            #~ if r!=0: exit(r)

        elif c == ord('q'): #quit
            break
            
        elif c == ord('Y'):
            if sel_node:
                i = tree.offset(sel_node)
                buffer = sel_node.split()
                sel_node = tree.node_at_offset(i)
                status(stdscr, "Yanked subtree")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('y'):
            if sel_node:
                i = tree.offset(sel_node)
                buffer = sel_node.detach()
                sel_node = tree.node_at_offset(i)
                status(stdscr, "Yanked node")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('X'):
            if sel_node:
                i = tree.offset(sel_node)
                _ = sel_node.split()
                sel_node = tree.node_at_offset(i)
                status(stdscr, "Cut subtree")
                changes = F_STAT_EXPORT|F_STAT_UNDO
                
        elif c == ord('x'):
            if sel_node:
                i = tree.offset(sel_node)
                _ = sel_node.detach()
                sel_node = tree.node_at_offset(i)
                status(stdscr, "Cut node")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('g'): #gobble
            if sel_node:
                sel_node.gobble()
                status(stdscr, "Gobbled node")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('G'): #degobble
            if sel_node:
                sel_node.degobble()
                status(stdscr, "Degobbled node")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('\t'): #cling
            if sel_node:
                sel_node.cling()
                status(stdscr, "Clinged node")
                changes = F_STAT_EXPORT|F_STAT_UNDO
                    
        elif c == curses.KEY_BTAB: #decling
            if sel_node:
                sel_node.decling()
                status(stdscr, "Declinged node")
                changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('P'):
            paste_before(sel_node, buffer, stdscr)
            changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('p'):
            paste_after(sel_node, buffer, stdscr)
            changes = F_STAT_EXPORT|F_STAT_UNDO

        elif c == ord('U'):
            r = undo.redo()
            if r:
                tree = r
                sel_node = tree
                changes = F_STAT_EXPORT

        elif c == ord('u'):
            r = undo.undo()
            if r:
                tree = r
                sel_node = tree
                changes = F_STAT_EXPORT

        elif c == curses.KEY_UP:
            if sel_node:
                sel_node = sel_node.prev()

        elif c == curses.KEY_DOWN:
            if sel_node:
                sel_node = sel_node.next()

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

        elif c == curses.KEY_HOME:
            sel_node = tree

        if changes|F_STAT_UNDO:
            undo.store(tree)
        if changes|F_STAT_EXPORT:
            r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)            

def debug_print_tree(tree, i=0):
    print "  "*i + str(tree)
    for c in tree.children:
         debug_print_tree(c, i+1)
         
curses.wrapper(main)
#~ tree = importer.import_scad('/home/yuri/Documents/headphone/headphon0.scad')
#~ debug_print_tree(tree)
#~ r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)
