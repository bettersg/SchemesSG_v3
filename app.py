from flask import Flask, jsonify, request, render_template
import os
import schemes_model as schemes_model
import flask.json as json
from flask_cors import CORS, cross_origin
from config import config
from dotenv.main import load_dotenv, find_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

# Load configuration based on environment variable
load_dotenv()
env = os.getenv('FLASK_ENV', 'development')

# TODO: to be moved to database
openai_api_key = os.getenv('OPENAI-API-KEY')
openai_api_type = os.getenv('OPENAI-API-TYPE')
openai_api_version = os.getenv('OPENAI-API-VERSION')
openai_endpoint = os.getenv('OPENAI-ENDPOINT')
deployment_name = os.getenv('DEPLOYMENT-NAME')
model_name = os.getenv('MODEL-NAME')

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

# TODO: incorrectly retains state across multiple clients. Look into RunnableWithMessageHistory
@app.route('/chatbot', methods=['POST'])
def get_data():
	input = request.get_json().get('data')

	llm = AzureChatOpenAI(deployment_name=deployment_name, azure_endpoint=openai_endpoint, openai_api_version=openai_api_version, openai_api_key=openai_api_key, openai_api_type=openai_api_type, model_name=model_name)
	memory = ConversationSummaryBufferMemory(llm=llm, max_token_limit=100) 

	try:
		conversation = ConversationChain(llm=llm, memory=memory, verbose=True)
		output = conversation.predict(input=input)
		memory.save_context({"input": input}, {"output": output})
		return jsonify({"response":True, "message":output})
	except Exception as e:
		print(e)
		error_message = f'Error: {str(e)}'
		return jsonify({"response": False, "message": error_message})

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
