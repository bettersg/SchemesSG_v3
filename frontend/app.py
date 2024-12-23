import uuid
from flask import Flask, jsonify, render_template, request, session
import os
import requests
import schemes_model as schemes_model
import flask.json as json
from flask_cors import CORS, cross_origin
from config import config

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

# Load configuration based on environment variable
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

@cross_origin()

@app.route('/')
def root():
	if 'session_id' not in session:
		session['session_id'] = str(uuid.uuid4())

	return render_template('index.html')

@app.route('/index.html')
def index():
	return render_template('index.html')

@app.route('/schemesbank.html')
def schemesbank():
	return render_template('schemesbank.html')

@app.route('/schemespal.html')
def schemespal():
	return render_template('schemespal.html')

@app.route('/schemescase.html')
def schemescase():
	return render_template('schemescase.html')

@app.route('/listing.html')
def listing():
	return render_template('listing.html')

@app.route('/team.html')
def team():
	return render_template('team.html')

@app.route('/update.html')
def update():
	return render_template('update.html')

@app.route('/gotit.html')
def gotit():
	return render_template('gotit.html')

@app.route('/about.html')
def about():
	return render_template('about.html')

@app.route('/blog.html')
def blog():
	return render_template('blog.html')

@app.route('/blog/gapfinder-analysis-of-queries-and-listings.html')
def gapfinder():
	return render_template('gapfinder-analysis-of-queries-and-listings.html')

@app.route('/testing.html')
def test():
	return render_template('testing.html')

@app.route('/chatbot', methods=['POST'])
def send_message():
	data = request.get_json()
	input_text = data.get('data')
	response = requests.post('http://0.0.0.0:8000/chatbot', json={'message': input_text, 'sessionID': session['session_id']})

	return jsonify(response.json())

@app.route('/schemespredict', methods=['get','post'])
def schemes_predict():
	data = request.get_json()
	query = data.get('query')
	relevance = data.get('relevance')
	response = requests.post('http://0.0.0.0:8000/schemespredict', json={'query': query, 'relevance': relevance, 'sessionID': session['session_id']})

	return jsonify(response.json())


if __name__ == '__main__':
	app.secret_key = 'super secret key'
	port = int(os.getenv("PORT",9099))
	app.run(host='0.0.0.0',port=port,debug=True)
