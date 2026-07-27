from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import InningsSetupForm, NewBowlerForm, WicketForm
from .models import Delivery, Innings


def get_innings(innings_id):
    return get_object_or_404(
        Innings.objects.select_related(
            "match",
            "batting_team",
            "bowling_team",
            "current_striker",
            "current_non_striker",
            "current_bowler",
        ),
        pk=innings_id,
    )


def next_sequence(innings):
    last_delivery = innings.deliveries.order_by("-sequence").first()

    if last_delivery is None:
        return 1

    return last_delivery.sequence + 1


def swap_strike(innings):
    innings.current_striker, innings.current_non_striker = (
        innings.current_non_striker,
        innings.current_striker,
    )


def end_over_if_needed(innings):
    if innings.legal_balls > 0 and innings.legal_balls % 6 == 0:
        swap_strike(innings)
        innings.needs_new_bowler = True


@staff_member_required
def scorer_home(request):
    innings_list = Innings.objects.filter(
        is_completed=False
    ).select_related(
        "match",
        "batting_team",
        "bowling_team",
    ).order_by("match_id", "number")

    return render(
        request,
        "scoring/scorer_home.html",
        {"innings_list": innings_list},
    )


@staff_member_required
def innings_setup(request, innings_id):
    innings = get_innings(innings_id)

    if innings.current_striker_id:
        return redirect("scoring:live_scorer", innings_id=innings.id)

    if request.method == "POST":
        form = InningsSetupForm(request.POST, innings=innings)

        if form.is_valid():
            innings.opening_striker = form.cleaned_data["striker"]
            innings.opening_non_striker = form.cleaned_data["non_striker"]
            innings.current_striker = form.cleaned_data["striker"]
            innings.current_non_striker = form.cleaned_data["non_striker"]
            innings.current_bowler = form.cleaned_data["bowler"]
            innings.save()

            return redirect("scoring:live_scorer", innings_id=innings.id)
    else:
        form = InningsSetupForm(innings=innings)

    return render(
        request,
        "scoring/innings_setup.html",
        {
            "innings": innings,
            "form": form,
        },
    )


@staff_member_required
def live_scorer(request, innings_id):
    innings = get_innings(innings_id)

    if not innings.current_striker_id and not innings.is_completed:
        return redirect("scoring:innings_setup", innings_id=innings.id)

    over_limit_reached = (
        innings.legal_balls >= innings.match.over_per_innings * 6
    )

    return render(
        request,
        "scoring/live_scorer.html",
        {
            "innings": innings,
            "new_bowler_form": NewBowlerForm(innings=innings),
            "wicket_form": WicketForm(innings=innings),
            "recent_deliveries": innings.deliveries.order_by(
                "-sequence"
            )[:12],
            "over_limit_reached": over_limit_reached,
        },
    )


@staff_member_required
@require_POST
def record_runs(request, innings_id):
    innings = get_innings(innings_id)

    if innings.is_completed or innings.needs_new_bowler:
        return redirect("scoring:live_scorer", innings_id=innings.id)

    event = request.POST.get("event")

    normal_runs = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "6": 6,
    }

    if event not in list(normal_runs) + ["wide", "no_ball"]:
        messages.error(request, "Invalid scoring action.")
        return redirect("scoring:live_scorer", innings_id=innings.id)

    with transaction.atomic():
        if event in normal_runs:
            runs = normal_runs[event]

            delivery = Delivery(
                inning=innings,
                sequence=next_sequence(innings),
                striker=innings.current_striker,
                non_striker=innings.current_non_striker,
                bowler=innings.current_bowler,
                runs_off_bat=runs,
                extras=0,
                extra_type="NONE",
                is_legal_delivery=True,
            )

            delivery.full_clean()
            delivery.save()

            if runs % 2 == 1:
                swap_strike(innings)

            end_over_if_needed(innings)

        elif event == "wide":
            delivery = Delivery(
                inning=innings,
                sequence=next_sequence(innings),
                striker=innings.current_striker,
                non_striker=innings.current_non_striker,
                bowler=innings.current_bowler,
                runs_off_bat=0,
                extras=1,
                extra_type="WIDE",
                is_legal_delivery=False,
            )

            delivery.full_clean()
            delivery.save()

        elif event == "no_ball":
            delivery = Delivery(
                inning=innings,
                sequence=next_sequence(innings),
                striker=innings.current_striker,
                non_striker=innings.current_non_striker,
                bowler=innings.current_bowler,
                runs_off_bat=0,
                extras=1,
                extra_type="NO_BALL",
                is_legal_delivery=False,
            )

            delivery.full_clean()
            delivery.save()

        innings.save()

    return redirect("scoring:live_scorer", innings_id=innings.id)


