import tempfile
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import UserProfile

from .forms import PlayerTournamentRegistrationForm
from .models import Tournament, Registration
from .models import Payment
from .services import submit_player_payment
from players.models import Player



class PlayerRegistrationFormTests(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="CricVision Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
            is_published=True,
            entry_fee=100,
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


    def test_player_can_submit_online_payment(self):
        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                form = PlayerTournamentRegistrationForm(
                    data={
                        "username": "payment_player",
                        "password": "StrongPassword123!",
                        "password_confirm": "StrongPassword123!",
                        "email": "payment@example.com",
                        "full_name": "Payment Player",
                        "phone_number": "9876543211",
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
                user = registration.player.user

                payment = submit_player_payment(
                    registration=registration,
                    user=user,
                    method="ONLINE",
                    transaction_reference="TEST-UPI-1234",
                )

                self.assertEqual(Payment.objects.count(), 1)
                self.assertEqual(payment.method, "ONLINE")
                self.assertEqual(payment.status, "PENDING")
                self.assertEqual(
                    payment.amount,
                    self.tournament.entry_fee,
                )

                registration.refresh_from_db()

                self.assertEqual(
                    registration.payment_status,
                    "PENDING",
                )

    def test_my_registrations_requires_login(self):
        url = reverse("tournaments:my_registrations")

        response = self.client.get(url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={url}",
        )


def test_player_only_sees_own_registrations(self):
    User = get_user_model()

    current_user = User.objects.create_user(
        username="current_player",
        password="StrongPassword123!",
    )

    current_player = Player.objects.create(
        user=current_user,
        full_name="Current Player",
    )

    Registration.objects.create(
        player=current_player,
        tournament=self.tournament,
    )

    other_user = User.objects.create_user(
        username="other_player",
        password="StrongPassword123!",
    )

    other_player = Player.objects.create(
        user=other_user,
        full_name="Other Player",
    )

    other_tournament = Tournament.objects.create(
        name="Private Other Player Cup",
        city="Kolkata",
        start_date=date(2026, 12, 5),
        end_date=date(2026, 12, 7),
        is_published=True,
    )

    Registration.objects.create(
        player=other_player,
        tournament=other_tournament,
    )

    self.client.force_login(current_user)

    response = self.client.get(
        reverse("tournaments:my_registrations")
    )

    self.assertEqual(response.status_code, 200)

    self.assertContains(
        response,
        self.tournament.name,
    )

    self.assertNotContains(
        response,
        other_tournament.name,
    )