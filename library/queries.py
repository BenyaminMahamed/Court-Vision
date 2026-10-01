import math
from django.db.models import Count, Q, F
from .models import Shot, LeagueZoneAverages
from .zone_wedges import zone_display_label

def get_player_shot_data(player_id, season="2023-24", shot_type=None):
    """
    Aggregates shot data for a player across all 14 zones and compares 
    them to league baseline averages.
    """
    shots = Shot.objects.filter(player_id=player_id, season=season)
    
    if shot_type and shot_type != "all":
        # Handle shot type filters
        type_map = {
            "catch_shoot": "Catch and Shoot",
            "pullup": "Pullups",
            "paint_touch": "Paint Touches",
            "post_up": "Post Ups"
        }
        filter_val = type_map.get(shot_type, shot_type)
        shots = shots.filter(shot_type__icontains=filter_val)

    # Fetch League Averages for 2023-24
    league_avg_qs = LeagueZoneAverages.objects.filter(season=season)
    league_dict = {la.zone_area: la.fg_pct for la in league_avg_qs if la.zone_area}

    # Aggregate shots grouped by zone_area
    zone_counts = (
        shots.values("zone_area")
        .annotate(
            fga=Count("id"),
            fgm=Count("id", filter=Q(shot_made=True))
        )
    )

    zones_data = {}
    total_fga = 0
    total_fgm = 0

    for item in zone_counts:
        area = item["zone_area"]
        if not area:
            continue

        fga = item["fga"]
        fgm = item["fgm"]
        pct = round((fgm / fga) * 100, 1) if fga > 0 else 0.0

        total_fga += fga
        total_fgm += fgm

        lg_pct = league_dict.get(area, 0.450)
        if lg_pct < 1.0:
            lg_pct = lg_pct * 100.0  # Normalize percentage scale

        diff = round(pct - lg_pct, 1)

        zones_data[area] = {
            "fgm": fgm,
            "fga": fga,
            "pct": pct,
            "lg_pct": round(lg_pct, 1),
            "diff": diff,
            "label": zone_display_label(area)
        }

    overall_pct = round((total_fgm / total_fga) * 100, 1) if total_fga > 0 else 0.0

    return {
        "zones": zones_data,
        "total_fga": total_fga,
        "total_fgm": total_fgm,
        "overall_pct": overall_pct,
        "shots_raw": list(shots.values("loc_x", "loc_y", "shot_made", "zone_area"))
    }
