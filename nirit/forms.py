# nirit/forms.py
import logging
import re
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins, EmailMultiAlternatives
from django import forms
from django.conf import settings
from django.utils.encoding import smart_str
from django.utils.http import int_to_base36
from django.template import loader
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from nirit.models import Organization, OToken, UserProfile
from nirit.utils import validate_year, lookup_email
from nirit.widgets import ImageWidget
from nirit.fixtures import Message

logger = logging.getLogger('nirit.forms')


class PassResetForm(PasswordResetForm):
    """
    Override PasswordResetForm,
    to allow email sent to use HTML format.

    """
    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        for user in self.users_cache:
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            c = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.pk),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            subject = loader.render_to_string('messages/emails/password_reset_subject.txt', c)
            # Email subject *must not* contain newlines
            subject = ''.join(subject.splitlines())
            text_content = loader.render_to_string('messages/emails/password_reset.txt', c)
            html_content = loader.render_to_string('messages/emails/password_reset.html', c)
            msg = EmailMultiAlternatives(subject, text_content, from_email, [user.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        widgets = {
            'image': ImageWidget(),
            'logo': ImageWidget(),
            'square_logo': ImageWidget(),
        }

    def clean_founded(self):
        year = self.cleaned_data['founded']
        # founded needs to be a valid year
        # validate_year raise a ValidationError exception if the year is not valid
        validate_year(year)
        return year

class CompanyForm(OrganizationForm):
    floor = forms.IntegerField(label='Floor')
    directions = forms.CharField(label='Detailed Directions', widget=forms.Textarea, required=False, help_text="\
                 Detailed desription on how to find your office within the building.\
                 e.g.: turn right coming out of the lift, opposite the kitchen.")

    def save(self, commit=True):
        organization = super(CompanyForm, self).save(commit)
        # Return list of additional data,
        # as well as the organization object
        return {
            'organization': organization,
            'floor': self.cleaned_data['floor'],
            'directions': self.cleaned_data['directions'],
        }


class SignUpForm(forms.Form):
    first_name = forms.CharField(label='First name', max_length=30)
    last_name = forms.CharField(label='Last name', max_length=30)
    email = forms.EmailField(label='Email Address', 
            help_text="Your email will not be shared with any third parties or be used for the purposes of marketing products or services other than Nirit.")
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    auth_code = forms.CharField(label='Authorization Code', max_length=30, required=False,
                help_text="You need a valid <strong>Authorization Code</strong> to be able to create a "\
                         +"<strong>Business Profile</strong> for your <strong>Company</strong>."\
                         +"<p>If you would like to register your <strong>Company</strong>, "\
                         +"please contact us using <a href=\"javascript:void(0)\" data-uv-lightbox=\"classic_widget\""\
                         +" data-uv-mode=\"support\" data-uv-primary-color=\"#ced9e4\" data-uv-link-color=\"#2e7fa1\">this form</a>, "\
                         +"and we\'ll generate a new <strong>Authorization Code</strong> for you.</p>")
    agreed = forms.BooleanField()

    def check_username(self, count=0):
        if not self.cleaned_data.has_key("first_name") or not self.cleaned_data.has_key("last_name"):
            return ''
        # Since User.username is unique, this check is redundant,
        # but we use this check to recursively generate a unique username
        username = '{!s}_{!s}'.format(smart_str(self.cleaned_data["first_name"]).lower(), 
                                      smart_str(self.cleaned_data["last_name"]).lower())
        # Replace characters other that [\w.@+-]
        username = re.sub('[^\w.@+-]', '', username)
        # the username field is limited to 30 characters
        if count:
            if count < 10:
                username = '{}_{}'.format(username[:28], count)
            elif count < 100:
                username = '{}_{}'.format(username[:27], count)
            else:
                username = '{}_{}'.format(username[:26], count)
        else:
            username = username[:30]
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        count += 1
        return self.check_username(count=count)

    def clean_email(self):
        # Email is required
        if not self.cleaned_data.has_key("email"):
            raise forms.ValidationError('Email address is required.')
        # Check whether this email has already been registered
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('A user with that email address already exists.')

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        # Generate username
        cleaned_data['username'] = self.check_username()
        cleaned_data['company'] = None
        # Check if an Authorization Code was provided
        if cleaned_data.has_key('auth_code') and cleaned_data['auth_code']:
            # Check the validity of the code
            if not OToken().is_valid(cleaned_data['auth_code']):
                message = Message().get('invalid_token')
                raise ValidationError(message)
        else:
            # The user is trying to join an existing company
            # Find the company associated with this email address
            if cleaned_data.has_key('email'):
                company = lookup_email(cleaned_data['email'])
                if not company:
                    # Email admins
                    # make sure we only do that if the T&Cs have been checked though
                    # also make sure the passord is set as it is cleared when errors are found,
                    # so we might have someone submitting and forgetting to re-type the password
                    if cleaned_data.has_key('agreed') and cleaned_data['agreed'] and cleaned_data.has_key('password'):
                        subject = 'An Account Sign-Up has Failed'
                        data = {
                            'contact': ', '.join([
                                'First Name: {}'.format(cleaned_data['first_name'] if cleaned_data.has_key('first_name') else ''),
                                'Last Name: {}'.format(cleaned_data['last_name'] if cleaned_data.has_key('last_name') else ''),
                                'Email: {}'.format(cleaned_data['email'] if cleaned_data.has_key('email') else ''),
                                'BAC: {}'.format(cleaned_data['auth_code'] if cleaned_data.has_key('auth_code') else ''),
                            ]),
                        }
                        text_content = Message().get('email_sign_up_failed_text', data)
                        html_content = Message().get('email_sign_up_failed_html', data)
                        mail_admins(subject, text_content, html_message=html_content)

                    message = Message().get('email_failed')
                    raise ValidationError(message)
                else:
                    cleaned_data['company'] = company
        return cleaned_data

    def save(self, commit=True):
        # Generate random username based on first and last names
        user = User.objects.create_user(self.cleaned_data["username"], 
                                        self.cleaned_data["email"], 
                                        self.cleaned_data["password"])
        if commit:
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.save()
            if self.cleaned_data['company']:
                # The User is a Staff Member
                user.groups.add(Group.objects.get(name='Staff'))
                # Assign it to the Company
                profile = user.get_profile()
                profile.company = self.cleaned_data['company']
                profile.save()
            else:
                # The User is the Owner of a Company
                # User will be able to create a Business Profile when he confirms his email address
                user.groups.add(Group.objects.get(name='Owner'))
                # Assign the token building to the User
                t = OToken.objects.get(key=self.cleaned_data['auth_code'])
                t.user = user
                t.save() # we assign the user to the token as well to keep a record of who redeemed it
                profile = user.get_profile()
                profile.building = t.building
                profile.status = UserProfile.VERIFIED # activate user
                profile.save()
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User

    def clean_first_name(self):
        # first name is required
        firstname = self.cleaned_data["first_name"]
        if not firstname:
            raise ValidationError('First name is required.')
        return firstname

    def clean_last_name(self):
        # Last name is required
        lastname = self.cleaned_data["last_name"]
        if not lastname:
            raise ValidationError('Last name is required.')
        return lastname

    def clean_email(self):
        # Email address is required
        email = self.cleaned_data["email"]
        if not email:
            raise ValidationError('Email address is required.')
        # Check whether this email has already been registered
        if email == self.instance.email:
            # skip the check if the email is the existing email
            return email
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('A user with that email address already exists.')


class MemberForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        widgets = {
            'thumbnail': ImageWidget(),
        }
