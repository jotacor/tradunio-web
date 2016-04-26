#!flask/bin/python
from app import create_app
import os
from werkzeug.contrib.profiler import ProfilerMiddleware

app = create_app(os.getenv('TRADUNIO_ENV') or 'default')

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
app.run(debug=True)
