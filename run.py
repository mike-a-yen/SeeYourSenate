print('In run')
from app import app
print('In run: imported app')
import os


if __name__ == '__main__':
    print('In if statement')
    PORT = int(os.environ.get('PORT',5000))
    print('Running on port',PORT)
    app.run(host='0.0.0.0',port=PORT,debug=True)
