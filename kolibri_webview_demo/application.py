import json
import os
import sqlalchemy
import sys

import gi
gi.require_version('Gtk', '3.0')  # noqa
gi.require_version('WebKit2', '4.0')  # noqa
from gi.repository import GLib, Gio, Gtk, WebKit2

from . import models


class WebViewApi(object):
    def __init__(self):
        from .models import session, Base
        self.session = session
        self.models = Base.classes

    def dispatch(self, payload):
        try:
            func = payload['func']
            kwargs = payload.get('args', {})
            return {
                'callId': payload['callId'],
                'result': getattr(self, func)(**kwargs),
            }
        except Exception as e:
            return {
                'callId': payload['callId'],
                'error': {
                    'message': str(e),
                    'type': e.__class__.__name__,
                }
            }

    def get_metadata(self):
        channelmetadata = self.session.query(self.models.content_channelmetadata).first()
        return {
            'name': channelmetadata.name,
            'description': channelmetadata.description,
        }


class WebView(WebKit2.WebView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.web_view_api = WebViewApi()

        user_content_manager = self.get_user_content_manager()
        user_content_manager.register_script_message_handler('eosKnowledgeLibCall')
        user_content_manager.connect('script-message-received::eosKnowledgeLibCall',
                                     self.resolveWebCall)

        html = GLib.file_get_contents(os.path.dirname(__file__) + '/template/index.html').contents.decode('utf-8')
        self.load_html(html)

    def resolveWebCall(self, manager, js_result):
        payload = json.loads(js_result.get_js_value().to_string())
        response_payload = self.web_view_api.dispatch(payload)
        print(f'EosKnowledgeLib.resolveCall({json.dumps(response_payload)})')

        self.run_javascript(
            f'EosKnowledgeLib.resolveCall({json.dumps(response_payload)})',
            None, None
        )


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        webview = WebView()

        self.add(webview)
        webview.show()


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.endlessm.kolibri_webview_demo", **kwargs)
        self.window = None
        self.session = None

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            models.create_session('sqlite:////home/eor/.kolibri/content/databases/1ceff53605e55bef987d88e0908658c5.sqlite3')
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = AppWindow(application=self, title="Main Window")

        self.window.present()

    def do_command_line(self, command_line):
        self.activate()
        return 0
