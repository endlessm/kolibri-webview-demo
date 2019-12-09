import os

from . import utils

ChannelMetadata = None
ContentNode = None
File = None


class WebViewApi(object):
    def __init__(self):
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
        filename = utils.get_kolibri_storage_file_path(f'{file.local_file_id}.{file.extension}')
        return {
            'id': file.id,
            'file_uri': f'file://{filename}',
            'ekn_uri': f'ekn:///kolibri/storage/{file.local_file_id}.{file.extension}',
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
