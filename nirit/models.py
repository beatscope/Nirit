# nirit/models.py
import logging
import datetime
import hashlib
import re
import uuid
from django.db import models
from django.db.models.signals import post_save
from django.core.mail import EmailMultiAlternatives
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.timesince import timesince
from django.conf import settings
from rest_framework.authtoken.models import Token
from nirit.fixtures import DEPARTMENTS

logger = logging.getLogger('nirit.models')


class Expertise(models.Model):
    title = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return force_unicode(self.title)

    class Meta:
        ordering = ['title']


class Notice(models.Model):
    ALERT = 0
    NOTICE = 1
    INTRO = 2

    TYPES = (
        (ALERT, 'ALERT'),
        (NOTICE, 'NOTICE'),
        (INTRO, 'INTRO'),
    )
    subject = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)
    sender = models.ForeignKey(User)
    type = models.IntegerField(default=NOTICE, choices=TYPES)
    is_official = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True)

    def __unicode__(self):
        text = "{}, {}: {}".format(self.created.date(), self.created.time(), self.subject)
        if self.is_reply:
            text = "(R#{}) {}".format(self.reply_to.id, text)
        if self.type == 0:
            text = "{} [{}]".format(text, self.get_type_display())
        return "[#{}] {}".format(self.id, text)

    def get_subject(self):
        # escape subject to prevent script attacks
        return escape(self.subject)

    def get_age(self):
        return timesince(self.created, datetime.datetime.now())

    def get_replies(self):
        return Notice.objects.filter(reply_to=self)\
                             .exclude(sender__profile__company__status=Organization.BANNED)\
                             .exclude(sender__profile__status=UserProfile.BANNED)


class Organization(models.Model):
    DEPARTMENT_CHOICES = DEPARTMENTS
    SIZE_CHOICES = (
        ('A', 'myself only'),
        ('B', '2-10'),
        ('C', '11-50'),
        ('D', '51-200'),
        ('E', '201-500'),
        ('F', '501-1000'),
        ('G', '1001-5000'),
        ('H', '5001-10000'),
        ('I', '10001+'),
    )
    PENDING = 0
    VERIFIED = 1
    BANNED = 2
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (BANNED, 'Banned'),
    )
    
    name = models.CharField("Company Name", max_length=200, unique=True)
    codename = models.CharField(max_length=64, unique=True, null=True, blank=True)
    description = models.TextField("Company Description", null=True)
    created = models.DateField(auto_now_add=True)
    
    image = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                              help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 626 x 192 pixels or larger.")
    logo = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                             help_text="PNG, JPEG, or GIF; max size 2 MB.")
    square_logo = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                                    help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 60 x 60 pixels or larger.")

    department = models.IntegerField("Company Department", choices=DEPARTMENT_CHOICES, null=True, help_text="Main Company Industry")
    size = models.CharField("Company Size", max_length=1, choices=SIZE_CHOICES, null=True)
    founded = models.CharField("Year Founded", max_length=4, null=True, blank=True)
    floor = models.IntegerField("Floor", null=True)
    expertise = models.ManyToManyField(Expertise, help_text="Areas of Expertise", null=True, blank=True)
    status = models.IntegerField("Verification Status", choices=STATUS_CHOICES, default=PENDING)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        # generate codename from name when creating
        if self.id is None:
            created = True
            self.codename = hashlib.sha256(self.name).hexdigest()
        else:
            created = False
        super(Organization, self).save(*args, **kwargs)
        # create the permission when creating
        if created:
            content_type = ContentType.objects.get(app_label='nirit', model='organization')
            permission_name = 'Can access organization "{}"'.format(self.name)
            permission_codename = 'can_access_organization_{}'.format(self.codename)
            permission = Permission.objects.create(codename=permission_codename, name=permission_name, content_type=content_type)

    def delete(self, *args, **kwargs):
        # delete the permission before deleting the object
        permission = Permission.objects.get(codename='can_access_organization_{}'.format(self.codename))
        permission.delete()
        super(Organization, self).delete(*args, **kwargs)

    @property
    def floor_tag(self):
        tag = 'th'
        if self.floor < 0:
            return 'Basement'
        if self.floor == 0:
            return 'Ground'
        if self.floor not in (11, 12, 13): # 11, 12 and 13 are exceptions, they use 'th'
            last_digit = int(str(self.floor)[-1:])
            if last_digit == 1:
                tag = 'st'
            elif last_digit == 2:
                tag = 'nd'
            elif last_digit == 3:
                tag = 'rd'
        return "{}{}".format(self.floor, tag)

    @property
    def members(self):
        return User.objects\
               .filter(profile__company=self)\
               .filter(groups__name__in=['Owner','Rep','Staff','Building Manager'])\
               .exclude(profile__status=UserProfile.BANNED)\
               .distinct()

    @property
    def buildings(self):
        return Building.objects.filter(organizations=self)

    @property
    def slug(self):
        return re.sub(r'\s', '-', self.name).lower()

    @property
    def link(self):
        return '{}/{}'.format(self.slug, self.codename)

    def get_staff_awaiting(self):
        # Return pending staff
        return self.members.filter(profile__status=UserProfile.PENDING)

    def get_status(self):
        return self.get_status_display()

    def get_image(self):
        try:
            return self.image.url
        except ValueError:
            return ''

    def get_logo(self):
        try:
            return self.logo.url
        except ValueError:
            return ''

    def get_square_logo(self):
        try:
            return self.square_logo.url
        except ValueError:
            return ''

    def is_staff(self, user):
        return user in self.members.all()

    def is_owner(self, user):
        if not self.is_staff(user):
            return False
        return 'Owner' in [g.name for g in user.groups.all()]

    def is_rep(self, user):
        if not self.is_staff(user):
            return False
        return 'Rep' in [g.name for g in user.groups.all()]

    def is_editor(self, user):
        # Editors are allowed to edit Organizations info.
        # Editors are Admins
        is_allowed = False
        if self.is_owner(user):
            is_allowed = True
        elif self.is_rep(user):
            is_allowed = True
        return is_allowed

    def mail_editors(self, subject, text_content, html_content=None):
        from_email = settings.EMAIL_FROM
        recipients_list = [member.email for member in self.members if self.is_editor(member)]
        logger.debug(recipients_list)
        if recipients_list:
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            msg.send()


