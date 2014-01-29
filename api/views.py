# api/views.py
import logging
import re
from django.http import Http404
from django.db.models import Q
from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from nirit.models import Space, Notice, Expertise, Supplier, \
                         Organization, CompanyProfile, UserProfile
from api.serializers import SpaceSerializer, \
                            UserSerializer, \
                            NoticeSerializer, \
                            OrganizationSerializer, \
                            ExpertiseSerializer, \
                            SupplierSerializer

logger = logging.getLogger('api.views')

@api_view(('GET',))
@permission_classes((permissions.IsAdminUser, ))
def api_root(request, format=None):
    return Response({
        'spaces': reverse('spaces-list', request=request, format=format),
        'notices': reverse('notices-list', request=request, format=format),
        'organizations': reverse('organizations-list', request=request, format=format),
        'expertise': reverse('expertise-list', request=request, format=format),
        'suppliers': reverse('suppliers-list', request=request, format=format),
    })


class SpaceListView(generics.ListAPIView):
    """
    List all spaces (read-only).

    """
    queryset = Space.objects.all()
    serializer_class = SpaceSerializer


class SpaceView(generics.RetrieveAPIView):
    """
    Retrieve a space.

    """
    queryset = Space.objects.all()
    serializer_class = SpaceSerializer
    lookup_field = 'codename'


