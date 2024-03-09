from flask import request, make_response, session
from flask_restful import Resource

# Local imports
from config import app, db, api
# Add your model imports
# from models import 


if __name__ == '__main__':
    app.run(port=5555, debug=True)