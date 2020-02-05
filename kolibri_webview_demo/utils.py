# Copyright © 2019 Endless Mobile, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import os

from gi.repository import GLib

KOLIBRI_DATA_DIR = os.environ.get('KOLIBRI_HOME')

if KOLIBRI_DATA_DIR:
    KOLIBRI_DATA_DIR = os.path.expanduser(KOLIBRI_DATA_DIR)
else:
    KOLIBRI_DATA_DIR = os.path.join(GLib.get_home_dir(), '.kolibri')


def get_kolibri_storage_file_path(filename):
    return os.path.join(
        KOLIBRI_DATA_DIR, 'content', 'storage',
        filename[0], filename[1], filename)
