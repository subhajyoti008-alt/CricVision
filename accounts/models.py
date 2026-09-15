from django.conf import settings
from django.db import models

# Create your models here.

class UserProfile(models.Model):
    class Role(models.TextChoices):
        PLAYER = "PLAYER", "Player"
        TEAM_OWNER = "TEAM_OWNER", "Team Owner"
        ORGANIZER = "ORGANIZER", "Organizer"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name = "profile",
    )
    role = models.CharField(
        max_length=20,
        choices = Role.choices,
        default = Role.PLAYER,
    )
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"