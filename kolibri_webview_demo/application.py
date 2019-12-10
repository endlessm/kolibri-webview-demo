import json
import logging
import os
import re
import sqlalchemy
import sys
import zipfile

from gi.repository import GLib, Gio, Gtk, WebKit2

from .models import create_session
from .web_view_api import WebViewApi
from . import utils

logger = logging.getLogger(__name__)

APPLICATION_NAME = "Kolibri WebView Demo"


class WebView(WebKit2.WebView):
    def __init__(self, main_window, *args, **kwargs):
        web_context = WebKit2.WebContext()
        web_context.get_security_manager().register_uri_scheme_as_local('ekn')
        web_context.register_uri_scheme('ekn', self.load_ekn_uri)

        super().__init__(*args, web_context=web_context, **kwargs)

        self.web_view_api = WebViewApi(main_window)

        user_content_manager = self.get_user_content_manager()
        user_content_manager.register_script_message_handler('eosKnowledgeLibCall')
        user_content_manager.connect('script-message-received::eosKnowledgeLibCall',
                                     self.resolve_web_call)

        web_settings = self.get_settings()
        web_settings.set_enable_developer_extras(True)
        web_settings.set_enable_write_console_messages_to_stdout(True)
        web_settings.set_javascript_can_access_clipboard(True)

        html = GLib.file_get_contents(
            os.path.join(os.path.dirname(__file__), 'data/template/index.html')
        ).contents.decode('utf-8')
        self.load_html(html, 'ekn://home')

    def resolve_web_call(self, manager, js_result):
        payload = json.loads(js_result.get_js_value().to_string())
        response_payload = self.web_view_api.dispatch(payload)

        self.run_javascript(
            'EosKnowledgeLib.resolveCall({json})'.format(json=json.dumps(response_payload)),
            None, None)

    def update_search(self, query):
        self.run_javascript(
            'window.dispatchEvent(new CustomEvent(\'ekn-update-search\', {\n' +
            '    detail: {\n' +
            '        query: \'{query}\',\n'.format(query=query) +
            '    },\n' +
            '}));',
            None, None)

    def go_back(self):
        pass

    def go_forward(self):
        pass

    def go_home(self):
        self.run_javascript(
            'window.dispatchEvent(new CustomEvent(\'ekn-go-home\'));',
            None, None)

    def load_ekn_uri(self, req):
        match = re.match(
            r'^\/kolibri\/storage\/([a-zA-Z0-9\.]+)([a-zA-Z0-9\.\/]+)?$',
            req.get_path())
        if match:
            file_path = utils.get_kolibri_storage_file_path(match.group(1))
            file = Gio.File.new_for_path(file_path)
            if file.query_exists():
                print('load_ekn_uri', req.get_path(), file_path, match.group(1), match.group(2))
                if os.path.splitext(match.group(1))[1] == '.zip':
                    with zipfile.ZipFile(file_path) as zfile:
                        zfile_member = 'index.html'
                        if match.group(2) is not None:
                            # TODO: Load relative HTML5 files
                            # zfile_member = match.group(2).strip('/')
                            pass

                        input_stream = Gio.MemoryInputStream.new_from_bytes(
                            GLib.Bytes(zfile.read(zfile_member)))
                        req.finish(input_stream, -1, 'text/html')
                else:
                    content_type = file.query_info(
                        Gio.FILE_ATTRIBUTE_STANDARD_CONTENT_TYPE,
                        Gio.FileQueryInfoFlags.NONE, None).get_content_type()
                    req.finish(file.read(), -1, content_type)


class MainWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'MainWindow'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, default_width=900, default_height=700)

        builder = Gtk.Builder.new_from_file(
            os.path.join(os.path.dirname(__file__), 'data/ui/mainwindow.ui')
        )
        builder.connect_signals(self)

        self.header_bar = builder.get_object('header_bar')
        self.set_titlebar(self.header_bar)
        self.set_title(APPLICATION_NAME)

        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.main_vbox)
        self.main_vbox.show()

        self.search_bar = builder.get_object('search_bar')
        self.main_vbox.pack_start(self.search_bar, False, False, 0)
        self.search_bar.show()

        self.search_button = builder.get_object('button_search')
        self.search_entry = builder.get_object('search_entry')

        self.webview = WebView(self)
        self.main_vbox.pack_end(self.webview, True, True, 0)
        self.webview.show()

    def toggle_search(self):
        toggled = self.search_button.get_active()
        self.search_button.set_active(not toggled)

    def on_search_entry_search_changed(self, search_entry):
        self.webview.update_search(search_entry.get_text())

    def on_button_go_back_clicked(self, *args):
        self.webview.go_back()

    def on_button_go_forward_clicked(self, *args):
        self.webview.go_forward()

    def on_button_go_home_clicked(self, *args):
        self.webview.go_home()

    def on_button_search_toggled(self, *args):
        toggled = self.search_button.get_active()
        self.search_bar.set_reveal_child(toggled)
        self.search_entry.set_text('')
        if toggled:
            self.search_entry.grab_focus()
    
    def on_search_entry_stop_search(self, *args):
        self.search_button.set_active(False)

    def set_header_title(self, title, subtitle=None):
        if not title:
            title = APPLICATION_NAME
            subtitle = None
        self.header_bar.set_title(title)
        self.header_bar.set_subtitle(subtitle)


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id='com.endlessm.KolibriWebViewDemo',
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE, **kwargs)
        self.main_window = None
        self.channel_id = None

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.on_quit_action_activate)
        self.add_action(quit_action)
        self.set_accels_for_action('app.quit', ['<Primary>q'])

        search_action = Gio.SimpleAction.new('search', None)
        search_action.connect('activate', self.on_search_action_activate)
        self.add_action(search_action)
        self.set_accels_for_action('app.search', ['<Primary>f'])

    def do_activate(self):
        # We only allow a single window and raise any existing ones
        if not self.main_window:
            # gvfs.init()

            database_path = os.path.join(
                utils.KOLIBRI_DATA_DIR,
                'content/databases/{id}.sqlite3'.format(id=self.channel_id)
            )
            create_session(database_path)

            # Windows are associated with the application
            # when the last one is closed the application shuts down
            self.main_window = MainWindow(application=self)

        self.main_window.present()

    def do_command_line(self, command_line):
        arguments = command_line.get_arguments()
        if len(arguments) == 1:
            logger.error('Missing channel_id')
            return 1

        self.channel_id = arguments[1]
        self.activate()
        return 0

    def on_quit_action_activate(self, action, param):
        self.quit()

    def on_search_action_activate(self, action, param):
        if self.main_window:
            self.main_window.toggle_search()