class Building(models.Model):
    name = models.CharField(max_length=200, unique=True)
    codename = models.CharField(max_length=64, unique=True, null=True, blank=True)
    organizations = models.ManyToManyField(Organization, null=True, blank=True)
    notices = models.ManyToManyField(Notice, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        # generate codename from name
        if self.id is None:
            self.codename = hashlib.sha256(self.name).hexdigest()
        super(Building, self).save(*args, **kwargs)
        # create the permission
        if self.id is None:
            content_type = ContentType.objects.get(app_label='nirit', model='building')
            permission_name = 'Can access building "{}"'.format(self.name)
            permission_codename = 'can_access_building_{}'.format(self.codename)
            permission = Permission.objects.create(codename=permission_codename, name=permission_name, content_type=content_type)

    def delete(self, *args, **kwargs):
        # delete the permission before deleting the object
        permission = Permission.objects.get(codename='can_access_building_{}'.format(self.codename))
        permission.delete()
        super(Building, self).delete(*args, **kwargs)

    @property
    def slug(self):
        return re.sub(r'\s', '-', self.name).lower()

    @property
    def link(self):
        return '{}/{}'.format(self.slug, self.codename)

    @property
    def members(self):
        """
        Return all members througout all the Organizations of the Building.
        Building Managers are considered members of their Buildings.

        """
        members = []
        for o in self.organizations.all():
            users = User.objects.filter(profile__company=o)\
                    .filter(groups__name__in=['Owner','Rep','Staff','Building Manager'])\
                    .exclude(profile__status=UserProfile.BANNED)\
                    .distinct()\
                    .order_by('first_name', 'last_name', 'username')
            members.extend(users)
        return members

    @property
    def managers(self):
        """
        Return all Building Managers througout all the Organizations of the Building.

        """
        managers = []
        for o in self.organizations.all():
            users = User.objects.filter(profile__company=o)\
                    .filter(groups__name='Building Manager')\
                    .exclude(profile__status=UserProfile.BANNED)\
                    .distinct()\
                    .order_by('first_name', 'last_name', 'username')
            managers.extend(users)
        return managers

    def get_members_count(self):
        return len(self.members)

    def get_pending_companies(self):
        # Return pending companies
        return self.organizations.filter(status=Organization.PENDING)

    def get_notices(self):
        return self.notices.filter(is_reply=False)

    def get_notices_count(self):
        return self.get_notices().count()

    def mail_managers(self, subject, text_content, html_content=None):
        from_email = settings.EMAIL_FROM
        recipients_list = [manager.email for manager in self.managers]
        if recipients_list:
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            msg.send()


class OToken(models.Model):
    """
    Organization Token.
    A valid token is required in order to create an Organization.

    """
    key = models.CharField(max_length=14, primary_key=True)
    building = models.ForeignKey(Building)
    user = models.ForeignKey(User)
    redeemed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(OToken, self).save(*args, **kwargs)

    def generate_key(self):
        code = str(uuid.uuid4())
        unique = code[9:23].upper()
        # make sure it is unique
        token = OToken.objects.filter(pk=unique)
        if token:
            unique = self.generate_key()
        return unique

    def is_valid(self, token):
        try:
            t = OToken.objects.get(key=token)
            # Valid tokens have not yet been redeemed
            return not t.redeemed
        except OToken.DoesNotExist:
            return False

    def __unicode__(self):
        return self.key


class UserProfile(models.Model):
    PENDING = 0
    VERIFIED = 1
    BANNED = 2
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (BANNED, 'Banned'),
    )

    user = models.OneToOneField(User, related_name='profile')
    company = models.ForeignKey(Organization, null=True, blank=True, related_name='company', on_delete=models.SET_NULL)
    building = models.ForeignKey(Building, null=True, blank=True, help_text="Primary building", on_delete=models.SET_NULL)
    starred = models.ManyToManyField(Notice, null=True, blank=True)
    networked = models.ManyToManyField(Organization, null=True, blank=True, related_name='networked')
    thumbnail = models.ImageField(upload_to='./member/%Y/%m/%d', null=True, blank=True, \
                                  help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 60 x 60 pixels or larger.")
    job_title = models.CharField(max_length=64, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    status = models.IntegerField("Verification Status", choices=STATUS_CHOICES, default=PENDING)

    def get_avatar(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            return '{}images/useravatar_60x60.png'.format(settings.STATIC_URL)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
post_save.connect(create_auth_token, sender=User)



