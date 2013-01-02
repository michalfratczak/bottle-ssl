"""
A simple example of using bottle to achieve an HTTPS login using Linux to
verify username and password.
"""

from bottle import *
from beaker.middleware import SessionMiddleware
import json
import crypt
import spwd
import pwd

@route('/<filename:path>')
def send_static(filename):
  return static_file(filename, root=".")

@route('/whoami')
def whoami():
  response.content_type = 'application/json; charset=utf-8'
  try:
    username = current_user()
  except:
    username = None 
  finally:
    return json.dumps({ "d" : username })

@route('/')
def default():
  redirect("/index.html")

@route('/login', method='POST')
def login():
  name = request.forms.UserName
  passwd = request.forms.Password

  #if the username does not appear in the password
  #file, then a KeyError is thrown
  try:
    crypted = pwd.getpwnam(name)[1]
  except KeyError:
    redirect('/index.html')

  #use shadow password if needed
  if crypted and (crypted == 'x' or crypted == '*'):
    crypted = spwd.getspnam(name)[1]

  if crypt.crypt(passwd, crypted) == crypted:
    session = beakerSession()
    session['username'] = name 

  redirect('/index.html')

@route('/logout', method='POST')
def logout():
  session = beakerSession()
  session.delete()

def beakerSession():
  return request.environ.get('beaker.session')

def current_user():
  session = beakerSession()
  username = session.get('username', None);
  if username is None:
    raise AuthException("Unauthenticated user")
  return username


#Create our own sub-class of Bottle's ServerAdapter
#so that we can specify SSL. Using just server='cherrypy'
#uses the default cherrypy server, which doesn't use SSL
class SSLCherryPyServer(ServerAdapter):
  def run(self, handler): 
    from cherrypy import wsgiserver
    server = wsgiserver.CherryPyWSGIServer((self.host, self.port), handler)
    server.ssl_certificate = "cacert.pem"
    server.ssl_private_key = "privkey.pem"
    try:
      server.start()
    finally:
      server.stop()

#define beaker options
#-Each session data is stored inside a file located inside a 
# folder called data that is relative to the working directory
#-The cookie expires at the end of the browser session
#-The session will save itself when accessed during a request
# so save() method doesn't need to be called
session_opts = {
  'session.type': 'file',
  'session.cookie_expires': True,
  'session.data_dir': './data',
  'session.auto': True
}

#Create the default bottle app and then wrap it around
#a beaker middleware and send it back to bottle to run
app = default_app()
myapp = SessionMiddleware(app, session_opts)
run(app=myapp, host='0.0.0.0', port=443, server=SSLCherryPyServer)
