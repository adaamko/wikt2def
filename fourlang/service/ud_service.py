import inspect
import argparse
from flask import Flask
from flask import request
from flask import jsonify
from fourlang.service.parser_wrapper import ParserWrapper

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

            if len(sentence.split()) == 1:
                h = dep[0].text
                d = dep[2].text
            else:
                h = dep[0].lemma if dep[0].lemma is not None else dep[0].text
                d = dep[2].lemma if dep[2].lemma is not None else dep[2].text

            curr_dep.append([h, dep[0].index])
            curr_dep.append([d, dep[2].index])

            dep_list.append(curr_dep)
        sen_deps.append(dep_list)
    ret_value = {"deps": sen_deps}

    return jsonify(ret_value)


@app.route('/lemmatize', methods=['POST'])
def lemmatize():
    r = request.json
    sentence = r['text']
    doc = wrapper.nlp(sentence)
    lemmas = []
    words = []
    for sens in doc.sentences:
        for token in sens.tokens:
            words.append(token.text)
            current_lemma = []
            for word in token.words:
                if word.index in token.index.split('-'):
                    current_lemma += [word.lemma if word.lemma is not None else word.text]
            lemmas.append(current_lemma)

    ret_value = {"lemmas": lemmas, "words": words}

    return jsonify(ret_value)


@app.route("/lemmatize_word", methods=['POST'])
def lemmatize_word():
    r = request.json
    sentence = r['word']
    doc = wrapper.nlp(sentence)
    lemma = ""
    for sens in doc.sentences:
        for word in sens.words:
            lemma = " ".join([lemma, word.lemma])

    ret_value = {"lemma": lemma.strip()}

    return jsonify(ret_value)


def main(language, port_to_run):
    wrapper.set_parser(language)
    app.run(port=port_to_run)


if __name__ == '__main__':
    main(args.lang[0], args.port[0])
