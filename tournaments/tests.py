import tempfile
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from accounts.models import UserProfile

from .forms import PlayerTournamentRegistrationForm
from .models import Tournament


class PlayerRegistrationFormTests(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="CricVision Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
            is_published=True,
        )

    def create_test_photo(self):
        image = Image.new("RGB", (1, 1), "white")
        image_buffer = BytesIO()

        image.save(image_buffer, format="PNG")

        return SimpleUploadedFile(
            "rahul.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

    def test_player_can_register_for_a_tournament(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                form = PlayerTournamentRegistrationForm(
                    data={
                        "username": "rahul_kumar",
                        "password": "StrongPassword123!",
                        "password_confirm": "StrongPassword123!",
                        "email": "rahul@example.com",
                        "full_name": "Rahul Kumar",
                        "phone_number": "9876543210",
                        "date_of_birth": "2008-05-10",
                        "city": "Kolkata",
                        "batting_style": "RIGHT",
                        "bowling_style": "PACE",
                        "tournament": self.tournament.id,
                    },
                    files={
                        "profile_photo": self.create_test_photo(),
                    },
                )

                self.assertTrue(form.is_valid(), form.errors)

                registration = form.save()

                User = get_user_model()
                user = User.objects.get(
                    username="rahul_kumar"
                )

                self.assertEqual(
                    user.profile.role,
                    UserProfile.Role.PLAYER,
                )

                self.assertEqual(
                    user.player_profile.full_name,
                    "Rahul Kumar",
                )

                self.assertTrue(
                    user.player_profile.profile_photo.name.startswith(
                        "player_photos/"
                    )
                )

                self.assertEqual(
                    registration.tournament,
                    self.tournament,
                )

                self.assertEqual(
                    registration.status,
                    "PENDING",
                )

                self.assertEqual(
                    registration.payment_status,
                    "UNPAID",
                )