class NoticeListView(generics.ListAPIView):
    """
    List notices (read-only).

    Notices list represent a board.
    Boards can be filtered for:
    
    - A Space
        - refined by Member's starred notices
        - refined by Member's network notices
        - refined by Member's company notices
    - A Member
    - A Company

    """
    model = Notice
    serializer_class = NoticeSerializer
    paginate_by = 5

    def get_queryset(self):
        """
        Build queryset according to request parameters.
        
        """
        queryset = Notice.objects.none()

        # Space Notices
        if self.request.QUERY_PARAMS.has_key('space'):
            space = self.request.QUERY_PARAMS.get('space', None)
            if not space:
                return queryset
            try:
                space = Space.objects.get(codename=space)
            except Space.DoesNotExist:
                return queryset
            else:
                queryset = space.notices.filter(is_reply=False)
                # exclude notices posted by a BANNED company
                # we only exclude the Companies which are banned in this particular Space
                banned = [bp['organization__id'] for bp \
                         in space.space_profile.filter(status=CompanyProfile.BANNED).values('organization__id')]
                if banned:
                    queryset = queryset.exclude(sender__profile__company__pk__in=banned)
                # handle filters
                # when filters are provided, we expect the 'filter' and 'member' parameters
                if self.request.QUERY_PARAMS.has_key('filter') and self.request.QUERY_PARAMS.has_key('member'):
                    try:
                        profile = UserProfile.objects.get(codename=self.request.QUERY_PARAMS['member'])
                    except UserProfile.DoesNotExist:
                        pass
                    else:
                        # apply filter selection
                        if self.request.QUERY_PARAMS['filter'] == 'starred':
                            starred = [int(n['id']) for n in profile.starred.values('id')]
                            queryset = queryset.filter(pk__in=starred)
                        elif self.request.QUERY_PARAMS['filter'] == 'network':
                            network = [int(o['id']) for o in profile.networked.values('id')]
                            queryset = queryset.filter(sender__profile__company__pk__in=network)
                        elif self.request.QUERY_PARAMS['filter'] == 'company':
                            company = profile.company.id
                            queryset = queryset.filter(sender__profile__company__pk=company)
                        elif self.request.QUERY_PARAMS['filter'] == 'mention':
                            if self.request.QUERY_PARAMS.has_key('mention') and self.request.QUERY_PARAMS['mention']:
                                mention = self.request.QUERY_PARAMS['mention']
                                q = Q(subject__contains='@{}'.format(mention)) | Q(body__contains='@{}'.format(mention))
                                queryset = queryset.filter(q)

        # Company Notices
        elif self.request.QUERY_PARAMS.has_key('company'):
            company = self.request.QUERY_PARAMS.get('company', None)
            if not company:
                return queryset
            try:
                organization = Organization.objects.get(codename=company)
            except Organization.DoesNotExist:
                return queryset
            else:
                members = organization.members.all()
                # concatenate notices from all company members
                # sent officially
                for member in members:
                    queryset = queryset | Notice.objects.filter(sender=member, is_reply=False, is_official=True)
                # exclude notices posted by a BANNED company
                # we only exclude Notices sent in the Space where the Company is banned
                banned = [cp['space__id'] for cp \
                         in organization.company_profile.filter(status=CompanyProfile.BANNED).values('space__id')]
                if banned:
                    queryset = queryset.exclude(space__pk__in=banned)

        # Member Notices
        elif self.request.QUERY_PARAMS.has_key('member'):
            member = self.request.QUERY_PARAMS.get('member', None)
            if not member:
                return queryset
            try:
                profile = UserProfile.objects.get(codename=member)
            except UserProfile.DoesNotExist:
                return queryset
            else:
                queryset = Notice.objects.filter(sender=profile.user, is_reply=False).order_by('-updated')
                # exclude notices posted by a BANNED company
                # we only exclude Notices sent in the User's Active Space,
                # where the Company is banned
                try:
                    company_profile = CompanyProfile.objects.get(space=profile.space, organization=profile.company)
                    if company_profile.status == CompanyProfile.BANNED:
                        queryset = Notice.objects.none()
                except CompanyProfile.DoesNotExist:
                    pass

        # By default, we return Notices for the User's Active Space
        if self.request.user.get_profile().space:
            queryset = queryset.filter(space=self.request.user.get_profile().space)
        # exclude notices posted by a BANNED user
        queryset = queryset.exclude(sender__profile__status=UserProfile.BANNED)
        # order all results by latest updated
        queryset = queryset.order_by('-updated')
        return queryset

    def metadata(self, request):
        """
        display list of notices for the authenticated user.

        """
        data = super(NoticeListView, self).metadata(request)
        data.pop('description')
        data.pop('renders')
        data.pop('parses')
        if request.user.is_authenticated:
            # Add notice types
            data['types'] = []
            profile = request.user.get_profile()
            if 'Manager' in profile.roles:
                # Managers are allowed to specify which type of Notice to post
                data['types'] = [{'value': key, 'label': value} for key, value in Notice.TYPES]
            # Retrieve the full list of Notices the logged-in user can see
            # i.e.: sent in the user's active uilding
            queryset = Notice.objects.filter(space=profile.space, is_reply=False).order_by('-created')
            # exclude BANNED senders
            queryset = queryset.exclude(sender__profile__status=UserProfile.BANNED)
            # exclude notices posted by a BANNED company
            # we only exclude Notices sent in the User's Active Space,
            # where the Company is banned
            company_profile = CompanyProfile.objects.get(space=profile.space, organization=profile.company)
            if company_profile.status == CompanyProfile.BANNED:
                queryset = Notice.objects.none()

            count = queryset.count()
            notices = {}
            for notice in queryset:
                replies = notice.get_replies()
                count += replies.count()
                notices[notice.id] = [int(r['id']) for r in replies.values('id')]
            starred = [int(n['id']) for n in profile.starred.values('id')]
            network = [int(o['id']) for o in profile.networked.values('id')]
            data['results'] = {
                'all': count, # count all posts and replies
                'starred': queryset.filter(pk__in=starred).count(),
                'network': queryset.filter(sender__profile__company__pk__in=network).count(),
                'company': queryset.filter(sender__profile__company=profile.company).count(),
                'notices': notices,
            }
        return data


