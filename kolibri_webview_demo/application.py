import json
import logging
import os
import re
import sqlalchemy
import sys

# from django.conf import settings

from gi.repository import GLib, Gio, Gtk, WebKit2

from .models import create_session
from .web_view_api import WebViewApi
from . import utils

logger = logging.getLogger(__name__)


class WebView(WebKit2.WebView):
    def __init__(self, *args, **kwargs):
        web_context = WebKit2.WebContext()
        web_context.get_security_manager().register_uri_scheme_as_local('ekn')
        web_context.register_uri_scheme('ekn', self.load_ekn_uri)

        super().__init__(*args, web_context=web_context, **kwargs)

        self.web_view_api = WebViewApi()

        user_content_manager = self.get_user_content_manager()
        user_content_manager.register_script_message_handler('eosKnowledgeLibCall')
        user_content_manager.connect('script-message-received::eosKnowledgeLibCall',
                                     self.resolveWebCall)

        web_settings = self.get_settings()
        web_settings.set_enable_developer_extras(True)
        web_settings.set_enable_write_console_messages_to_stdout(True)
        web_settings.set_javascript_can_access_clipboard(True)

        html = GLib.file_get_contents(os.path.dirname(__file__) + '/template/index.html').contents.decode('utf-8')
        self.load_html(html, 'ekn://home')

    def resolveWebCall(self, manager, js_result):
        payload = json.loads(js_result.get_js_value().to_string())
        response_payload = self.web_view_api.dispatch(payload)

        self.run_javascript(
            f'EosKnowledgeLib.resolveCall({json.dumps(response_payload)})',
            None, None
        )

    def load_ekn_uri(self, req):
        match = re.match(r'^\/kolibri\/storage\/([a-zA-Z0-9\.]+)$', req.get_path())
        if match:
            file_path = utils.get_kolibri_storage_file_path(match.group(1))
            file = Gio.File.new_for_path(file_path)
            if file.query_exists():
                content_type = file.query_info(
                    Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                    Gio.FileQueryInfoFlags.NONE, None).get_content_type()
                print(file_path, content_type)
                req.finish(file.read(), -1, content_type)


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, default_width=720, default_height=640)

        webview = WebView()

        self.add(webview)
        webview.show()


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.endlessm.kolibri_webview_demo",
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.window = None
        self.channel_id = None

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.window:
            gvfs.init()

            database_path = os.path.join(
                utils.KOLIBRI_DATA_DIR, 'content', 'databases',
                f'{self.channel_id}.sqlite3')
            create_session(database_path)

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
