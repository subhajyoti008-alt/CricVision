from django.contrib import admin

from .models import Team

# Register your models here.

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "city", "captain")
    search_fields = ("name", "short_name", "city")
    filter_horizontal = ("players",)

