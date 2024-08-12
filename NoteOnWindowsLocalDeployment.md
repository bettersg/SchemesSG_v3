# Local Deployment on Windows.

For some reason, pip installing gensim==4.1.2 (for frontend) does not work on windows. To deploy locally on windows, I had to do the following:

```bash
# Backend Installation (from root dir)
cd ./backend
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

uvicorn fast_api.api:app --host 0.0.0.0 --port 8000 #deployment

# Frontend Installation (from root dir)
cd ./frontend
py -m venv venv
venv\Scripts\activate
pip install -r requirements_min.txt #New requirements.txt file with only required dependencies

py app.py #deployment
```

Also I added some jquery files in the `frontend/static` folder cause if not the search button on the frontend does not work.
