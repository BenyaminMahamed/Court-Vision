"""
Play-style quiz: an 8-question diagnostic that scores the user across the
same shot-type categories shot_types.py buckets real shots into (pullup,
catch_shoot, rim, post). The result combines the user's PRIMARY and
SECONDARY tendency into one of 12 named archetypes -- richer than just
picking the single winning category -- while still tying back to real,
measurable shot data for the player recommendations (which rank by the
primary category alone, since that is what the Shot table can answer).

"other" (shot_types.py's untagged catch-all) is never a quiz target --
it is not a playstyle anyone would pick.
"""

QUIZ_QUESTIONS = [
    {
        "id": "q1",
        "prompt": "A defender closes out on you hard at the three-point line. You...",
        "options": [
            {"id": "a", "label": "Shoot it before they arrive", "category": "catch_shoot"},
            {"id": "b", "label": "Take one hard dribble into a pull-up", "category": "pullup"},
            {"id": "c", "label": "Attack the closeout and get downhill to the rim", "category": "rim"},
            {"id": "d", "label": "Shot-fake and go to work on the block", "category": "post"},
        ],
    },
    {
        "id": "q2",
        "prompt": "In a pick-and-roll, your favorite outcome is...",
        "options": [
            {"id": "a", "label": "Popping for a clean catch-and-shoot look", "category": "catch_shoot"},
            {"id": "b", "label": "Coming off the screen into a pull-up", "category": "pullup"},
            {"id": "c", "label": "Diving hard to the rim for the lob or dump-off", "category": "rim"},
            {"id": "d", "label": "Not a fan of PNR -- give me a post touch instead", "category": "post"},
        ],
    },
    {
        "id": "q3",
        "prompt": "Pick the pro move you would most want in your bag:",
        "options": [
            {"id": "a", "label": "Steph's movement shooting and gravity", "category": "catch_shoot"},
            {"id": "b", "label": "Kyrie's step-back", "category": "pullup"},
            {"id": "c", "label": "Giannis's downhill finishing", "category": "rim"},
            {"id": "d", "label": "Jokic's post footwork and touch", "category": "post"},
        ],
    },
    {
        "id": "q4",
        "prompt": "Your ideal shot diet leans toward...",
        "options": [
            {"id": "a", "label": "Standstill threes off a kick-out", "category": "catch_shoot"},
            {"id": "b", "label": "Shifty, self-created mid-range jumpers", "category": "pullup"},
            {"id": "c", "label": "Finishing above the rim in traffic", "category": "rim"},
            {"id": "d", "label": "Playing with your back to the basket", "category": "post"},
        ],
    },
    {
        "id": "q5",
        "prompt": "You get the ball in isolation with 8 seconds left. First instinct:",
        "options": [
            {"id": "a", "label": "Swing it -- you are a play-finisher, not a shot-creator", "category": "catch_shoot"},
            {"id": "b", "label": "Create your own look off the dribble", "category": "pullup"},
            {"id": "c", "label": "Drive to the basket, no matter who is in the way", "category": "rim"},
            {"id": "d", "label": "Back your man down", "category": "post"},
        ],
    },
    {
        "id": "q6",
        "prompt": "Late game, your team needs a bucket. You want the ball because...",
        "options": [
            {"id": "a", "label": "You will get a clean look off movement", "category": "catch_shoot"},
            {"id": "b", "label": "You can create your own shot under pressure", "category": "pullup"},
            {"id": "c", "label": "You will just bully your way to the rim", "category": "rim"},
            {"id": "d", "label": "You will go to work on the smaller defender in the post", "category": "post"},
        ],
    },
    {
        "id": "q7",
        "prompt": "Which skill do you spend the most time working on?",
        "options": [
            {"id": "a", "label": "Off-ball movement and relocating for threes", "category": "catch_shoot"},
            {"id": "b", "label": "Ball-handling and shot creation", "category": "pullup"},
            {"id": "c", "label": "Finishing through contact at the rim", "category": "rim"},
            {"id": "d", "label": "Post footwork and back-to-the-basket moves", "category": "post"},
        ],
    },
    {
        "id": "q8",
        "prompt": "Pick a stat line you would be proudest of:",
        "options": [
            {"id": "a", "label": "48% from three on high volume", "category": "catch_shoot"},
            {"id": "b", "label": "25 points a game on tough, contested shots", "category": "pullup"},
            {"id": "c", "label": "70% at the rim with and-ones", "category": "rim"},
            {"id": "d", "label": "Efficient post-up scoring against bigger defenders", "category": "post"},
        ],
    },
]

