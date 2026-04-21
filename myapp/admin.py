from django.contrib import admin
from .models import User, Election, Candidate

# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
    list_filter = ('role',)
    search_fields = ('username', 'email')

admin.site.register(Election)
admin.site.register(Candidate)