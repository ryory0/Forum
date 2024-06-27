from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserActivateTokens, ViewHistory, Thread, Comment

class UserActivateTokensAdmin(admin.ModelAdmin):
    list_display = ('token_id', 'user', 'activate_token', 'expired_at')

admin.site.register(User, UserAdmin)
admin.site.register(Thread)
admin.site.register(Comment)
admin.site.register(UserActivateTokens, UserActivateTokensAdmin)
admin.site.register(ViewHistory)