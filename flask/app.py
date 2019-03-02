from flask import Flask, request, jsonify,render_template

app = Flask(__name__)

# @app.route('/', methods = ['GET','POST'])
# def index():
#     #value = request.json['key']
#     #result = "result"
#     data = request.get_json()
#     name = data['name']
#     location = data['location']

#     return jsonify({'Result': 'Success!', 'name': name,'location': location})

@app.route('/')
def index():
    


@app.route('/update', methods = ['POST'])
def update():
    return render_template('index.html')
