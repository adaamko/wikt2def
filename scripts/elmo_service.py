import argparse
import os
from flask import Flask
from flask import request
from flask import jsonify
from elmoformanylangs import Embedder

parser = argparse.ArgumentParser(description="Service to generate embeddings in a given language")
parser.add_argument("-p", "--port", help="set port for the service", default=1666, type=int)

args = parser.parse_args()

app = Flask(__name__)


@app.route('/<language>', methods=['POST'])
def elmo(language):
    if language not in languages:
        raise AttributeError("Required language not in list: {}".format(languages.keys()))
    r = request.json
    sentences = [sent.split(' ') for sent in r['sentences']]
    if languages[language] is None:
        languages[language] = Embedder(os.path.join(os.path.dirname(os.path.abspath(__file__)), paths[language]))
    result = languages[language].sents2elmo(sentences)
    return jsonify({"embeddings": [r.tolist() for r in result]})


if __name__ == "__main__":
    languages = {"en": None, "it": None, "de": None}
    paths = {"en": '../ELMo/en/144/', "it": '../ELMo/it/159/', "de": '../ELMo/de/142/'}
    app.run(port=args.port)

