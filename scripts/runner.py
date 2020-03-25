from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source
from scripts.parse_data import read_sherliic, build_graph
from scripts.similarity import Similarity
from tqdm import tqdm

preds = []
text_to_4lang = TextTo4lang(lang="en")
df = read_sherliic("../../sherliic/dev.csv", "../../sherliic/relation_index.tsv", keep_context=True, just_ab=True)
data_frame = build_graph(df)
lexicon = Lexicon(lang="en")
similarity = Similarity(with_embedding=False)

with open("nodes_2_sherliic.txt", "w") as f:
    for index in tqdm(range(len(data_frame))):
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]
        score = data_frame.score[index]
        graph_premise = text_to_4lang.process_deps(premise, method="expand", depth=2, blacklist=["in", "on", "of"])
        graph_hypothesis = text_to_4lang.process_deps(hypothesis, method="expand", depth=1, blacklist=["in", "on", "of"])
        pred = similarity.asim_jac_edges(graph_premise, graph_hypothesis)

        Source(graph_premise.to_dot()).render('nodes_2_sherliic/{}_{}_premise.gv'.format(
            "-".join(df.premise[index].split(" ")), "-".join(df.hypothesis[index].split(" "))))
        Source(graph_hypothesis.to_dot()).render('nodes_2_sherliic/{}_{}_hypothesis.gv'.format(
            "-".join(df.premise[index].split(" ")), "-".join(df.hypothesis[index].split(" "))))

        f.write("{} {} {}\t{} {} {}\t{}\t{}\n".format(
            df.prem_argleft[index], df.premise[index], df.prem_argright[index],
            df.hypo_argleft[index], df.hypothesis[index], df.hypo_argright[index], pred, score))

