from django.contrib import admin
from .models import Player

# Register your models here.
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "city", 
        "batting_style",
        "bowling_style",
        "is_wicketkeeper",
    )

    list_filter = ("batting_style", "bowling_style", "is_wicketkeeper")
    search_fields = ("full_name", "city")
    
