# nirit/models.py
import logging
import base64
import datetime
import hashlib
import random
import re
import uuid
from django.db import models
from django.db.models.signals import post_save
from django.core.mail import EmailMultiAlternatives
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, User
from django.utils.crypto import pbkdf2, get_random_string
from django.utils.html import strip_tags, linebreaks
from django.utils.encoding import force_unicode
from django.utils.timesince import timesince
from django.conf import settings
from rest_framework.authtoken.models import Token
from nirit.fixtures import DEPARTMENTS, SUPPLIER_TYPES
from nirit import utils
from markitup.fields import MarkupField

logger = logging.getLogger('nirit.models')


class Geocode(models.Model):
    code = models.CharField(max_length=125)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __unicode__(self):
        return '{},{}'.format(self.latitude, self.longitude)


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
    subject = models.CharField(max_length=128)
    body = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    date = models.DateField(auto_now_add=True)
    sender = models.ForeignKey(User)
    type = models.IntegerField(default=NOTICE, choices=TYPES)
    is_official = models.BooleanField(default=False)
    is_reply = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, editable=False)

    def __unicode__(self):
        text = u"{}, {}: {}".format(
            self.created.date(), 
            self.created.time(), 
            force_unicode(self.subject),
        )
        if self.is_reply:
            text = u"[R#{}] {!s}".format(self.reply_to.id, text)
        else:
            text = u"[{}] {!s}".format(self.get_type_display(), text)
        return u"[#{}] {}".format(self.id, text)

    def get_subject(self):
        # escape subject to prevent script attacks
        subject = force_unicode(self.subject)
        return strip_tags(subject)

    def get_body(self):
        # escape body to prevent script attacks,
        # and convert line breaks in p tags
        body = force_unicode(self.body)
        body = linebreaks(body, autoescape=True)
        return body

    def get_age(self):
        return timesince(self.created, datetime.datetime.now())

    def get_replies(self):
        replies = Notice.objects.filter(reply_to=self)\
                                .exclude(sender__profile__status=UserProfile.BANNED)
        # Exclude post sent by Companies BANNED in the Notice's Building
        exclude = []
        for reply in replies:
            # the reply has to be in the same building as the original Notice
            buildings = self.building_set.all()
            # check the status of the reply company is each building
            for building in buildings:
                building_profile = CompanyProfile.objects.get(building=building, organization=reply.sender.profile.company)
                if building_profile.status == CompanyProfile.BANNED:
                    exclude.append(reply.id)
        if exclude:
            replies = replies.exclude(pk__in=exclude)
        return replies


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
        
    name = models.CharField("Company Name", max_length=200, unique=True)
    codename = models.CharField(max_length=64, null=True, blank=True)
    description = models.TextField("Company Description", null=True)
    created = models.DateField(auto_now_add=True)
    
    image = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                              help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 626 x 192 pixels or larger.")
    logo = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                             help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 180 x 90 pixels or larger.")
    square_logo = models.ImageField(upload_to='./company/%Y/%m/%d', null=True, blank=True, \
                                    help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 60 x 60 pixels or larger.")

    department = models.IntegerField("Company Department", choices=DEPARTMENT_CHOICES, null=True, help_text="Main Company Industry")
    size = models.CharField("Company Size", max_length=1, choices=SIZE_CHOICES, null=True)
    founded = models.CharField("Year Founded", max_length=4, null=True, blank=True)
    expertise = models.ManyToManyField(Expertise, help_text="Areas of Expertise", null=True, blank=True)

    website = models.URLField("Website", null=True, blank=True, help_text="Company website URL")
    facebook = models.URLField("Facebook", null=True, blank=True, help_text="Facebook Page")
    twitter = models.URLField("Twitter", null=True, blank=True, help_text="Twitter Profile")
    linkedin = models.URLField("LinkedIn", null=True, blank=True, help_text="LinkedIn Page")

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
    def members(self):
        return User.objects\
               .filter(profile__company=self)\
               .filter(groups__name__in=['Owner','Rep','Staff','Building Manager'])\
               .exclude(profile__status=UserProfile.BANNED)\
               .distinct()

    @property
    def editors(self):
        return User.objects\
               .filter(profile__company=self)\
               .filter(groups__name__in=['Owner','Rep'])\
               .exclude(profile__status=UserProfile.BANNED)\
               .distinct()

    @property
    def slug(self):
        return re.sub(r'\s', '-', self.name).lower()

    @property
    def link(self):
        return '{}/{}'.format(self.slug, self.codename)

    def get_image(self):
        try:
            return self.image.url
        except ValueError:
            return ''

    def get_logo(self):
        try:
            logo = self.logo.url
            if logo.endswith('False'):
                return ''
            return logo
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
        if recipients_list:
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            msg.send()


class Building(models.Model):
    name = models.CharField(max_length=200, unique=True)
    codename = models.CharField(max_length=64, unique=True, null=True, blank=True)
    postcode = models.CharField("Postcode", max_length=8, help_text='Please include the gap (space) between the outward and inward codes')
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
    def geocode(self):
        try:
            geocode = Geocode.objects.get(code=self.postcode)
        except Geocode.DoesNotExist:
            # If the geocode for this postcode has not yet been stored,
            # fetch it
            try:
                point = utils.get_postcode_point(self.postcode)
            except:
                # The function raises an Exception when the postcode does not exist
                # we store the resulst as (0, 0) to avoid fetching the API every time
                point = (0.0, 0.0)
            geocode = Geocode.objects.create(code=self.postcode, latitude=point[0], longitude=point[1])
        return geocode

    @property
    def members(self):
        """
        Return all members througout all the Organizations of the Building.
        Building Managers are considered members of their Buildings.

        """
        profiles = self.building_profile.filter(building=self)\
                                        .exclude(status=CompanyProfile.BANNED)
        ids = []
        for profile in profiles:
            ids.extend([m['id'] for m in profile.organization.members.values('id')])
        members = User.objects.filter(pk__in=ids)\
                              .filter(groups__name__in=['Owner','Rep','Staff','Building Manager'])\
                              .exclude(profile__status=UserProfile.BANNED)\
                              .distinct()\
                              .order_by('first_name', 'last_name', 'username')
        return members

    @property
    def managers(self):
        """
        Return all Building Managers througout all the Organizations of the Building.

        """
        profiles = self.building_profile.filter(building=self)\
                                        .exclude(status=CompanyProfile.BANNED)
        ids = []
        for profile in profiles:
            ids.extend([m['id'] for m in profile.organization.members.values('id')])
        managers = User.objects.filter(pk__in=ids)\
                               .filter(groups__name='Building Manager')\
                               .exclude(profile__status=UserProfile.BANNED)\
                               .distinct()\
                               .order_by('first_name', 'last_name', 'username')
        return managers

    def get_pending_companies(self):
        # Return pending companies
        pending_profiles = self.building_profile.filter(status=CompanyProfile.PENDING)
        return Organization.objects.filter(pk__in=[p.organization.id for p in pending_profiles])

    def get_notices(self):
        notices = self.notices.filter(is_reply=False)\
                              .exclude(sender__profile__status=UserProfile.BANNED)
        banned = [bp['organization__id'] for bp \
                 in self.building_profile.filter(status=CompanyProfile.BANNED).values('organization__id')]
        if banned:
            notices = notices.exclude(sender__profile__company__pk__in=banned)
        return notices

    def mail_managers(self, subject, text_content, html_content=None):
        from_email = settings.EMAIL_FROM
        recipients_list = [manager.email for manager in self.managers]
        if recipients_list:
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipients_list)
            if html_content:
                msg.attach_alternative(html_content, "text/html")
            msg.send()


