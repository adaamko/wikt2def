from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source

import sys
import json
import datetime
import traceback
import json
from flask import Flask
from flask import request
from networkx.readwrite import json_graph

HOST = 'localhost'
PORT = 5006
app = Flask(__name__)

text_to_4lang_en = TextTo4lang(lang="en")


@app.route('/build', methods=['POST'])
def build():
    ret_value = {"result": {"errors": None, "graph": None}}
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
        irtg_graph = text_to_4lang_en.process_text(text, method=method, depth=int(depth), filt=True, black_or_white="black")

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
