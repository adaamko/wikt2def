from flask import Flask
app = Flask(__name__)

@app.route('/process_text')
def hello():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(port=5000)