class CompanyProfile(models.Model):
    PENDING = 0
    VERIFIED = 1
    BANNED = 2
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (VERIFIED, 'Verified'),
        (BANNED, 'Banned'),
    )
    organization = models.ForeignKey(Organization, related_name='company_profile')
    building = models.ForeignKey(Building, null=True, blank=True, related_name='building_profile')
    floor = models.IntegerField("Floor", null=True, blank=True)
    status = models.IntegerField("Verification status", choices=STATUS_CHOICES, default=PENDING)
    directions = models.TextField("Detailed Directions", null=True, blank=True)

    def __unicode__(self):
        if self.building:
            return u'{} at {}'.format(self.organization.name, self.building.name)
        return u'{} [No Building Assigned]'.format(self.organization.name)

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

    def get_status(self):
        return self.get_status_display()


class OToken(models.Model):
    """
    Organization Token.
    A valid token is required in order to create an Organization.

    """
    key = models.CharField(max_length=14, primary_key=True)
    building = models.ForeignKey(Building)
    user = models.ForeignKey(User, null=True, blank=True)
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
    codename = models.CharField(max_length=255, unique=True, null=True, blank=True)
    company = models.ForeignKey(Organization, null=True, blank=True, related_name='company', on_delete=models.SET_NULL)
    building = models.ForeignKey(Building, null=True, blank=True, help_text="Primary building", on_delete=models.SET_NULL)
    starred = models.ManyToManyField(Notice, null=True, blank=True)
    networked = models.ManyToManyField(Organization, null=True, blank=True, related_name='networked')
    thumbnail = models.ImageField(upload_to='./member/%Y/%m/%d', null=True, blank=True, \
                                  help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 60 x 60 pixels or larger.")
    job_title = models.CharField(max_length=64, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    status = models.IntegerField("Verification Status", choices=STATUS_CHOICES, default=PENDING, \
                                 null=True, blank=True)

    def __unicode__(self):
        return self.name

    @property
    def name(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.codename

    @property
    def roles(self):
        roles = self.user.groups.exclude(name='Administrator')
        return [str(g.name) for g in roles]

    @property
    def buildings(self):
        buildings = []
        if self.company:
            profiles = CompanyProfile.objects.filter(organization=self.company)
            buildings = [profile.building for profile in profiles]
        return buildings

    @property
    def token(self):
        try:
            token = Token.objects.get(user=self.user)
            return token.key
        except Token.DoesNotExist:
            return ''

    @property
    def avatar(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            return '{}images/nirit-icon-60x60-grey.png'.format(settings.STATIC_URL)

    @property
    def small_avatar(self):
        if self.thumbnail:
            return self.thumbnail.url
        else:
            return '{}images/nirit-icon-32x32-grey.png'.format(settings.STATIC_URL)

    def is_pending(self):
        return self.status == self.PENDING

    def generate_hash(self):
        # Generate a random binary string
        # Configured to use PBKDF2 + HMAC + SHA256 with 10000 iterations.
        # The result is a 64 byte binary string
        hash = pbkdf2(self.user.username, get_random_string(), 10000, digest=hashlib.sha256)
        self.codename = base64.b64encode(hash).decode('ascii').strip()
        self.save()

    def generate_hash(self):
        # Generate member codename based on his full name
        if not self.codename:
            # Slug format: initials(fullname)/random(1-999)/count(fullname)/random(1-999)*count(fullname)
            groups = self.user.first_name.split()
            groups.extend(self.user.last_name.split())
            initials = ''.join(['{}.'.format(n[0]) for n in groups if n and re.search(r'[^-_0-9a-zA-Z]', n) is None])
            initials = initials.lower()
            count = UserProfile.objects.filter(codename__contains=initials).count()
            slug = '{}/{}/{}/{}'.format(initials, random.randint(1, 999), count, count * random.randint(1, 999))
            self.codename = slug
            self.save()

    def get_starred(self):
        # Convert logged-in user starred notices into list of IDs
        return [int(n.id) for n in self.starred.all()]

    def mail(self, subject, text_content, html_content=None):
        from_email = settings.EMAIL_FROM
        msg = EmailMultiAlternatives(subject, text_content, from_email, [self.user.email])
        if html_content:
            msg.attach_alternative(html_content, "text/html")
        msg.send()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
    else:
        profile = instance.get_profile()
        profile.generate_hash()

def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
post_save.connect(create_auth_token, sender=User)


class Page(models.Model):
    title = models.CharField(max_length=64, unique=True)
    slug = models.CharField(max_length=64, unique=True)
    body = MarkupField()
    status = models.BooleanField("Publish Status", default=False)

    def __unicode__(self):
        return self.title


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    slug = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255,
                               help_text='Please include the postcode')
    geocode = models.ForeignKey(Geocode, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True,
                                help_text="Change the location to ovverride the Geocode")
    type = models.IntegerField(choices=SUPPLIER_TYPES, default=0)
    image = models.ImageField(upload_to='./supplier/%Y/%m/%d', null=True, blank=True, \
                              help_text="PNG, JPEG, or GIF; max size 2 MB. Image must be 626 x 192 pixels or larger.")
    buildings = models.ManyToManyField(Building, null=True, blank=True)

    @property
    def postcode(self):
        if not self.address:
            return None
        postcode = utils.Extractor(self.address).extract_postcode()
        if not postcode:
            return None
        return postcode

    def generate_geocode(self):
        try:
            postcode = self.postcode if self.postcode else 'N/A'
            geocode = Geocode.objects.get(code=postcode)
        except Geocode.DoesNotExist:
            # If the geocode for this postcode has not yet been stored,
            # fetch it
            try:
                point = utils.get_postcode_point(postcode)
            except Exception as e:
                # The function raises an Exception when the postcode does not exist
                # we store the resulst as (0, 0) to avoid fetching the API every time
                point = (0.0, 0.0)
            geocode = Geocode.objects.create(code=postcode, latitude=point[0], longitude=point[1])
        self.geocode = geocode
        self.location = '{},{}'.format(geocode.latitude, geocode.longitude)
        self.save()

    def generate_slug(self):
        # Generate supplier slug
        if not self.slug:
            # Slug format: hyphenise(name)/random(1-999)/count(name)/random(1-999)*(count(name))
            hyphenized = re.sub(r'\s\s*', '-', self.name.lower())
            hyphenized = re.sub(r'[^-_0-9a-z]', '', hyphenized)
            hyphenized = re.sub(r'--+', '-', hyphenized)
            count = Supplier.objects.filter(name=self.name).distinct().count()
            slug = '{}/{}/{}/{}'.format(hyphenized, random.randint(1, 999), count, count * random.randint(1, 999))
            self.slug = slug
            self.save()

def create_supplier_slug(sender, instance, created, **kwargs):
    if not instance.slug:
        instance.generate_slug()

def generate_supplier_location(sender, instance, created, **kwargs):
    if not instance.location:
        instance.generate_geocode()

post_save.connect(create_supplier_slug, sender=Supplier)
post_save.connect(generate_supplier_location, sender=Supplier)
