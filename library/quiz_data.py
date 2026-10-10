"""
Play-style quiz: a short diagnostic that scores the user toward one of the
same shot-type categories shot_types.py buckets real shots into (pullup,
catch_shoot, rim, post). The result then drives two recommendations:
  - an Action.Category to go study in the action library
  - the real players in the dataset whose actual shot mix leans hardest
    into that category (computed live from Shot data, not hardcoded)

Deliberately only 4 of the 5 shot_types.py categories are quiz targets --
"other" is a catch-all bucket for untagged shots, not a playstyle anyone
would pick, so it's never a question option or a possible result.
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
]

PLAYSTYLE_RESULTS = {
    "catch_shoot": {
        "label": "Catch-and-Shoot Shooter",
        "description": "You play off the ball and punish a second of hesitation. Movement shooting and spacing are your game.",
        "action_category": "OFF",
    },
    "pullup": {
        "label": "Shot Creator",
        "description": "You need the ball in your hands. Pull-up jumpers and self-created looks off the dribble are your bread and butter.",
        "action_category": "ISO",
    },
    "rim": {
        "label": "Rim Pressure",
        "description": "You get downhill and finish through contact. Pick-and-roll dives and transition are where you live.",
        "action_category": "PNR",
    },
    "post": {
        "label": "Post Scorer",
        "description": "You work with your back to the basket. Footwork, touch, and a back-down game are your calling card.",
        "action_category": "POST",
    },
}


def score_quiz(answers):
    """
    answers: dict of {question_id: option_id}, e.g. {"q1": "b", "q2": "a", ...}
    Returns the winning category key (one of PLAYSTYLE_RESULTS' keys).
    Ties break in question order -- the first category to reach the max
    score wins, so earlier questions act as a soft tiebreaker.
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

    return max(scores, key=lambda k: scores[k])
