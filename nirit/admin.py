# nirit/admin.py
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from nirit.models import Building, Organization, Notice, Expertise, UserProfile
from nirit.actions import force_delete_selected

class BackOffice(admin.sites.AdminSite):
    pass

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(UserAdmin):
    inlines = (UserProfileInline, )

class BuildingAdmin(admin.ModelAdmin):
    # Override delete() bulk action to use Model.delete()
    # this is to delete the Permission on delete
    actions = [force_delete_selected]

    def get_actions(self, request):
        actions = super(BuildingAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

class OrganizationAdmin(admin.ModelAdmin):
    # Override delete() bulk action to use Model.delete()
    # this is to delete the Permission on delete
    actions = [force_delete_selected]

    def get_actions(self, request):
        actions = super(OrganizationAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


site = BackOffice()
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)
site.register(Building)
site.register(Organization, OrganizationAdmin)
site.register(Notice)
site.register(Expertise)
