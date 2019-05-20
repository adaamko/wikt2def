import inspect
import argparse
from flask import Flask
from flask import request
from flask import jsonify
from parser_wrapper import ParserWrapper

parser = argparse.ArgumentParser(description = "")
parser.add_argument("-p", "--port", required=True, nargs="+", help="set port for the service", default=5005, type=int)
parser.add_argument("-l", "--lang", required=True, nargs="+", help="set the parser's language", default="en")

wrapper = ParserWrapper()
args = parser.parse_args()

app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse():
    r = request.json
    sentence = r['text']
    doc = wrapper.nlp(sentence)
    deps = doc.sentences[0].dependencies
    sen_deps = []
    for sens in doc.sentences:
        deps = sens.dependencies
        dep_list = []
        for dep in deps:
            curr_dep = []
            curr_dep.append(dep[1])

            h = dep[0].lemma if dep[0].lemma is not None else dep[0].text
            d = dep[2].lemma if dep[2].lemma is not None else dep[2].text

            curr_dep.append([h, dep[0].index])
            curr_dep.append([d, dep[2].index])

            dep_list.append(curr_dep)
        sen_deps.append(dep_list)
    ret_value = {"deps": sen_deps}

    return jsonify(ret_value)


def main(language, port_to_run):
    wrapper.set_parser(language)
    app.run(port=port_to_run)

if __name__ == '__main__':
    main(args.lang[0], args.port[0])