@staff_member_required
@require_POST
def record_wicket(request, innings_id):
    innings = get_innings(innings_id)

    if innings.is_completed or innings.needs_new_bowler:
        return redirect("scoring:live_scorer", innings_id=innings.id)

    form = WicketForm(request.POST, innings=innings)

    if not form.is_valid():
        messages.error(request, "Please select valid wicket information.")
        return redirect("scoring:live_scorer", innings_id=innings.id)

    dismissed_player = form.cleaned_data["dismissed_player"]
    next_batter = form.cleaned_data["next_batter"]

    with transaction.atomic():
        delivery = Delivery(
            inning=innings,
            sequence=next_sequence(innings),
            striker=innings.current_striker,
            non_striker=innings.current_non_striker,
            bowler=innings.current_bowler,
            runs_off_bat=0,
            extras=0,
            extra_type="NONE",
            is_legal_delivery=True,
            is_wicket=True,
            wicket_player=dismissed_player,
            dismissal_kind="Wicket",
        )

        delivery.full_clean()
        delivery.save()

        if dismissed_player == innings.current_striker:
            innings.current_striker = next_batter
        else:
            innings.current_non_striker = next_batter

        if next_batter is None:
            innings.is_completed = True
        else:
            end_over_if_needed(innings)

        innings.save()

    return redirect("scoring:live_scorer", innings_id=innings.id)


@staff_member_required
@require_POST
def select_new_bowler(request, innings_id):
    innings = get_innings(innings_id)

    form = NewBowlerForm(request.POST, innings=innings)

    if form.is_valid():
        innings.current_bowler = form.cleaned_data["bowler"]
        innings.needs_new_bowler = False
        innings.save()
    else:
        messages.error(request, "Select a valid bowler.")

    return redirect("scoring:live_scorer", innings_id=innings.id)


def update_match_result(match):
    try:
        first_innings = match.innings.get(number=1)
        second_innings = match.innings.get(number=2)
    except Innings.DoesNotExist:
        return

    if not first_innings.is_completed or not second_innings.is_completed:
        return

    first_score = first_innings.total_runs
    second_score = second_innings.total_runs

    match.status = "COMPLETED"

    if second_score > first_score:
        max_wickets = second_innings.batting_team.players.count() - 1
        wicket_remaining = max(max_wickets - second_innings.wickets, 0)

        match.winner = second_innings.batting_team
        match.result_summery = (f"{second_innings.batting_team.name} won by "
                                f"{wicket_remaining} wickets"
                                )


    elif first_score > second_score:
        run_margin = first_score - second_score

        match.winner = first_innings.batting_team
        match.result_summery = (
            f"{first_innings.batting_team.name} won by"
            f"{run_margin} runs"
        )

    else:
        match.winner = None
        match.result_summery = "Match tied"

    match.save(
        update_fields=[
            "status",
            "winner",
            "result_summery",
        ]
    )
                    


@staff_member_required
@require_POST
def finish_innings(request, innings_id):
    innings = get_innings(innings_id)

    innings.is_completed = True
    innings.save(update_fields = ["is_completed"])

    if innings.number == 1:
        second_innings = innings.match.innings.filter(
            number = 2
        ).first()
        
        if second_innings:
            second_innings.target_runs = innings.total_runs + 1
            second_innings.save(update_fields = ["target_runs"])

        elif innings.number == 2:
            update_match_result(innings.match)

    messages.success(request, "Innings marked as completed.")

    return redirect("scoring:scorer_home")