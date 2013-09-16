# nirit/admin.py
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from nirit.models import Building, Organization, Notice, Expertise, \
                         UserProfile, CompanyProfile, Page

class BackOffice(admin.sites.AdminSite):
    pass

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(UserAdmin):
    list_display = ('profile', 'building', 'company', 'username', 'email', 'is_staff')
    list_filter = ('profile__building__name', 'profile__company__name')
    inlines = (UserProfileInline, )

    def building(self, obj):
        if obj.profile.building:
            return obj.profile.building.name
        else:
            return '-'
    building.short_description = 'Building'

    def company(self, obj):
        if obj.profile.company:
            return obj.profile.company.name
        else:
            return '-'
    company.short_description = 'Company'

class BuildingAdmin(admin.ModelAdmin):

    def get_actions(self, request):
        actions = super(BuildingAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

class CompanyProfileInline(admin.StackedInline):
    model = CompanyProfile
    extra = 0

class OrganizationAdmin(admin.ModelAdmin):
    inlines = (CompanyProfileInline, )

    def get_actions(self, request):
        actions = super(OrganizationAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status')


site = BackOffice()
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)
site.register(Building, BuildingAdmin)
site.register(Organization, OrganizationAdmin)
site.register(Notice)
site.register(Expertise)
site.register(Page, PageAdmin)
