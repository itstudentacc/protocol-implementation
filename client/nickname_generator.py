import random
import hashlib

# Define components for nicknames
adjectives = ["Skibidi", "Ohio", "HawkTuah", "Sigma", "Fortnite", "NPC", "Rizzy", "Mogging", "Gooning", "Mewing", "TikTok", "Yapping"]
nouns = ["Maxxer", "Gooner", "Mewer", "Grandma", "Master", "Sigma", "Gyatt", "KaiCenat", "Ishowspeed", "Jonkler", "Mogger", "LivyDunne", "Wolf", "Skibidi", "Dawg", "MrBeast", "Respekt"]

def generate_nickname(fingerprint):
    # Hash the fingerprint to create a unique seed
    hash_object = hashlib.sha256(fingerprint.encode())
    hash_int = int(hash_object.hexdigest(), 16)
    
    # Seed the random number generator
    random.seed(hash_int)
    
    # Randomly select one from each list
    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    
    # Combine them in the desired format
    return f"{adj}_{noun}"




