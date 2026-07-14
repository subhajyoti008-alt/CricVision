from django.contrib import admin

from .models import Tournament

# Register your models here.
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "competition_type", 
        "city", 
        "format",
        "start_date",
        "end_date",
        "is_published",
    )

    list_filter = (
        "competition_type",
        "format",
        "is_published",
        "city"
        )
    
    search_fields = ("name", "city", "venue")
    filter_horizontal = ("teams",)
