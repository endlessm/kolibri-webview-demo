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

import re
import os
import sqlalchemy

from . import utils

ChannelMetadata = None
ContentNode = None
File = None


class WebViewApi(object):
    def __init__(self, main_window):
        self.__main_window = main_window

        global ChannelMetadata, ContentNode, File

        from .models import session, Base
        self.session = session
        self.models = Base.classes

        ChannelMetadata = self.models.content_channelmetadata
        ContentNode = self.models.content_contentnode
        File = self.models.content_file

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
        channel_metadata = self.session.query(ChannelMetadata).one()
        return {
            'id': channel_metadata.id,
            'name': channel_metadata.name,
            'description': channel_metadata.description,
        }

    def set_header_title(self, **kwargs):
        self.__main_window.set_header_title(**kwargs)

    def _content_node_to_json(self, content_node):
        return {
            'id': content_node.id,
            'title': content_node.title,
            'description': content_node.description,
            'kind': content_node.kind,
            'thumbnail_file': None,
            'main_file': None,
            'supplementary_files': [],
            'other_files': [],
        }

    def _file_to_json(self, file):
        filename = utils.get_kolibri_storage_file_path(
            '{id}.{extension}'.format(
                id=file.local_file_id, extension=file.extension
            )
        )
        return {
            'id': file.id,
            'file_uri': 'file://{filename}'.format(filename=filename),
            'ekn_uri': 'ekn:///kolibri/storage/{id}.{extension}'.format(
                id=file.local_file_id, extension=file.extension
            ),
            'preset': file.preset,
            'lang': file.lang_id,
            'file_size': file.file_size,
            'available': os.path.isfile(filename),
        }

    def get_content_node(self, content_node_id):
        content_node = self.session.query(ContentNode) \
            .filter(ContentNode.id == content_node_id) \
            .one()

        result = self._content_node_to_json(content_node)

        files = self.session.query(File) \
            .filter(File.contentnode_id == content_node_id) \
            .order_by(File.priority) \
            .all()

        for file in files:
            if file.thumbnail == 1:
                result['thumbnail_file'] = self._file_to_json(file)
            elif file.supplementary == 1:
                result['supplementary_files'].append(self._file_to_json(file))
            else:
                if result['main_file'] is None:
                    result['main_file'] = self._file_to_json(file)
                else:
                    result['other_files'].append(self._file_to_json(file))

        children = self.session.query(ContentNode) \
            .filter(ContentNode.parent_id == content_node_id) \
            .order_by(ContentNode.sort_order).all()

        result['children'] = list(map(self._content_node_to_json, children))

        return result

    def search(self, query, **kwargs):
        """
        Inspired by the Kolibri search API (`ContentNodeSearchViewset`):

        https://github.com/learningequality/kolibri/blob/develop/kolibri/core/content/api.py
        """
        MAX_RESULTS = 30

        # all words with punctuation removed
        all_words = [w for w in re.split('[?.,!";: ]', query) if w]

        # TODO
        # words in all_words that are not stopwords
        # critical_words = [w for w in all_words if w not in stopwords_set]

        # queries ordered by relevance priority
        all_queries = [
            sqlalchemy.and_(*[ContentNode.title.ilike('%{w}%'.format(w=w)) for w in all_words]),
            # sqlalchemy.and_(*[ContentNode.title.ilike('%{w}%'.format(w=w)) for w in critical_words]),
            sqlalchemy.and_(*[ContentNode.description.ilike('%{w}%'.format(w=w)) for w in all_words]),
            # sqlalchemy.and_(*[ContentNode.description.ilike('%{w}%'.format(w=w)) for w in critical_words]),
        ]

        # # any critical word in title, reverse-sorted by word length
        # for w in sorted(critical_words, key=len, reverse=True):
        #     all_queries.append(Q(title__icontains=w))
        # # any critical word in description, reverse-sorted by word length
        # for w in sorted(critical_words, key=len, reverse=True):
        #     all_queries.append(Q(description__icontains=w))

        content_node_ids = []
        content_ids = set()

        for query in all_queries:
            content_nodes = self.session.query(ContentNode.id, ContentNode.content_id) \
                .filter(~ContentNode.content_id.in_(list(content_ids))) \
                .filter(query) \
                .limit(MAX_RESULTS * 2) \
                .all()

            for content_node in content_nodes:
                if content_node.content_id not in content_ids:
                    content_ids.add(content_node.content_id)
                    content_node_ids.append(content_node.id)
                    if len(content_node_ids) >= MAX_RESULTS:
                        break

            if len(content_node_ids) >= MAX_RESULTS:
                break

        nodes = self.session.query(ContentNode) \
            .filter(ContentNode.id.in_(content_node_ids)) \
            .all()

        return {
            'results': list(map(self._content_node_to_json, nodes)),
        }
