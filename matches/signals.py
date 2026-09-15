from django.db.models.signals import post_save
from django.dispatch import receiver

from tournaments.services import rebuild_points_table

from .models import Match


@receiver(post_save, sender=Match)
def update_points_table_when_match_is_saved(sender, instance, **kwargs):
    if (
        instance.tournament_id
        and instance.status in ["COMPLETED", "ABANDONED"]
    ):
        rebuild_points_table(instance.tournament)