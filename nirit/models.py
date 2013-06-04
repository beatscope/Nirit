# nirit/models.py
import logging
import re
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

logger = logging.getLogger('nirit.models')


class Notice(models.Model):
    INFO = 0
    NOTICE = 1
    TYPES = (
        (INFO, 'INFO'),
        (NOTICE, 'NOTICE')
    )
    subject = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
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

    def get_replies(self):
        return Notice.objects.filter(reply_to=self)


class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True)
    codename = models.CharField(max_length=64, unique=True)
    members = models.ManyToManyField(User)
    summary = models.TextField("Short Description", null=True)
    description = models.TextField("Long Description", null=True)
    department = models.CharField(max_length=255, null=True)
    floor = models.IntegerField(null=True)
    keywords = models.CharField("Keywords/Crafts", max_length=255, null=True)
    size = models.CharField("Company Size", max_length=255, null=True)
    formed = models.DateField(null=True)
    joined = models.DateField(auto_now_add=True)
    status = models.IntegerField(default=0)

    def __unicode__(self):
        return "[#{}] {}".format(self.id, self.name)

    @property
    def slug(self):
        return re.sub(r'\s', '-', self.name).lower()

    @property
    def link(self):
        return '{}/{}'.format(self.slug, self.codename)


class Building(models.Model):
    name = models.CharField(max_length=200, unique=True)
    codename = models.CharField(max_length=64, unique=True)
    organizations = models.ManyToManyField(Organization)
    notices = models.ManyToManyField(Notice)

    def __unicode__(self):
        return "[#{}] {}".format(self.id, self.name)

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
        Building Managers are not considered members.

        """
        members = []
        for o in self.organizations.all():
            members.extend(o.members.filter(groups__name__in=['Owner','Rep','Staff']))
        return members


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    building = models.ForeignKey(Building, null=True)
    starred = models.ManyToManyField(Notice)
    networked = models.ManyToManyField(Organization)

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
