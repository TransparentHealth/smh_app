from django.contrib import admin

from .models import Organization, ResourceGrant, ResourceRequest


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(ResourceGrant)
class ResourceGrantAdmin(admin.ModelAdmin):
    search_fields = ('organization__name', 'user__username')


@admin.register(ResourceRequest)
class ResourceRequestAdmin(admin.ModelAdmin):
    search_fields = ('organization__name', 'member__username', 'user__username')
