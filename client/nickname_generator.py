import random

adjectives = ["Skibidi", "Ohio", "HawkTuah", "Sigma", "Fortnite", "Npc", "Rizzy", "Mogging", "Gooning", "Mewing", "TikTok", "Yapping"]
nouns = ["Maxxer", "Gooner", "Mewer", "Grandma", "Master", "Sigma", "Gyatt", "Cenat", "Ishowspeed", "Jonkler", "Mogger", "LivyDunne", "Wolf", "Skibidi", "Dawg", "MrBeast", "Ninja"]

def generate_nickname():
    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    
    formats = [
        f"{adj}_{noun}",
        f"{adj}{noun}",
        f"{adj}_of_{noun}",
        f"The{adj}{noun}",
    ]
    
    return random.choice(formats)


