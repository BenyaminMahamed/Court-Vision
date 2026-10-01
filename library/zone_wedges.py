import math

SPLIT_BASIC_ZONES = {
    "Restricted Area",
    "In The Paint (Non-RA)",
    "Close Range",
    "Mid-Range",
    "Above the Break 3",
    "Left Corner 3",
    "Right Corner 3",
}

def classify_zone_area(arg1, arg2, arg3=None, arg4=None):
    """
    Flexible classifier supporting both signatures:
    1. classify_zone_area(loc_x, loc_y, zone_basic)
    2. classify_zone_area(zone_basic, zone_range, loc_x, loc_y)
    """
    if isinstance(arg1, (int, float)) and isinstance(arg2, (int, float)):
        loc_x, loc_y = float(arg1), float(arg2)
        zone_basic = str(arg3) if arg3 else ""
        zone_range = ""
    else:
        zone_basic = str(arg1) if arg1 else ""
        zone_range = str(arg2) if arg2 else ""
        loc_x = float(arg3) if arg3 is not None else 0.0
        loc_y = float(arg4) if arg4 is not None else 0.0

    if zone_basic == "Restricted Area":
        return "Restricted Area"
    if zone_basic == "In The Paint (Non-RA)":
        return "In The Paint (Non-RA)"

    if zone_basic == "Left Corner 3":
        return "Left Corner 3"
    if zone_basic == "Right Corner 3":
        return "Right Corner 3"

    angle = math.degrees(math.atan2(loc_x, loc_y))

    # Close Range (Layer 2)
    if "Less Than 8 ft." in zone_range or (zone_range == "8-16 ft." and loc_y < 120) or zone_basic == "Close Range":
        if angle < -30:
            return "Close Range Left"
        elif angle <= 30:
            return "Close Range Center"
        else:
            return "Close Range Right"

    # Mid-Range (Layer 3)
    if zone_basic == "Mid-Range":
        if angle < -54:
            return "Mid-Range Left"
        elif angle < -18:
            return "Mid-Range Left-Center"
        elif angle <= 18:
            return "Mid-Range Center"
        elif angle <= 54:
            return "Mid-Range Right-Center"
        else:
            return "Mid-Range Right"

    # Above the Break 3 (Layer 4)
    if angle < -18:
        return "Above the Break 3 Left"
    elif angle <= 18:
        return "Above the Break 3 Center"
    else:
        return "Above the Break 3 Right"


def combined_zone_key(zone_basic, zone_area):
    if zone_area:
        return zone_area
    return zone_basic


def zone_display_label(zone_key):
    labels = {
        "Restricted Area": "Restricted Area",
        "In The Paint (Non-RA)": "In The Paint (Non-RA)",
        "Close Range Left": "Close Range Left",
        "Close Range Center": "Close Range Center",
        "Close Range Right": "Close Range Right",
        "Mid-Range Left": "Mid-Range Left",
        "Mid-Range Left-Center": "Mid-Range Left-Center",
        "Mid-Range Center": "Mid-Range Center",
        "Mid-Range Right-Center": "Mid-Range Right-Center",
        "Mid-Range Right": "Mid-Range Right",
        "Left Corner 3": "Left Corner 3",
        "Above the Break 3 Left": "Above the Break 3 Left",
        "Above the Break 3 Center": "Above the Break 3 Center",
        "Above the Break 3 Right": "Above the Break 3 Right",
        "Right Corner 3": "Right Corner 3",
    }
    return labels.get(zone_key, zone_key)
