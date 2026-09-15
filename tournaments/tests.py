from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import UserProfile

from .forms import PlayerTournamentRegistrationForm
from .models import Tournament


# Create your tests here.

class PlayerRegistrationFormTests(TestCase):
    def setUp(self):
        self.tournament = Tournament.objects.create(
            name="CricVision Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
            is_published=True,
        )

    def test_player_can_register_for_a_tournament(self):
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
            }
        )

        self.assertTrue(form.is_valid(), form.errors)

        registration = form.save()

        User = get_user_model()
        user = User.objects.get(username="rahul_kumar")

        self.assertEqual(
            user.profile.role,
            UserProfile.Role.PLAYER,
        )

        self.assertEqual(
            user.player_profile.full_name,
            "Rahul Kumar",
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