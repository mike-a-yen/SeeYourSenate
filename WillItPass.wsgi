import sys
import os

sys.path.insert(0, "/var/www/html/WillItPass")

# virtualenv
activate_env=os.path.expanduser("~/html/WillItPass/pass-env/bin/activate_this.py")
with open(activate_env) as f:
     exec(f.read(), dict(__file__=activate_env))


from app import app as application