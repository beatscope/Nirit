# api/serializers.py
""" 
Nirit API 
Uses the Django REST framework.

"""
import logging
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from nirit.models import Building, Organization, Notice, Expertise

logger = logging.getLogger('api.serializers')


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.Field(source='name')
    url = serializers.HyperlinkedIdentityField(view_name='organization-detail', lookup_field = 'codename')
    status = serializers.Field(source='get_status')
    slug = serializers.SlugField(source='link', read_only=True)
    buildings = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='building-detail', lookup_field='codename')
    department = serializers.Field(source='get_department_display')
    expertise = serializers.RelatedField(many=True)
    members = serializers.RelatedField(many=True, read_only=True)
    image = serializers.Field(source='get_image')
    square_logo = serializers.Field(source='get_square_logo')
    logo = serializers.Field(source='get_logo')
    floor = serializers.Field(source='floor_tag')

    class Meta:
        model = Organization
        lookup_field = 'codename'


class BuildingSerializer(serializers.ModelSerializer):
    name = serializers.Field(source='name')
    slug = serializers.SlugField(source='link')
    members = serializers.IntegerField(source='get_members_count')
    notices = serializers.IntegerField(source='get_notices_count')
    organizations = OrganizationSerializer(many=True)

    class Meta:
        model = Building
        lookup_field = 'codename'


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.RelatedField(source='groups', many=True, read_only=True)
    is_admin = serializers.Field(source='is_superuser')
    full_name = serializers.RelatedField(source='get_full_name')
    avatar = serializers.RelatedField(source='profile.get_avatar')
    company = OrganizationSerializer(source='profile.company')

    class Meta:
        model = User
        fields = ('id', 'is_staff', 'is_admin', 'username', 'full_name', 'first_name', 'last_name', 'avatar', 'company', 'roles')


class NoticeSerializer(serializers.ModelSerializer):
    subject = serializers.Field(source='get_subject')
    type = serializers.Field(source='get_type_display')
    sender = UserSerializer()
    age = serializers.Field(source='get_age')
    official = serializers.BooleanField(source='is_official')
    replies = serializers.PrimaryKeyRelatedField(source='get_replies', many=True, read_only=True)
    buildings = serializers.RelatedField(source='building_set', many=True, read_only=True)

    class Meta:
        model = Notice
        fields = ('id', 'subject', 'created', 'date', 'age', 'sender', 'type', 'official', 'buildings', 'is_reply', 'replies')


class ExpertiseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='expertise-detail')

    class Meta:
        model = Expertise
