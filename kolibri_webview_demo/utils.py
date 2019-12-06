import os

from gi.repository import GLib

KOLIBRI_DATA_DIR = os.environ.get('KOLIBRI_DATA_DIR')

if KOLIBRI_DATA_DIR:
    KOLIBRI_DATA_DIR = os.path.expanduser(KOLIBRI_DATA_DIR)
else:
    KOLIBRI_DATA_DIR = os.path.join(GLib.get_home_dir(), '.kolibri')


def get_kolibri_storage_file_path(filename):
    return os.path.join(
        KOLIBRI_DATA_DIR, 'content', 'storage',
        filename[0], filename[1], filename)
