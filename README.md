[![Build Status](https://travis-ci.org/nickbabcock/bottle-ssl.svg?branch=master)](https://travis-ci.org/nickbabcock/bottle-ssl)

# bottle-ssl

This repo contains a sample web app that demonstrates a secure login mechanism
for linux users using SSL on top of Bottle. The authentication mechanism
requires the app to be ran as root on a linux system, but this is just for
demonstration purposes. Other than authentication, the code is cross platform
and python 2 and 3 compatible. See the [Docker instructions](#docker) if you
want to try out the sample app.

## Introduction

[Bottle][bottle] is a great micro web framework that can be as minimalist or
feature rich as one wants. Bottle is great for rapid development and for
debugging. However, Bottle is not recommended to be deployed in production
without additional plugins, as it lacks security [and speed][serverOptions].
The developers of Bottle know this and so made Bottle easily extendible.

A common want in web programming is having a secure login page and to remember
the logged in user. This cannot be achieved without extending Bottle through
various plugins. This project starts a web page that'll allow a user to log in
over TLS 1.2 (other protocols are disabled) using their name and password on a
linux server and remember the user through the use of a cookie.

## Requirements:

- Python 2.7.9, 3.4, or later. Minimum requirement to run Bottle and friends.
- [Bottle][bottle]: This will be the web framework that will have everything based on it.
- [CherryPy][cherrypy] (now cheroot): Bottle can't achieve SSL or heavy
  traffic, so this is where CherryPy comes in. Since CherryPy is based on
  cheroot, we'll be using cheroot directly.
- [Beaker][beaker]: Will be used as Bottle middleware that allows session data.
- [OpenSSL][openssl]: Program used to generate the self signed certificate.

Before you [`poetry install`](https://github.com/sdispater/poetry) the python
dependencies you will need to install Openssl (most likely with the command
`sudo apt-get install openssl`)

## OpenSSL and Self Signed Certificates

First the SSL certificate and private key are generated using OpenSSL. It is
absolutely critical to generate a private key with at least 1024 bits
(recommended: 2048/4096) else you'll run into security or other issues (eg.
[Internet Explorer will not display the page no matter what if there are less
than 1024 bits][1024bit]).  The generated files, in this case are privkey.pem and
cacert.pem. For simplicity's sake, these are stored inside the directory.

```bash
openssl req -new -x509 -days 1095 -nodes -newkey rsa:2048 -out cacert.pem -keyout privkey.pem
```

## Bottle and SSL

My recommendation is to not use get bogged down in working with the builtin
servers that bottle recognizes, as sorting out dependencies can be a pain.
Instead craft your own bottle adapter with cheroot:

```python
from bottle import ServerAdapter, run

class SSLCherootAdapter(ServerAdapter):
    def run(self, handler):
        from cheroot import wsgi
        from cheroot.ssl.builtin import BuiltinSSLAdapter
        import ssl

        server = wsgi.Server((self.host, self.port), handler)
        server.ssl_adapter = BuiltinSSLAdapter("cacert.pem", "privkey.pem")

        # By default, the server will allow negotiations with extremely old protocols
        # that are susceptible to attacks, so we only allow TLSv1.2
        server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1
        server.ssl_adapter.context.options |= ssl.OP_NO_TLSv1_1

        try:
            server.start()
        finally:
            server.stop()

run(host='localhost', port=8080, server=SSLCherootAdapter)
```

## Alternatives

If creating your own adapter is too burdensome, run the app with
[gunicorn](http://gunicorn.org/) (one will need to slightly change the code to
return an app). Gunicorn will bring the speed and the ssl, so one could get
rid of CherryPy (cheroot). I definitely recommend checking out gunicorn for a
middle of the road solution.

For a heavyweight solution run nginx, apache, HAProxy in front of bottle.

## Testing SSL Configuration

[sslyze](https://github.com/nabla-c0d3/sslyze) will run a suite of checks on a
given site and report back which protocols, cipher suites, and vulnerabilities
are available.

## Docker

Included in this repo is a Dockerfile that spins up a bottle app using a self
signed certificate and demonstrates authentication. Since this is a sample app,
it's not uploaded to the registry but if you already have `docker`, building
the container is quite straightforward:

```bash
cd bottle-ssl
docker build -t nickbabcock/bottle-ssl .
docker run -ti -p 9443:443 nickbabcock/bottle-ssl
```

Then navigate your browser to port 9443 of the docker machine. For the
username, enter `BottleUser` and for the password `iambottle`

[bottle]: http://bottlepy.org/
[cherrypy]: http://cherrypy.org/
[beaker]: http://beaker.readthedocs.org/en/latest/
[pyopenssl]: https://launchpad.net/pyopenssl
[openssl]: http://openssl.org/
[serverOptions]: http://bottlepy.org/docs/dev/deployment.html#server-options
[1024bit]: http://technet.microsoft.com/en-us/security/advisory/2661254
