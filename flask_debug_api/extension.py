import json

from flask import (
    Blueprint, current_app, render_template, url_for, g,
    request, after_this_request, make_response, redirect)
from markupsafe import Markup
try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import JsonLexer
    from pygments.styles import get_style_by_name
    PYGMENT_STYLE = get_style_by_name('colorful')
    HAVE_PYGMENTS = True
except ImportError:
    HAVE_PYGMENTS = False

module = Blueprint('debug-api', __name__, template_folder='templates')
TEMPLATE = 'debug-api/content.html'
METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']


class DebugAPIExtension(object):
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.config.setdefault('DEBUG_API_PREFIX', '/api')
        app.register_blueprint(module, url_prefix='/_debug-api')


@module.route('/route/<api_endpoint>')
def route(api_endpoint):
    path = url_for(api_endpoint, **request.args.to_dict())
    return redirect(url_for('debug-api.browse', path=path[1:]))


@module.route('/browse', defaults={'path': '/'}, methods=METHODS)
@module.route('/browse/<path:path>', methods=METHODS)
def browse(path):
    adapter = g.url_adapter
    g.methods = [method for method in METHODS if adapter.test(path, method)]
    if adapter.test(path, request.method):
        after_this_request(modify_response)
        (endpoint, kwargs) = adapter.match(path)
        view_func = current_app.view_functions[endpoint]
        return view_func(**kwargs)
    return render_template(TEMPLATE, methods=g.methods)


def modify_response(response):
    if response.mimetype == 'application/json':
        data = format_json(response.get_data())
        rendered = render_template(
            TEMPLATE, data=data, methods=g.methods)
        return make_response(rendered)
    return response


def format_json(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8', 'replace')

    data = json.dumps(json.loads(data), indent=2, sort_keys=True)

    if not HAVE_PYGMENTS:
        return Markup('<pre>%s</pre>' % data)

    return Markup(highlight(
        data,
        JsonLexer(),
        HtmlFormatter(noclasses=True, style=PYGMENT_STYLE)))
