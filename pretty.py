import curses

def addstr(win, y, x, text, style=0):
    my, mx = win.getmaxyx()
    if y < 0 or y >= my or x >= mx or x+len(text) <= 0:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    if x+len(text) >= mx:
        text[:mx-x]
    win.addstr(y, x, text, style)

def splitargs(s):
    p1 = s.find('(')
    p2 = s.rfind(')')
    p3 = s.find('=')
    if p1 == -1 or p2 == -1 or (p3 != -1 and p3 < p1):
        return s, None
    else:
        return s[:p1].strip(), s[p1+1:p2]

def fabulous(win, y, x, mx, s):
    color_default = curses.color_pair(0)
    color_name    = curses.color_pair(0)|curses.A_BOLD
    color_braces  = curses.color_pair(4)|curses.A_BOLD
    color_keyword = curses.color_pair(5)|curses.A_BOLD
    color_comment = curses.color_pair(6)

    #~ keywords = ["function", "include", "module", "use"]
    #~ tran = ["translate", "rotate", "scale", "resize"]
    #~ bops = ["union", "difference", "intersection"]
    #~ objs = ["function", "include", "module", "use"]

    args = None
    keyword = None
    name = None

    if s.startswith("//"):
        addstr(win, y, x, s, color_comment)
        return
    s, args = splitargs(s)
    if args == None:
        addstr(win, y, x, s, color_default)
        return
    p = 0
    l = s.find(" ")
    if l != -1:
        keyword = s[:l]
        addstr(win, y, x, keyword, color_keyword)
        p += len(keyword)+1
        name = s[l:].strip()
    else:
        name = s

    addstr(win, y, x+p, name, color_name)
    p+=len(name)
    if args != None:
        addstr(win, y, x+p, "(", color_braces)
        p+=1
        addstr(win, y, x+p, "%s"%args, color_default)
        p+=len(args)
        addstr(win, y, x+p, ")", color_braces)