# Keyed by (primary category, secondary category). The player-recommendation
# query (in views.py) only ever uses the primary key -- the secondary just
# picks which flavor of that primary archetype to show.
ARCHETYPES = {
    ("catch_shoot", "pullup"): {
        "label": "Movement Shooter",
        "description": "You shoot off movement and relocation, but can still create your own look when the catch-and-shoot chance isn't there.",
        "action_category": "OFF",
    },
    ("catch_shoot", "rim"): {
        "label": "3-and-D Wing",
        "description": "You live beyond the arc and attack closeouts when defenders run you off the line -- low usage, high value.",
        "action_category": "OFF",
    },
    ("catch_shoot", "post"): {
        "label": "Stretch Big",
        "description": "You space the floor from distance but can still punish a smaller closeout by backing them down.",
        "action_category": "OFF",
    },
    ("pullup", "catch_shoot"): {
        "label": "Shot Creator",
        "description": "You need the ball in your hands to create, but you are just as comfortable spotting up when someone else is cooking.",
        "action_category": "ISO",
    },
    ("pullup", "rim"): {
        "label": "Shifty Scorer",
        "description": "You create your own shot off the dribble and are not afraid to put it on the deck all the way to the rim.",
        "action_category": "ISO",
    },
    ("pullup", "post"): {
        "label": "Isolation Scorer",
        "description": "One-on-one is where you live -- pull-up jumpers and physical post touches against smaller defenders.",
        "action_category": "ISO",
    },
    ("rim", "catch_shoot"): {
        "label": "Slasher",
        "description": "You get downhill relentlessly but can also knock down an open catch-and-shoot look.",
        "action_category": "PNR",
    },
    ("rim", "pullup"): {
        "label": "Downhill Creator",
        "description": "You get to the rim first, but you can also pull up when the paint is clogged.",
        "action_category": "PNR",
    },
    ("rim", "post"): {
        "label": "Interior Finisher",
        "description": "You live around the rim -- lobs, dump-offs, and physical finishes, with a post game to fall back on.",
        "action_category": "PNR",
    },
    ("post", "catch_shoot"): {
        "label": "Face-Up Big",
        "description": "You work with your back to the basket but can also step out and knock down an open jumper.",
        "action_category": "POST",
    },
    ("post", "pullup"): {
        "label": "Face-Up Scorer",
        "description": "You use your size in the post but can also face up and create your own shot.",
        "action_category": "POST",
    },
    ("post", "rim"): {
        "label": "Back-to-Basket Bruiser",
        "description": "You bully smaller defenders inside and finish through contact when you get deep position.",
        "action_category": "POST",
    },
}


def score_breakdown(answers):
    """
    answers: dict of {question_id: option_id}, e.g. {"q1": "b", "q2": "a", ...}
    Returns the full {category: count} breakdown across all answered questions.
    """
    scores = {"catch_shoot": 0, "pullup": 0, "rim": 0, "post": 0}

    questions_by_id = {q["id"]: q for q in QUIZ_QUESTIONS}
    for qid, option_id in answers.items():
        question = questions_by_id.get(qid)
        if not question:
            continue
        option = next((o for o in question["options"] if o["id"] == option_id), None)
        if option:
            scores[option["category"]] += 1

    return scores


def quiz_result(answers):
    """
    Returns the full quiz result:
        {
            "primary": <category key -- the one used for player recommendations>,
            "secondary": <category key>,
            "label": <archetype label>,
            "description": <archetype description>,
            "action_category": <Action.Category code>,
            "scores": <full {category: count} breakdown, for the results bar chart>,
        }
    Ties break by category order in the scores dict -- a soft, stable
    tiebreaker rather than anything random.
    """
    scores = score_breakdown(answers)
    ordered = sorted(scores, key=lambda k: -scores[k])
    primary, secondary = ordered[0], ordered[1]
    archetype = ARCHETYPES[(primary, secondary)]

    return {
        "primary": primary,
        "secondary": secondary,
        "label": archetype["label"],
        "description": archetype["description"],
        "action_category": archetype["action_category"],
        "scores": scores,
    }
