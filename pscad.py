#!/usr/bin/env python

import curses
from Datastruct import Node
import importer
from copy import deepcopy

# TODO
# Hide document root and make it always present
# Fix comments
# output on every change
# colors
# undo/redo
# key_end
#sel node must be one with closest index

def usage(win):
    helptext = "yYxXpP (in) [dui trs]"
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

def main(stdscr):
    curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
    buffer = None

    tree = Node("Document root")
    sel_node = tree
    scroll = 0
    stdscr.refresh()
    while 1:
        print_buffer(stdscr, buffer)
        usage(stdscr)
        status(stdscr)

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
        pad.refresh(0+scroll,0, 0,0, y-3, x-1)
        if tree_h-scroll < y:
            pad = curses.newpad(y-(tree_h-scroll), x)
            pad.refresh(0,0, (tree_h-scroll),0, y-3, x-1)
        #~ status(stdscr, "%d %d %d"%(tree_h, scroll, y))
        
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
                buffer, sel_node = sel_node.split()
            else:
                status(stdscr, "No selection, could not yank")
        elif c == ord('y'):
            if sel_node:
                if not sel_node.parent:
                    status(stdscr, "You are not allowed the yank the root")
                else:
                    buffer = sel_node
                    q = sel_node.depth_first_walk()
                    if q:
                        sel_node = q
                    else:
                        sel_node = sel_node.prev()
                    i = buffer.parent.children.index(buffer)

                    buffer.parent.children.remove(buffer)
                    buffer.children.reverse()
                    for child in buffer.children:
                        buffer.parent.add_child(i, child)
                        child.parent = buffer.parent
                    buffer.children = []
        elif c == ord('X'):
            if sel_node:
                _, sel_node = sel_node.split()
            else:
                status(stdscr, "No selection, could not cut")
        elif c == ord('x'):
            if sel_node:
                t_buffer = sel_node
                if not sel_node.parent:
                    status(stdscr, "Could not cut: no selection")
                else:
                    q = sel_node.depth_first_walk()
                    if q:
                        sel_node = q
                    else:
                        sel_node = sel_node.prev()
                    i = t_buffer.parent.children.index(t_buffer)

                    t_buffer.parent.children.remove(t_buffer)
                    t_buffer.children.reverse()
                    for child in t_buffer.children:
                        t_buffer.parent.add_child(i, child)
                        child.parent = t_buffer.parent
                    t_buffer.children = []
                    t_buffer = None
        elif c == ord('P'):
            if not buffer:
                status(stdscr, "Could not paste buffer empty")
            elif not sel_node:
                status(stdscr, "no target")
            i = 0
            if sel_node != tree:
                i = sel_node.parent.children.index(sel_node)
            root = deepcopy(buffer)
            sel_node = sel_node.merge(i, root)
        elif c == ord('p'):
            if not buffer:
                status(stdscr, "Could not paste buffer empty")
            elif not sel_node:
                status(stdscr, "no target")
            i = len(sel_node.children)
            if sel_node != tree:
                i = sel_node.parent.children.index(sel_node)+1
            root = deepcopy(buffer)
            sel_node = sel_node.merge(i, root)
        elif c == curses.KEY_UP:
            if sel_node:
                sel_node = sel_node.prev()
        elif c == curses.KEY_DOWN:
            if sel_node:
                sel_node = sel_node.next()
        elif c == curses.KEY_HOME:
            sel_node = tree

curses.wrapper(main)
#~ 
#~ tree = importer.import_scad('/home/yuri/Documents/headphone/headphon0.scad')
#~ r = importer.export_scad('/home/yuri/Documents/pscad/temp.scad', tree)
