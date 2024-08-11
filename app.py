from flask import Flask, render_template
import os
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

# @app.route('/schemespredict', methods=['get','post'])
# def schemes_predict():
# 	result = 'nil'
# 	try:
# 		input = request.get_json()
# 		query = input['query']
# 		relevance = int(input['relevance'])
# 		result = schemes_model.search_similar_schemes(query, relevance)
# 	except Exception as e:
# 		print('Error: ',e)
# 	return result

if __name__ == '__main__':
	port = int(os.getenv("PORT",9099))
	app.run(host='0.0.0.0',port=port,debug=True)
