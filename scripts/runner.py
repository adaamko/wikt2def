from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source
from scripts.parse_data import read_sherliic
from scripts.similarity import Similarity
from tqdm import tqdm

preds = []
text_to_4lang = TextTo4lang(lang="en")
data_frame = read_sherliic("../../sherliic/dev.csv")
lexicon = Lexicon(lang="en")
similarity = Similarity(with_embedding=False)

with open("nodes_3_sherliic.txt", "w") as f:
    for i in tqdm(range(len(data_frame))):
        index = i
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]
        score = data_frame.score[index]
        graph_premise = text_to_4lang.process_text(premise, expand=True, depth=3, blacklist=["in", "on", "of"])
        graph_hypothesis = text_to_4lang.process_text(hypothesis, expand=True, depth=1, blacklist=["in", "on", "of"])
        pred = similarity.asim_jac_nodes(graph_premise, graph_hypothesis)
        Source(graph_premise.to_dot()).render('nodes_3_sherliic/{}_{}_premise.gv'.format(premise, hypothesis))
        Source(graph_hypothesis.to_dot()).render('nodes_3_sherliic/{}_{}_hypothesis.gv'.format(premise, hypothesis))

        f.write("{}\t{}\t{}\t{}\n".format(premise, hypothesis, pred, score))

