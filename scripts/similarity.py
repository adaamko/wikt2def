import re


def clear_node(node):
    return re.sub(r'_[0-9]*', '', node)


def asim_jac_edges(graph_hypothesis, graph_premise):
    hyp = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)])
    pre = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
    sim = hyp & pre
    if not sim or len(hyp) == 0:
        return 0
    else:
        return float(len(sim)) / len(hyp)


def asim_jac_nodes(graph_hypothesis, graph_premise):
    hyp = set([clear_node(node) for node in graph_hypothesis.G.nodes])
    pre = set([clear_node(node) for node in graph_premise.G.nodes])
    sim = hyp & pre
    if not sim or len(hyp) == 0:
        return 0
    else:
        return float(len(sim)) / len(hyp)
