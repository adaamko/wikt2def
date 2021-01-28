from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source

import sys
import json
import datetime
import traceback
import json
import graphviz
import stanza
from flask import Flask
from flask import request
from networkx.readwrite import json_graph

HOST = 'localhost'
PORT = 5006
app = Flask(__name__)

nlp = stanza.Pipeline('en')
text_to_4lang_en = TextTo4lang(lang="en")

# echo '0 Die Gebäudehöhe darf 6,5 m nicht überschreiten.' | python brise_nlp/plandok/get_attributes.py
def visualize(parsed):
    dot = graphviz.Digraph()
    dot.node("0", "ROOT", shape="box")
    for sentence in parsed.sentences:
        for token in sentence.tokens:
            for word in token.words:
                dot.node(str(word.id), word.text)
                dot.edge(str(word.head), str(word.id),
                         label=word.deprel)
    return dot


@app.route('/build', methods=['POST'])
def build():
    ret_value = {"result": {"errors": None, "graph": None, "ud": None}}
    data = request.get_json()

    if len(data) == 0 or not data["text"]:
        print("No input text found")
        ret_value["result"]["errors"] = "No input text found"
        sys.stdout.flush()
        return json.dumps(ret_value)

    print("Text to process: {0}".format(data))

    try:
        text = data["text"]
        method = data["method"]
        depth = data["depth"]
        irtg_graph = text_to_4lang_en.process_text(text, method=method, depth=int(depth), filt=False, black_or_white="")
        sen = nlp(text).sentences[0]
        ret_value["result"]["ud"] = visualize(sen).source
        if irtg_graph:
            ret_value["result"]["graph"] = irtg_graph.to_dot()
    except Exception as e:
        traceback.print_exc()
        ret_value["result"]["errors"] = str(e)

    print("Returning: {0}".format(ret_value))
    sys.stdout.flush()
    return json.dumps(ret_value)


@app.route('/get_definition', methods=['POST'])
def get_definition():
    ret_value = {"result": {"errors": None, "def": None}}
    data = request.get_json()

    if len(data) == 0 or not data["text"]:
        print("No input text found")
        ret_value["result"]["errors"] = "No input text found"
        sys.stdout.flush()
        return json.dumps(ret_value)

    print("Text to process: {0}".format(data))

    try:
        text = data["text"]
        definition = text_to_4lang_en.get_definition(text)

        if definition:
            ret_value["result"]["def"] = definition
    except Exception as e:
        traceback.print_exc()
        ret_value["result"]["errors"] = str(e)

    print("Returning: {0}".format(ret_value))
    sys.stdout.flush()
    return json.dumps(ret_value)


if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
