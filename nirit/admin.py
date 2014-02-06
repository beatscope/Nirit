# nirit/admin.py
from django.contrib import admin
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from nirit.models import Space, Organization, Notice, Expertise, \
                         UserProfile, CompanyProfile, Page, OToken, Supplier, \
                         Geocode

class BackOffice(admin.sites.AdminSite):
    pass

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(UserAdmin):
    list_display = ('profile', 'space', 'company', 'email', 'token', 'is_staff')
    list_filter = ('profile__space__name', 'profile__company__name')
    inlines = (UserProfileInline, )

    def space(self, obj):
        if obj.profile.space:
            return obj.profile.space.name
        else:
            return '-'
    space.short_description = 'Space'

    def company(self, obj):
        if obj.profile.company:
            return obj.profile.company.name
        else:
            return '-'
    company.short_description = 'Company'

    def token(self, obj):
        try:
            token = OToken.objects.get(user=obj)
            return token.key
        except OToken.DoesNotExist:
            return ''

class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'postcode', 'geocode', 'created')
    list_editable = ['postcode']

    def get_actions(self, request):
        actions = super(SpaceAdmin, self).get_actions(request)
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

class NoticeAdmin(admin.ModelAdmin):
    list_filter = ('space', 'sender__profile__company')

class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'status')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'address', 'postcode', 'location', 'locations')
    list_filter = ('spaces',)

    def postcode(self, obj):
        if obj.postcode:
            return obj.postcode
        else:
            return '-'

    def locations(self, obj):
        if obj.spaces.count():
            return ', '.join([str(b) for b in obj.spaces.all()])
        else:
            return '-'
    locations.short_description = 'Spaces'

class GeocodeAdmin(admin.ModelAdmin):
    list_display = ('code', '__unicode__')
    search_fields = ('code',)


site = BackOffice()
site.register(User, UserAdmin)
site.register(Group, GroupAdmin)
site.register(Space, SpaceAdmin)
site.register(Organization, OrganizationAdmin)
site.register(Notice, NoticeAdmin)
site.register(Expertise)
site.register(Page, PageAdmin)
site.register(Supplier, SupplierAdmin)
site.register(Geocode, GeocodeAdmin)
