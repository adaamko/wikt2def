import re

HEADER = u"digraph finite_state_machine {\n\tdpi=70;\n\trankdir=TB;\n"
EXCLUDE = ("punct")


def d_clean(string):
    s = string
    for c in '\\=@-,\'".!:;<>/{}[]()#^?':
        s = s.replace(c, '_')
    s = s.replace('$', '_dollars')
    s = s.replace('%', '_percent')
    s = s.replace('|', ' ')
    s = s.replace('*', ' ')
    if s == '#':
        s = '_number'
    keywords = ("graph", "node", "strict", "edge")
    if re.match('^[0-9]', s) or s in keywords:
        s = "X" + s
    return s


def dep_to_dot(deps):
    edges = []
    for sen in deps:
        for dep in sen:
            if dep[0] not in EXCLUDE:
                edges.append((dep[1][0], dep[0], dep[2][0]))

    words = set([e[0] for e in edges] + [e[2] for e in edges])
    lines = []
    for word in words:
        lines.append(u'\t{0} [shape=rectangle, label="{0}"];'.format(
            d_clean(word)))
    for edge in edges:
        dep, dtype, gov = map(d_clean, edge)
        lines.append(u'\t{0} -> {1} [label="{2}"];'.format(dep, gov, dtype))

    dot_str = HEADER
    dot_str += u"\n".join(lines)
    dot_str += "}\n"
    return dot_str
