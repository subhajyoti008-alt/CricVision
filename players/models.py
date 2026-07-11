from django.db import models

# Create your models here.

class Player(models.Model):
    BATTING_STYLES = [
        ("RIGHT", "Right-hand bat"),
        ("LEFT", "Left-hand bat"),
    ]

    BOWLING_STYLES = [
        ("NONE", "Dose not bowl"),
        ("PACE", "Fast / Medium pace"), 
        ("OFF_SPIN", "Off spin"),
        ("LEG_SPIN", "let-spin"),
        ("LEFT_ARM", "Left-arm spin"),
    ]

    full_name = models.CharField(max_length=120)
    date_of_birth = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=80, blank=True)

    batting_style = models.CharField(
        max_length=10, 
        choices = BATTING_STYLES,
        default="RIGHT",
    )
    bowling_style = models.CharField(
        max_length=15,
        choices = BOWLING_STYLES,
        default="NONE",
    )

    is_wicketkeeper = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name