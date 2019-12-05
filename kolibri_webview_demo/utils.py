from gi.repository import GLib


def get_kolibri_storage_file_path(filename):
    return f'{GLib.get_home_dir()}/.kolibri/content/storage/{filename[0]}/{filename[1]}/{filename}'
