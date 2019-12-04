import json
import logging
import os
import sqlalchemy
import sys

import gi
gi.require_version('Gtk', '3.0')  # noqa
gi.require_version('WebKit2', '4.0')  # noqa
from gi.repository import GLib, Gio, Gtk, WebKit2

from . import models

logger = logging.getLogger(__name__)

KOLIBRI_DATA_DIR = os.environ.get('KOLIBRI_DATA_DIR')

if KOLIBRI_DATA_DIR:
    KOLIBRI_DATA_DIR = os.path.expanduser(KOLIBRI_DATA_DIR)
else:
    KOLIBRI_DATA_DIR = os.path.join(GLib.get_home_dir(), '.kolibri')


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
        super().__init__(*args, application_id="org.endlessm.kolibri_webview_demo",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.window = None
        self.session = None
        self.channel_id = None

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            database_path = os.path.join(KOLIBRI_DATA_DIR, 'content', 'databases', f'{self.channel_id}.sqlite3')
            models.create_session(database_path)
            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.window = AppWindow(application=self, title="Main Window")

        self.window.present()

    def do_command_line(self, command_line):
        arguments = command_line.get_arguments()
        if len(arguments) == 1:
            logger.error('Missing channel_id')
            return 1

        self.channel_id = arguments[1]
        self.activate()
        return 0