class NoticePostView(APIView):
    """
    Post new Notice or Reply.
    Provides a post method handler.

    """
    def post(self, request, format=None):
        # subject is required
        if not request.DATA.has_key('subject') or not request.DATA['subject']:
            return Response({'detail': "Subject required."},
                            status=400,
                            exception=True)

        # check space(s) is(are) attached to Notices.
        if not request.DATA.has_key('spaces') or not request.DATA['spaces']:
            return Response({'detail': "Space(s) required."},
                            status=400,
                            exception=True)

        spaces = Space.objects.filter(codename__in=request.DATA['spaces'])
        if not spaces:
            return Response({'detail': "No Space(s) found."},
                            status=400,
                            exception=True)

        # the sender is always the logged-in user
        sender = request.user

        # is_official is checkbox formatted
        is_official = True \
                      if request.DATA.has_key('official') and request.DATA['official'] == 'on' \
                      else False

        # check for nid
        # if present, attach notice as reply
        if request.DATA.has_key('nid'):
            try:
                reply_to = Notice.objects.get(pk=int(request.DATA['nid']))
                # override space list when replying is case they are different
                spaces = reply_to.space_set.all()
            except Notice.DoesNotExists:
                reply_to = None
        else:
            reply_to = None
       
        # check requested type 
        notice_type = Notice.NOTICE # default type
        if request.DATA.has_key('type') and str(request.DATA['type']).isdigit():
            notice_type = int(request.DATA['type'])

        # create Notice
        notice = Notice.objects.create(subject=request.DATA['subject'], 
                                       body=request.DATA['body'] if request.DATA.has_key('body') else None,
                                       sender=sender,
                                       type=notice_type,
                                       is_official=is_official,
                                       is_reply = True if reply_to else False,
                                       reply_to=reply_to)

        # assign Spaces after the Notice is created
        for space in spaces:
            space.notices.add(notice)

        # touch the reply_to recipient notice to update its timestamp
        if reply_to:
            reply_to.save()
        
        # serialize notice to return
        serializer = NoticeSerializer(notice)
        return Response(serializer.data)


class NoticeView(generics.ListAPIView):
    """
    Retrieve a notice's replies.

    """
    model = Notice
    serializer_class = NoticeSerializer
    paginate_by = 6

    def get_queryset(self):
        try:
            notice = Notice.objects.get(pk=self.kwargs['pk'])
        except Notice.DoesNotExist:
            raise http404
        else:
            return notice.get_replies()


class OrganizationListView(generics.ListAPIView):
    """
    List all companies (read-only).

    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    lookup_field = 'codename'
    paginate_by = 999

    def get_queryset(self):
        """
        Filter query according to the query parameters.
        Can filter, and order:

        - by space (codename)
        - by name
        - by floor
        - by department

        """
        queryset = self.queryset
        
        # Space filter
        if self.request.QUERY_PARAMS.has_key('space'):
            queryset = queryset.filter(company_profile__space__codename=self.request.QUERY_PARAMS['space'])

        # Name filter
        if self.request.QUERY_PARAMS.has_key('name'):
            queryset = queryset.filter(name__icontains=self.request.QUERY_PARAMS['name'])

        # Deparment filter
        if self.request.QUERY_PARAMS.has_key('department'):
            regex = re.compile(r'{}'.format(str(self.request.QUERY_PARAMS['department'])), re.IGNORECASE)
            departments = [int(key) for key, label in Organization.DEPARTMENT_CHOICES if regex.search(label) is not None]
            queryset = queryset.filter(department__in=departments)

        # Floor filter
        if self.request.QUERY_PARAMS.has_key('floor'):
            queryset = queryset.filter(company_profile__floor__exact=self.request.QUERY_PARAMS['floor'])

        # Building filter
        if self.request.QUERY_PARAMS.has_key('building'):
            queryset = queryset.filter(company_profile__building__exact=self.request.QUERY_PARAMS['building'])

        # Ordering
        if self.request.QUERY_PARAMS.has_key('order-by'):
            order_by = self.request.QUERY_PARAMS['order-by']
            if order_by in ('name', 'department'):
                queryset = queryset.order_by(order_by)
            elif order_by == 'floor':
                queryset = queryset.order_by('company_profile__floor')
            elif order_by == 'building':
                queryset = queryset.order_by('company_profile__building')
        return queryset


class OrganizationView(generics.RetrieveUpdateAPIView):
    """
    Retrieve a company.

    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    lookup_field = 'codename'


class ExpertiseListView(generics.ListAPIView):
    """
    List all expertise.

    """
    queryset = Expertise.objects.all()
    serializer_class = ExpertiseSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('title',)
    renderer_classes = (renderers.BrowsableAPIRenderer, renderers.JSONRenderer, renderers.JSONPRenderer)


class ExpertiseCreateView(generics.CreateAPIView):
    """
    Create new Expertise.

    """
    model = Expertise
    serializer_class = ExpertiseSerializer


class ExpertiseView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an expertise.

    """
    queryset = Expertise.objects.all()
    serializer_class = ExpertiseSerializer


class SupplierListView(generics.ListAPIView):
    """
    List all suppliers.

    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('spaces__codename',)
