from main import app, SSLCherootAdapter
from bottle import run
from multiprocessing import Process
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import time
import ssl

# Create a retry object in case bottle is slow to start our server
retry = Retry(total=5, backoff_factor=0.3)


def run_app():
    run(app=app, host="0.0.0.0", port=8443, server=SSLCherootAdapter)


def setup_module(module):
    module.proc = Process(target=run_app)
    module.proc.start()


def teardown_module(module):
    module.proc.terminate()


def test_json_whoami():
    s = requests.Session()
    s.verify = "cacert.pem"
    s.mount("https://", HTTPAdapter(max_retries=retry))
    resp = s.get("https://localhost:8443/whoami")
    assert "application/json" in resp.headers["content-type"]
    assert resp.json() == {"d": None}


# Our code implicitly relies on ssl.create_default_context being available, as
# cheroot's builtin ssl module won't create the ssl context without it.
def test_ssl_default_context():
    assert hasattr(ssl, "create_default_context")


# Purpose of this test:
#  - Not logged in by default
#  - The log in mechanism works
#  - After logging in, whoami returns the correct user (eg. session working)
#  - After logging out, user is actually logged out
def test_whoami():
    s = requests.Session()
    s.verify = "cacert.pem"
    s.mount("https://", HTTPAdapter(max_retries=retry))
    who = s.get("https://localhost:8443/whoami").json()
    assert who == {"d": None}

    creds = {"UserName": "BottleUser", "Password": "iambottle"}
    login = s.post("https://localhost:8443/login", data=creds)
    assert login.status_code == 200

    who = s.get("https://localhost:8443/whoami").json()
    assert who == {"d": "BottleUser"}

    logout = s.post("https://localhost:8443/logout")
    assert logout.status_code == 200

    who = s.get("https://localhost:8443/whoami").json()
    assert who == {"d": None}
