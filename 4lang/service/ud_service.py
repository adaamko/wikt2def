from flask import Flask
from flask import request
from flask import jsonify
import stanfordnlp
import inspect

stanfordnlp.download('de', confirm_if_exists=True)
nlp = stanfordnlp.Pipeline(lang="de")

app = Flask(__name__)

@app.route('/parse', methods=['POST'])
def parse():
    r = request.json
    sentence = r['text']
    doc = nlp(sentence)
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
        sens_deps.append(dep_list)
    ret_value = {"deps": sen_deps}

    return jsonify(ret_value)

if __name__ == '__main__':
    app.run(port=5005)
