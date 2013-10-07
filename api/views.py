# api/views.py
import logging
import re
from django.http import Http404
from rest_framework import authentication
from rest_framework import filters
from rest_framework import generics
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from nirit.models import Building, Notice, Expertise, Organization, CompanyProfile, UserProfile
from api.serializers import BuildingSerializer, \
                            UserSerializer, \
                            NoticeSerializer, \
                            OrganizationSerializer, \
                            ExpertiseSerializer

logger = logging.getLogger('api.views')

@api_view(('GET',))
@permission_classes((permissions.IsAdminUser, ))
def api_root(request, format=None):
    return Response({
        'buildings': reverse('buildings-list', request=request, format=format),
        'notices': reverse('notices-list', request=request, format=format),
        'organizations': reverse('organizations-list', request=request, format=format),
        'expertise': reverse('expertise-list', request=request, format=format)
    })


class BuildingListView(generics.ListAPIView):
    """
    List all buildings (read-only).

    """
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    permission_classes = (permissions.IsAdminUser,)


class BuildingView(generics.RetrieveAPIView):
    """
    Retrieve a building.

    """
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    lookup_field = 'codename'
    permission_classes = (permissions.IsAdminUser,)


class NoticeListView(generics.ListAPIView):
    """
    List notices (read-only).

    Notices list represent a board.
    Boards can be filtered for:
    
    - A Building
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

        # Building Notices
        if self.request.QUERY_PARAMS.has_key('building'):
            building = self.request.QUERY_PARAMS.get('building', None)
            if not building:
                return queryset
            try:
                building = Building.objects.get(codename=building)
            except Building.DoesNotExist:
                return queryset
            else:
                queryset = building.notices.filter(is_reply=False)
                # exclude notices posted by a BANNED company
                # we only exclude the Companies which are banned in this particular Building
                banned = [bp['organization__id'] for bp \
                         in building.building_profile.filter(status=CompanyProfile.BANNED).values('organization__id')]
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
                # we only exclude Notices sent in the Building where the Company is banned
                banned = [cp['building__id'] for cp \
                         in organization.company_profile.filter(status=CompanyProfile.BANNED).values('building__id')]
                if banned:
                    queryset = queryset.exclude(building__pk__in=banned)

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
                # we only exclude Notices sent in the User's Active Building,
                # where the Company is banned
                company_profile = CompanyProfile.objects.get(building=profile.building, organization=profile.company)
                if company_profile.status == CompanyProfile.BANNED:
                    queryset = Notice.objects.none()

        # By default, we return Notices for the User's Active Building
        queryset = queryset.filter(building=self.request.user.get_profile().building)
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
            if 'Building Manager' in profile.roles:
                # Building Managers are allowed to specify which type of Notice to post
                data['types'] = [{'value': key, 'label': value} for key, value in Notice.TYPES]
            # Retrieve the full list of Notices the logged-in user can see
            # i.e.: sent in the user's active uilding
            queryset = Notice.objects.filter(building=profile.building, is_reply=False).order_by('-created')
            # exclude BANNED senders
            queryset = queryset.exclude(sender__profile__status=UserProfile.BANNED)
            # exclude notices posted by a BANNED company
            # we only exclude Notices sent in the User's Active Building,
            # where the Company is banned
            company_profile = CompanyProfile.objects.get(building=profile.building, organization=profile.company)
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
    # Check Token Authentication first, as this is how it will be used form AJAX
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication,)

    def post(self, request, format=None):
        # subject is required
        if not request.DATA.has_key('subject') or not request.DATA['subject']:
            return Response({'detail': "Subject required."},
                            status=400,
                            exception=True)

        # check building(s) is(are) attached to Notices.
        if not request.DATA.has_key('buildings') or not request.DATA['buildings']:
            return Response({'detail': "Building(s) required."},
                            status=400,
                            exception=True)

        buildings = Building.objects.filter(codename__in=request.DATA['buildings'])
        if not buildings:
            return Response({'detail': "No Building(s) found."},
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
                # override building list when replying is case they are different
                buildings = reply_to.building_set.all()
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

        # assign Buildings after the Notice is created
        for building in buildings:
            building.notices.add(notice)

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

        - by building (codename)
        - by name
        - by floor
        - by department

        """
        queryset = self.queryset
        
        # Building filter
        if self.request.QUERY_PARAMS.has_key('building'):
            queryset = queryset.filter(company_profile__building__codename=self.request.QUERY_PARAMS['building'])

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

        # Ordering
        if self.request.QUERY_PARAMS.has_key('order-by'):
            order_by = self.request.QUERY_PARAMS['order-by']
            if order_by in ('name', 'department'):
                queryset = queryset.order_by(order_by)
            elif order_by == 'floor':
                queryset = queryset.order_by('company_profile__floor')
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
    List all expertises, or create a new expertise.

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
    # Check Token Authentication first, as this is how it will be used form AJAX
    authentication_classes = (authentication.TokenAuthentication, authentication.SessionAuthentication,)


class ExpertiseView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an expertise.

    """
    queryset = Expertise.objects.all()
    serializer_class = ExpertiseSerializer
