from django.contrib import admin

from .models import Organization, ResourceGrant


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(ResourceGrant)
class ResourceGrantAdmin(admin.ModelAdmin):
    search_fields = ('organization__name', 'user__username')
