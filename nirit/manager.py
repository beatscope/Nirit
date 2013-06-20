# nirit/manager.py
"""
Data Manager.
Low-level API to the Django ORM. Provides methods to access to alter Nirit's data.

"""
import hashlib
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Permission, User, Group
from django.contrib.contenttypes.models import ContentType
from django.db.utils import IntegrityError
from nirit.models import *


class ModelManager(object):
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.status = 501
        self.response = 'Not Implemented'

    def trace(self, stack):
        if self.verbose:
            if type(stack) is list:
                print " ".join(["{!s}".format(s) for s in stack])
            else:
                print stack

    def respond(self):
        return {
            'status': self.status,
            'response': self.response
        }

    def create(self, name, value):
        self.trace(['> Create', name, '"{}"'.format(value)])
        # Building
        if name == 'building':
            codename = hashlib.sha256(value).hexdigest()
            instance = Building()
            instance.name = value
            instance.codename = codename
            try:
                instance.save()
            except IntegrityError:
                self.status = 304
                self.response = 'Not Modified'
            else:
                self.status = 200
                self.response = instance
                # Create the permission if the creation was successful
                content_type = ContentType.objects.get(app_label='nirit', model='building')
                permission_name = 'Can access building "{}"'.format(value)
                permission_codename = 'can_access_building_{}'.format(codename)
                self.trace("> Create permission '{}'".format(permission_name))
                permission = Permission.objects.create(codename=permission_codename, name=permission_name, content_type=content_type)
        # Organization
        elif name == 'organization':
            codename = hashlib.sha256(value).hexdigest()
            instance = Organization()
            instance.name = value
            instance.codename = codename
            try:
                instance.save()
            except IntegrityError:
                self.status = 304
                self.response = 'Not Modified'
            else:
                self.status = 200
                self.response = instance
                # Create the permission if the creation was successful
                content_type = ContentType.objects.get(app_label='nirit', model='organization')
                permission_name = 'Can access organization "{}"'.format(value)
                permission_codename = 'can_access_organization_{}'.format(codename)
                self.trace("> Create permission '{}'".format(permission_name))
                permission = Permission.objects.create(codename=permission_codename, name=permission_name, content_type=content_type)
        # User
        elif name == 'user':
            # Create new user with randomly-generated password
            # the username is the email address
            try:
                validate_email(value)
            except ValidationError as e:
                self.status = 400
                self.response = ', '.join([str(msg) for msg in e.messages])
            else:
                password = User.objects.make_random_password()
                try:
                    user = User.objects.create_user(value, value, password)
                    self.status = 200
                    self.response = password
                except IntegrityError:
                    self.status = 304
                    self.response = '"{}" already exists.'.format(value)
        # Group
        elif name == 'group':
            group = Group()
            group.name = value
            try:
                group.save()
            except IntegrityError:
                self.status = 304
                self.response = 'Not Modified'
            else:
                self.status = 200
                self.response = group
        return self.respond()

    def add(self, name, member, group):
        self.trace(['> Add', name, '"{}"'.format(member), 'to', '"{}"'.format(group)])
        if name == 'organization':
            try:
                # Find Organization
                try:
                    id = int(member)
                    organization = Organization.objects.get(pk=id)
                except ValueError:
                    organization = Organization.objects.get(name=member)
            except Organization.DoesNotExist:
                self.status = 404
                self.response = "Organization Not Found"
            else:
                self.trace(['> Organization:', organization])
                try:
                    # Find Building
                    try:
                        id = int(group)
                        building = Building.objects.get(pk=id)
                    except ValueError:
                        building = Building.objects.get(name=group)
                except Building.DoesNotExist:
                    self.status = 404
                    self.response = "Building Not Found"
                else:
                    self.trace(['> Building:', building])
                    building.organizations.add(organization)
                    self.status = 200
                    self.response = 'OK'
        elif name == 'user_to_organization':
            try:
                # Find User
                user = User.objects.get(username=member)
            except User.DoesNotExist:
                self.status = 404
                self.response = "User Not Found"
            else:
                self.trace(['> User:', user])
                try:
                    # Find Organization
                    try:
                        id = int(group)
                        organization = Organization.objects.get(pk=id)
                    except ValueError:
                        organization = Organization.objects.get(name=group)
                except Organization.DoesNotExist:
                    self.status = 404
                    self.response = "Organization Not Found"
                else:
                    self.trace(['> Organization:', organization])
                    organization.members.add(user)
                    self.status = 200
                    self.response = 'OK'
        elif name == 'user_to_group':
            try:
                # Find User
                user = User.objects.get(username=member)
            except User.DoesNotExist:
                self.status = 404
                self.response = "User Not Found"
            else:
                self.trace(['> User:', user])
                try:
                    # Find Group
                    try:
                        id = int(group)
                        group = Group.objects.get(pk=id)
                    except ValueError:
                        group = Group.objects.get(name=group)
                except Group.DoesNotExist:
                    self.status = 404
                    self.response = "Group Not Found"
                else:
                    self.trace(['> Group:', group])
                    user.groups.add(group)
                    self.status = 200
                    self.response = 'OK'
        return self.respond()

    def remove(self, name, member, group):
        self.trace(['> Remove', name, '"{}"'.format(member), 'from', '"{}"'.format(group)])
        if name == 'organization':
            try:
                # Find Organization
                try:
                    id = int(member)
                    organization = Organization.objects.get(pk=id)
                except ValueError:
                    organization = Organization.objects.get(name=member)
            except Organization.DoesNotExist:
                self.status = 404
                self.response = "Organization Not Found"
            else:
                self.trace(['> Organization:', organization])
                try:
                    # Find Building
                    try:
                        id = int(group)
                        building = Building.objects.get(pk=id)
                    except ValueError:
                        building = Building.objects.get(name=group)
                except Building.DoesNotExist:
                    self.status = 404
                    self.response = "Building Not Found"
                else:
                    self.trace(['> Building:', building])
                    building.organizations.remove(organization)
                    self.status = 200
                    self.response = 'OK'
        elif name == 'user_from_organization':
            try:
                # Find User
                user = User.objects.get(username=member)
            except Organization.DoesNotExist:
                self.status = 404
                self.response = "User Not Found"
            else:
                self.trace(['> User:', user])
                try:
                    # Find Organization
                    try:
                        id = int(group)
                        organization = Organization.objects.get(pk=id)
                    except ValueError:
                        organization = Organization.objects.get(name=group)
                except Organization.DoesNotExist:
                    self.status = 404
                    self.response = "Organization Not Found"
                else:
                    self.trace(['> Organization:', organization])
                    organization.members.remove(user)
                    self.status = 200
                    self.response = 'OK'
        elif name == 'user_from_group':
            try:
                # Find User
                user = User.objects.get(username=member)
            except User.DoesNotExist:
                self.status = 404
                self.response = "User Not Found"
            else:
                self.trace(['> User:', user])
                try:
                    # Find Group
                    try:
                        id = int(group)
                        group = Group.objects.get(pk=id)
                    except ValueError:
                        group = Group.objects.get(name=group)
                except Group.DoesNotExist:
                    self.status = 404
                    self.response = "Group Not Found"
                else:
                    self.trace(['> Group:', group])
                    user.groups.remove(group)
                    self.status = 200
                    self.response = 'OK'
        return self.respond()

    def post(self, name, subject, sender, buildings=None, nid=None, notice_type=None, is_official=False):
        stack = ['> Post', name, '"{}"'.format(subject), 'from', sender]
        if buildings:
            stack.extend(['to', buildings])
        if nid:
            stack.extend(['to', nid])
        if notice_type is not None:
            stack.extend([typ[1] for typ in Notice.TYPES if typ[0] == notice_type])
        self.trace(stack)
        try:
            sender = User.objects.get(username=sender)
        except User.DoesNotExist:
            self.status = 404
            self.response = "User Not Found."
        else:
            if subject: # subject is required
                # Create new notice if no recipient given
                # Building(s) to assign Notice to is(are) required
                if name == 'notice':
                    _buildings = []
                    for id in [b.strip() for b in buildings.split(',')]:
                        try:
                            id = int(id)
                        except ValueError:
                            _buildings = [] # reset list
                            self.status = 400
                            self.response = 'Building ID(s) required.'
                            break
                        else:
                            try:
                                _buildings.append(Building.objects.get(pk=id))
                            except Building.DoesNotExist:
                                _buildings = [] # reset list
                                self.status = 404
                                self.response = 'Building Not Found.'
                                break
                    if _buildings:
                        notice = Notice()
                        notice.subject = subject
                        notice.sender = sender
                        notice.is_official = is_official
                        if notice_type is not None and notice_type in (Notice.NOTICE, Notice.INFO):
                            notice.type = notice_type
                        notice.save()
                        for b in _buildings:
                            # make sure the user is a member of this Building
                            if sender in b.members or sender.is_superuser:
                                b.notices.add(notice)
                        self.status = 200
                        self.response = notice
                    else:
                        self.status = 400
                        self.response = "At least 1 Building ID is required."
                # Reply to Notice
                elif name == 'reply':
                    try:
                        recipient_notice = Notice.objects.get(pk=nid)
                    except Notice.DoesNotExist:
                        self.status = 404
                        self.response = "Notice #{} Does Not Exist".format(nid)
                    else:
                        notice = Notice()
                        notice.subject = subject
                        notice.sender = sender
                        notice.is_official = is_official
                        notice.is_reply = True
                        notice.reply_to = recipient_notice
                        notice.save()
                        for building in recipient_notice.building_set.all():
                            building.notices.add(notice)
                        self.status = 200
                        self.response = notice
        return self.respond()

    def reply(self):
        self.trace('> Reply')
        return self.respond()

    def delete(self, name, value):
        self.trace(['> Delete', name, value])
        if name == 'user':
            # Users are looked-up using their email address
            try:
                user = User.objects.get(username=value)
            except User.DoesNotExist:
                self.status = 404
                self.response = 'User Not Found'
            else:
                user.delete()
                self.status = 200
                self.response = 'OK'
        else:
            try:
                id = int(value)
            except ValueError:
                self.status = 400
                self.response = "ID needs to be an integer."
            else:
                if name == 'building':
                    try:
                        instance = Building.objects.get(pk=id)
                    except Building.DoesNotExist:
                        self.status = 404
                        self.response = 'Building Not Found'
                    else:
                        instance.delete()
                        # Delete Building permission
                        permission = Permission.objects.get(codename='can_access_building_{}'.format(instance.codename))
                        permission.delete()
                        self.status = 200
                        self.response = 'OK'
                elif name == 'organization':
                    try:
                        instance = Organization.objects.get(pk=id)
                    except Organization.DoesNotExist:
                        self.status = 404
                        self.response = 'Organization Not Found'
                    else:
                        instance.delete()
                        # Delete Organization permission
                        permission = Permission.objects.get(codename='can_access_organization_{}'.format(instance.codename))
                        permission.delete()
                        self.status = 200
                        self.response = 'OK'
                elif name == 'group':
                    try:
                        group = Group.objects.get(pk=id)
                    except Group.DoesNotExist:
                        self.status = 404
                        self.response = 'Group Not Found'
                    else:
                        group.delete()
                        self.status = 200
                        self.response = 'OK'
                elif name == 'notice':
                    try:
                        notice = Notice.objects.get(pk=id)
                    except Notice.DoesNotExist:
                        self.status = 404
                        self.response = 'Notice Not Found'
                    else:
                        notice.delete()
                        self.status = 200
                        self.response = 'OK'
        return self.respond()

    def set_preference(self, user, preference, value):
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            self.status = 404
            self.response = 'User Not Found'
        else:
            self.trace('> Set "{}" preference to "{}"'.format(preference, value))
            if preference == 'active-building':
                try:
                    building = Building.objects.get(pk=value)
                except Building.DoesNotExist:
                    self.status = 404
                    self.response = 'Building Not Found'
                else:
                    # make sure the user is a member of this Building
                    if user in building.members:
                        user.userprofile.building = building
                        user.userprofile.save()
                        self.status = 200
                        self.response = 'Active Building Set'
                    else:
                        self.status = 401
                        self.response = 'Not a Member'
            elif preference == 'network':
                try:
                    organization = Organization.objects.get(pk=value)
                except Organization.DoesNotExist:
                    self.status = 404
                    self.response = 'Organization Not Found'
                else:
                    if organization in user.userprofile.networked.all():
                        action = 'Removed from'
                        user.userprofile.networked.remove(organization)
                    else:
                        action = 'Added to'
                        user.userprofile.networked.add(organization)
                    self.status = 200
                    self.response = 'Organization {} Network.'.format(action)
            elif preference == 'starred':
                try:
                    notice = Notice.objects.get(pk=value)
                except Notice.DoesNotExist:
                    self.status = 404
                    self.response = 'Notice Not Found'
                else:
                    if notice in user.userprofile.starred.all():
                        action = 'Unflagged'
                        user.userprofile.starred.remove(notice)
                    else:
                        action = 'Flagged'
                        user.userprofile.starred.add(notice)
                    self.status = 200
                    self.response = 'Notice {} as Starred.'.format(action)
        return self.respond()

    def show(self, name, value):
        self.trace(['> Show', name, '"{}"'.format(value)])
        if name == 'building':
            try:
                instance = Building.objects.get(name=value)
            except Building.DoesNotExist:
                self.status = 404
                self.response = 'Building Not Found'
            else:
                self.status = 200
                self.response = instance
        elif name == 'organization':
            try:
                instance = Organization.objects.get(name=value)
            except Organization.DoesNotExist:
                self.status = 404
                self.response = 'Organization Not Found'
            else:
                self.status = 200
                self.response = instance
        elif name == 'user':
            try:
                user = User.objects.get(username=value)
            except User.DoesNotExist:
                self.status = 404
                self.response = 'User Not Found'
            else:
                self.status = 200
                user_profile = user.get_profile()
                self.response = (user.id, user, {
                    'active-building': user_profile.building,
                    'starred-notices': user_profile.starred.all(),
                    'networked-organizations': user_profile.networked.all()
                })
        elif name == 'group':
            try:
                group = Group.objects.get(name=value)
            except Group.DoesNotExist:
                self.status = 404
                self.response = 'Group Not Found'
            else:
                self.status = 200
                self.response = [group.id, group]
        elif name == 'notice':
            try:
                notice = Notice.objects.get(pk=value)
            except Notice.DoesNotExist:
                self.status = 404
                self.response = 'Notice Not Found'
            else:
                self.status = 200
                self.response = notice
        return self.respond()
