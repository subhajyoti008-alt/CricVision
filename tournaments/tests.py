import tempfile
from datetime import date
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from PIL import Image

from accounts.models import UserProfile

from .forms import PlayerTournamentRegistrationForm
from .models import Auction, Tournament, Registration
from .models import Payment
from .services import (submit_player_payment, approve_registration, return_registration_to_pending,)
from players.models import Player
from decimal import Decimal
from teams.models import Team




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


class RegistrationApprovalServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.tournament = Tournament.objects.create(
            name="Approval Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 10),
            end_date=date(2026, 12, 12),
            entry_fee=100,
            is_published=True,
        )

        self.organizer = User.objects.create_user(
            username="organizer_user",
            password="StrongPassword123!",
            is_staff=True,
        )

        player_user = User.objects.create_user(
            username="approval_player",
            password="StrongPassword123!",
        )

        self.player = Player.objects.create(
            user=player_user,
            full_name="Approval Player",
        )

        self.registration = Registration.objects.create(
            player=self.player,
            tournament=self.tournament,
        )

    def test_paid_registration_can_be_approved(self):
        self.registration.payment_status = "PAID"
        self.registration.save(
            update_fields=["payment_status"],
        )

        approve_registration(
            registration=self.registration,
            organizer=self.organizer,
        )

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.status,
            "APPROVED",
        )

    def test_unpaid_registration_cannot_be_approved(self):
        with self.assertRaises(ValidationError):
            approve_registration(
                registration=self.registration,
                organizer=self.organizer,
            )

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.status,
            "PENDING",
        )

    def test_approved_registration_can_return_to_pending(self):
        self.registration.payment_status = "PAID"
        self.registration.save(
            update_fields=["payment_status"],
        )

        approve_registration(
            registration=self.registration,
            organizer=self.organizer,
        )

        return_registration_to_pending(
            registration=self.registration,
            organizer=self.organizer,
        )

        self.registration.refresh_from_db()

        self.assertEqual(
            self.registration.status,
            "PENDING",
        )


class AuctionEligibilityTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.tournament = Tournament.objects.create(
            name="Auction Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 15),
            end_date=date(2026, 12, 17),
            entry_fee=100,
            is_published=True,
        )

        player_user = User.objects.create_user(
            username="auction_player",
            password="StrongPassword123!",
        )

        self.player = Player.objects.create(
            user=player_user,
            full_name="Auction Player",
        )

        self.registration = Registration.objects.create(
            player=self.player,
            tournament=self.tournament,
        )

    def test_paid_approved_player_can_enter_auction(self):
        self.registration.status = "APPROVED"
        self.registration.payment_status = "PAID"
        self.registration.save(
            update_fields=[
                "status",
                "payment_status",
            ],
        )

        auction = Auction.objects.create(
            registration=self.registration,
            base_price=Decimal("500.00"),
        )

        self.assertEqual(
            auction.status,
            "AVAILABLE",
        )

        self.assertEqual(
            auction.current_bid,
            Decimal("500.00"),
        )

    def test_unpaid_player_cannot_enter_auction(self):
        self.registration.status = "APPROVED"
        self.registration.save(
            update_fields=["status"],
        )

        with self.assertRaises(ValidationError):
            Auction.objects.create(
                registration=self.registration,
                base_price=Decimal("500.00"),
            )


class AuctionSaleTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.tournament = Tournament.objects.create(
            name="Sale Test Cup",
            city="Kolkata",
            start_date=date(2026, 12, 20),
            end_date=date(2026, 12, 22),
            entry_fee=100,
            is_published=True,
        )

        self.team = Team.objects.create(
            name="CricVision Warriors",
            short_name="CVW",
        )

        self.tournament.teams.add(self.team)

        player_user = User.objects.create_user(
            username="sale_player",
            password="StrongPassword123!",
        )

        self.player = Player.objects.create(
            user=player_user,
            full_name="Sale Player",
        )

        self.registration = Registration.objects.create(
            player=self.player,
            tournament=self.tournament,
            status="APPROVED",
            payment_status="PAID",
        )

        self.auction = Auction.objects.create(
            registration=self.registration,
            base_price=Decimal("500.00"),
        )

    def test_selling_auction_assigns_player_to_team(self):
        self.auction.mark_sold(
            team=self.team,
            price=Decimal("750.00"),
        )

        self.auction.refresh_from_db()

        self.assertEqual(
            self.auction.status,
            "SOLD",
        )

        self.assertEqual(
            self.auction.winning_team,
            self.team,
        )

        self.assertEqual(
            self.auction.final_price,
            Decimal("750.00"),
        )

        self.assertTrue(
            self.team.players.filter(
                pk=self.player.pk,
            ).exists()
        )

    def test_cannot_sell_player_to_team_from_another_tournament(self):
        outside_team = Team.objects.create(
            name="Outside Team",
            short_name="OUT",
        )

        with self.assertRaises(ValidationError):
            self.auction.mark_sold(
                team=outside_team,
                price=Decimal("750.00"),
            )

        self.auction.refresh_from_db()

        self.assertEqual(
            self.auction.status,
            "AVAILABLE",
        )

        self.assertFalse(
            outside_team.players.filter(
                pk=self.player.pk,
            ).exists()
        )