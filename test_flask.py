from flask import Flask

app = Flask(__name__)
app.debug = True
app.config['PROPAGATE_EXCEPTIONS'] = True

@app.route("/")
def hello():
    return "Hello from Flask!"

if __name__ == "__main__":
    app.run(port=8004)