from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'name')
    search_fields = ('user__username','user__fisrt_name', 'user__last_name',
                     'user__email') 
