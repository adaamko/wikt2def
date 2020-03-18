import pandas as pd
from graphviz import Source


def read_output(file_path, threshold=1.0, what_to_write="FP"):
    print("premise\thypothesis\tpredicted\tgold")
    df = pd.read_csv(file_path, delimiter="\t", header=None, names=["premise", "hypothesis", "predicted", "gold"])
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for row in df.iterrows():
        premise = row[1].premise
        hypothesis = row[1].hypothesis
        predicted = float(row[1].predicted)
        gold = float(row[1].gold)
        if (predicted >= threshold)*1 != gold and gold == 0.0:
            if what_to_write.upper() == "FP":
                print("{}\t{}\t{}\t{}".format(premise, hypothesis, predicted, gold))
            fp += 1
        elif (predicted >= threshold)*1 != gold and gold == 1.0:
            if what_to_write.upper() == "FN":
                print("{}\t{}\t{}\t{}".format(premise, hypothesis, predicted, gold))
            fn += 1
        elif (predicted >= threshold)*1 == gold and gold == 1.0:
            if what_to_write.upper() == "TP":
                print("{}\t{}\t{}\t{}".format(premise, hypothesis, predicted, gold))
            tp += 1
        elif (predicted >= threshold)*1 == gold and gold == 0.0:
            if what_to_write.upper() == "TN":
                print("{}\t{}\t{}\t{}".format(premise, hypothesis, predicted, gold))
            tn += 1
    print("tp: {}\ttn: {}\tfp: {}\tfn: {}".format(tp, tn, fp, fn))
    precision = tp/(tp+fp)
    recall = tp/(tp+fn)
    f1 = 2 * (precision * recall) / (precision + recall)
    print("precision: {}\trecall: {}\tf1: {}".format(precision, recall, f1))


def compare_graphs(graph_premise, graph_hypothesis):
    hyp_nodes = set(graph_hypothesis.get_nodes())
    prem_nodes = set(graph_premise.get_nodes())
    marked_nodes = hyp_nodes & prem_nodes
    dot_graph_premise = graph_premise.to_dot(marked_nodes)
    dot_graph_hypothesis = graph_hypothesis.to_dot(marked_nodes)
    return Source(dot_graph_premise), Source(dot_graph_hypothesis)
