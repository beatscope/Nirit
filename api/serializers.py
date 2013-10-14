# api/serializers.py
""" 
Nirit API 
Uses the Django REST framework.

"""
import logging
from django.conf import settings
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from nirit.models import Building, Organization, CompanyProfile, Notice, Expertise

logger = logging.getLogger('api.serializers')


class ShortCompanySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(source='link', read_only=True)
    square_logo = serializers.Field(source='get_square_logo')
    class Meta:
        model = Organization
        fields = ('name', 'codename', 'slug', 'square_logo')


class ShortUserSerializer(serializers.ModelSerializer):
    name = serializers.RelatedField(source='profile.name')
    codename = serializers.RelatedField(source='profile.codename')
    roles = serializers.RelatedField(source='groups', many=True, read_only=True)
    is_admin = serializers.Field(source='is_superuser')

    class Meta:
        model = User
        fields = ('name', 'codename', 'roles', 'is_staff', 'is_admin')


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.RelatedField(source='groups', many=True, read_only=True)
    is_admin = serializers.Field(source='is_superuser')
    codename = serializers.RelatedField(source='profile.codename')
    full_name = serializers.RelatedField(source='profile.name')
    avatar = serializers.RelatedField(source='profile.avatar')
    company = ShortCompanySerializer(source='profile.company', read_only=True)

    class Meta:
        model = User
        fields = ('codename', 'is_staff', 'is_admin', 'full_name', 'avatar', 'company', 'roles')


class CompanyProfileSerializer(serializers.ModelSerializer):
    """
    Display Building details in Organization serializer.

    """
    name = serializers.Field(source='building.name')
    codename = serializers.Field(source='building.codename')
    slug = serializers.Field(source='building.link')
    status = serializers.Field(source='get_status')
    floor = serializers.RelatedField()
    floor_tag = serializers.RelatedField()

    class Meta:
        model = CompanyProfile
        fields = ('name', 'codename', 'slug', 'status', 'floor', 'floor_tag')


class BuildingProfileSerializer(serializers.ModelSerializer):
    """
    Display Organization details in Building serializer.

    """
    name = serializers.Field(source='organization.name')
    codename = serializers.Field(source='organization.codename')
    department = serializers.Field(source='organization.get_department_display')
    expertise = serializers.RelatedField(source='organization.expertise', many=True)
    slug = serializers.Field(source='organization.link')
    status = serializers.Field(source='get_status')
    floor = serializers.RelatedField()
    floor_tag = serializers.RelatedField()
    square_logo = serializers.Field(source='organization.get_square_logo')

    class Meta:
        model = CompanyProfile
        fields = ('name', 'codename', 'department', 'expertise', 'slug', 'status', 'floor', 'floor_tag', 'square_logo')


class OrganizationSerializer(serializers.ModelSerializer):
    name = serializers.Field(source='name')
    slug = serializers.SlugField(source='link', read_only=True)
    department = serializers.Field(source='get_department_display')
    expertise = serializers.RelatedField(many=True)
    members = ShortUserSerializer(many=True, read_only=True)
    image = serializers.Field(source='get_image')
    square_logo = serializers.Field(source='get_square_logo')
    logo = serializers.Field(source='get_logo')
    buildings = CompanyProfileSerializer(source='company_profile', many=True)

    class Meta:
        model = Organization
        lookup_field = 'codename'
        fields = ('name', 'codename', 'slug', \
                  'department', 'expertise', 'image', 'square_logo', 'logo', \
                  'members', 'buildings')


class BuildingSerializer(serializers.ModelSerializer):
    name = serializers.Field(source='name')
    slug = serializers.SlugField(source='link')
    members = ShortUserSerializer(many=True, read_only=True)
    notices = serializers.IntegerField(source='get_notices.count')
    organizations = BuildingProfileSerializer(source='building_profile', many=True)

    class Meta:
        model = Building
        lookup_field = 'codename'
        fields = ('name', 'codename', 'slug', 'members', 'notices', 'organizations')


class NoticeSerializer(serializers.ModelSerializer):
    subject = serializers.Field(source='get_subject')
    body = serializers.Field(source='get_body')
    type = serializers.Field(source='get_type_display')
    sender = UserSerializer()
    age = serializers.Field(source='get_age')
    official = serializers.BooleanField(source='is_official')
    replies = serializers.PrimaryKeyRelatedField(source='get_replies', many=True, read_only=True)
    buildings = serializers.RelatedField(source='building_set', many=True, read_only=True)

    class Meta:
        model = Notice
        fields = ('id', 'subject', 'body', 'created', 'date', 'age', 'sender', 'type', 'official', 'buildings', 'is_reply', 'replies')


class ExpertiseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='expertise-detail')

    class Meta:
        model = Expertise
