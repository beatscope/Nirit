# nirit/api.py
import logging
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings
from nirit.models import Building, Notice
from nirit.manager import ModelManager
from nirit.utils import build_notice_card

logger = logging.getLogger('nirit.api')


def notices(request, nid=-1, action='view', rng=0):
    data = {'code': '403', 'status': 'Forbidden'}
    if request.method == 'GET' and nid > -1:
        try:
            notice = Notice.objects.get(pk=nid)
        except (Notice.DoesNotExist, ValueError):
            # Is the Building Board requested?
            try:
                building = Building.objects.get(codename=nid)
            except Building.DoesNotExist:
                data['code'], data['status'] = 404, 'Not Found'
            else:
                # Return ranged cards for the Building
                # The range is used as the starting point
                # e.g.: if range = 6, return replies from 7 to 7 + settings.BOARD_NOTICES
                rng = rng if rng else 0
                data['code'], data['status'] = 200, 'OK'
                cards = building.notices.filter(is_reply=False).order_by('-created')
                data['cards_count'] = cards.count()
                data['cards'] = []
                for card in cards[int(rng):int(rng)+settings.BOARD_NOTICES]:
                    data['cards'].append(build_notice_card(card, mimetype='json'))
        else:
            data['code'], data['status'] = 200, 'OK'
            data['id'] = notice.id
            notice_data = build_notice_card(notice, mimetype='json')
            if action == 'replies':
                replies = notice.get_replies()
                data['replies_count'] = replies.count()
                data['replies'] = []
                # The range is used as the starting point
                # e.g.: if range = 2, return replies from 3 to 12 (if settings.BOARD_NOTICES = 10)
                rng = rng if rng else 0
                for reply in replies[int(rng):int(rng)+settings.BOARD_NOTICES]:
                    reply_data = build_notice_card(reply, mimetype='json')
                    data['replies'].append(reply_data)
            else:
                data.update(notice_data)
                data['type'] = notice.get_type_display()
                data['subject'] = notice.subject
                data['replies'] = notice.get_replies().count()

    elif request.method == 'POST' and request.POST.has_key('subject') and (request.POST.has_key('buildings') or request.POST.has_key('nid')):
        manager = ModelManager()
        is_official = bool(int(request.POST['is_official']))
        if not request.POST.has_key('nid'):
            # New Notice
            # Join comma-separated list of Building IDs, taken from the Building's codenames
            buildings = ','.join([str(b.id) for b in Building.objects.filter(codename__in=request.POST['buildings'].split(','))])
            res = manager.post('notice', subject=request.POST['subject'], sender=request.user.username, buildings=buildings, is_official=is_official)
        else:
            # Reply
            res = manager.post('reply', subject=request.POST['subject'], sender=request.user.username, nid=request.POST['nid'], is_official=is_official)
        data['code'] = res['status']
        if data['code'] in (200, 304):
            data['status'] = 'OK'
        else:
            data['status'] = 'Bad Request'
            logger.error(res['response'])
    c = RequestContext(request)
    response = render_to_response('nirit/default.json', {'data': json.dumps(data)}, context_instance=c)
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response
