# nirit/api.py
""" Nirit API """
import logging
from django.conf import settings
from nirit.models import Building, Notice
from nirit.manager import ModelManager
from nirit.utils import build_notice_card

logger = logging.getLogger('nirit.api')


class NoticeAPI(object):
    """
    The Notice API.
    Provides programmatic access to the Data Manager, allowing view and manipulation of Notices.

    """
    
    def get(self, object_code, start=0, replies_only=False):
        """
        Provides GET access to Notices and their replies.

        @param  object_code:    The Building Codename or Notice ID.
        @type   object_code:    string

        @param  start:          The index from which to return results for.
                                By default, the results contains the first N notices or replies,
                                where N is defined in 'nirit.settings.BOARD_NOTICES'.
        @type   start:          number
    
        @param  replies_only:   Specifies whether the result should only contain the replies.
        @type   replies_only:   boolean

        @return:                A dictionary of native Python objects, compatible with the JSON format.
        @rtype:                 dict

        """
        data = {'code': '403', 'status': 'Forbidden'}
        try:
            # is a specific Notice requested?
            notice = Notice.objects.get(pk=object_code)
        except (Notice.DoesNotExist, ValueError):
            # either the notice does not exist, or a Building listing was requested.
            # is the Building Board requested?
            try:
                building = Building.objects.get(codename=object_code)
            except Building.DoesNotExist:
                # the Building does not exist, or it is the Notice that doesn't
                # either way, there is no result, so we return a 404 error
                data['code'], data['status'] = 404, 'Not Found'
            else:
                # if we reached this point, a Building listing was requested,
                # we return a ranged list, using the start parameter as the starting point.
                # e.g.: if range = 6, return replies from 7 to 7 + settings.BOARD_NOTICES
                start = start if start else 0
                data['code'], data['status'] = 200, 'OK'
                cards = building.notices.filter(is_reply=False).order_by('-created')
                data['cards_count'] = cards.count()
                data['cards'] = []
                for card in cards[int(start):int(start)+settings.BOARD_NOTICES]:
                    data['cards'].append(build_notice_card(card, mimetype='json'))
        else:
            # if we reached this point, a specific Notice was requested
            data['code'], data['status'] = 200, 'OK'
            data['id'] = notice.id
            notice_data = build_notice_card(notice, mimetype='json')
            if replies_only:
                # we are only interested in the replies
                replies = notice.get_replies()
                data['replies_count'] = replies.count()
                data['replies'] = []
                # the range is used as the starting point
                # e.g.: if range = 2, return replies from 3 to 12 (if settings.BOARD_NOTICES = 10)
                start = start if start else 0
                for reply in replies[int(start):int(start)+settings.BOARD_NOTICES]:
                    reply_data = build_notice_card(reply, mimetype='json')
                    data['replies'].append(reply_data)
            else:
                # we want the full notice object
                data.update(notice_data)
                data['type'] = notice.get_type_display()
                data['subject'] = notice.subject
                data['replies'] = notice.get_replies().count()
        return data

    def post(self, subject=None, sender=None, buildings=None, nid=None, is_official=False):
        """
        Provides POST access to editing and sending Notices.

        @param  subject:        The notice or reply subject line.
        @type   subject:        string
    
        @param  sender:         The sender's username.
        @type   sender:         string

        @param  buildings:      A coma-separated list of Building codenames. Used as the recipient Building for any new Notice.
        @type   buildings:      string

        @param  nid:            When no None, the notice ID to reply to.
        @type   nid:            integer

        @param  is_official:    Whether the post is official or not (1: yes, 0:no)
        @type   is_official:    boolean

        @return:                An object representing the response status
        @rtype:                 dict

        """
        data = {'code': '403', 'status': 'Forbidden'}
        manager = ModelManager()
        if nid is None:
            # New Notice
            # Join comma-separated list of Building IDs, taken from the Building's codenames
            _buildings = ','.join([str(b.id) for b in Building.objects.filter(codename__in=buildings.split(','))])
            res = manager.post('notice', subject=subject, sender=sender, buildings=_buildings, is_official=is_official)
        else:
            # Reply
            res = manager.post('reply', subject=subject, sender=sender, nid=nid, is_official=is_official)
        data['code'] = res['status']
        if data['code'] in (200, 304):
            data['status'] = 'OK'
        else:
            data['status'] = 'Bad Request'
            logger.error(res['response'])
        return data
