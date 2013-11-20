# nirit/manager.py
"""
Data Manager.
Low-level API to the Django User ORM.
Provides methods to access or alter Nirit's Users.

"""
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.utils import IntegrityError
from nirit.models import *
from nirit.utils import lookup_email


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

    def create_user(self, email):
        self.trace(['> Create User', '"{}"'.format(email)])
        # Create new user with randomly-generated password
        # the username is the email address
        try:
            validate_email(email)
        except ValidationError as e:
            self.status = 400
            self.response = ', '.join([str(msg) for msg in e.messages])
        else:
            password = User.objects.make_random_password()
            try:
                user = User.objects.create_user(email, email, password)
                self.status = 200
                self.response = password
            except IntegrityError as e:
                self.status = 304
                self.response = e
        return self.respond()

    def create_token(self, space, count):
        self.status = 200
        self.response = ['No token created']
        try:
            space = Space.objects.get(codename=space)
        except Space.DoesNotExist:
            self.status = 404
            self.response = 'Space Not Found'
        else:
            self.response = []
            while count > 0:
                token = OToken()
                token.space = space
                token.save()
                self.response.append(token)
                count -= 1
        return self.respond()

    def list_tokens(self, space):
        self.status = 200
        self.response = []
        try:
            space = Space.objects.get(codename=space)
        except Space.DoesNotExist:
            self.status = 404
        else:
            # return valid tokens
            tokens = OToken.objects.filter(space=space, redeemed=False)
            self.response.extend(list(tokens))
        return self.respond()

    def set_preference(self, user, preference, value):
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            self.status = 404
            self.response = 'User Not Found'
        else:
            self.trace('> Set "{}" preference to "{}"'.format(preference, value))
            if preference == 'active-space':
                try:
                    space = Space.objects.get(pk=value)
                except Space.DoesNotExist:
                    self.status = 404
                    self.response = 'Space Not Found'
                else:
                    # make sure the user is a member of this Space
                    if user in space.members:
                        user.get_profile().space = space
                        user.get_profile().save()
                        self.status = 200
                        self.response = 'Active Space Set'
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
                    if organization in user.get_profile().networked.all():
                        action = 'Removed from'
                        user.get_profile().networked.remove(organization)
                    else:
                        action = 'Added to'
                        user.get_profile().networked.add(organization)
                    self.status = 200
                    self.response = 'Organization {} Network.'.format(action)
            elif preference == 'starred':
                try:
                    notice = Notice.objects.get(pk=value)
                except Notice.DoesNotExist:
                    self.status = 404
                    self.response = 'Notice Not Found'
                else:
                    if notice in user.get_profile().starred.all():
                        action = 'Unflagged'
                        user.get_profile().starred.remove(notice)
                    else:
                        action = 'Flagged'
                        user.get_profile().starred.add(notice)
                    self.status = 200
                    self.response = 'Notice {} as Starred.'.format(action)
        return self.respond()

    def lookup_email(self, email):
        self.status = 404
        self.response = 'No Match Found'
        company = lookup_email(email)
        if company:
            self.status = 200
            self.response = company
        return self.respond()
