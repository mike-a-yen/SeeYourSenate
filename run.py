from app import application
import os


PORT = int(os.environ.get('PORT',5000))
application.run(host='0.0.0.0',port=PORT,debug=True)
