"""
Generates a mock 10,000-book catalog spread across 7 genres, and writes it
to books.json in a shape that app.py can load directly at startup:

    {
      "<isbn>": {
        "title": ..., "author": ..., "isbn": ..., "genre": ...,
        "tags": [...], "available_copies": ...
      },
      ...
    }
"""

import json
import random

random.seed(42)  # reproducible output

GENRES = ["christian", "politics", "history", "economics", "sorcery", "science", "sports"]

TARGET_TOTAL = 10_000

# --- Word banks per genre, used to assemble varied, plausible-sounding titles ---

TITLE_PARTS = {
    "christian": {
        "adjectives": ["Sacred", "Eternal", "Living", "Redeeming", "Hidden", "Steadfast",
                       "Unwavering", "Amazing", "Everlasting", "Radiant", "Humble", "Holy"],
        "nouns": ["Grace", "Faith", "Covenant", "Scripture", "Gospel", "Redemption",
                  "Prayer", "Discipleship", "Wisdom", "Mercy", "Salvation", "Spirit",
                  "Shepherd", "Kingdom", "Sabbath", "Psalms", "Communion", "Pilgrimage"],
        "templates": [
            "The {adj} {noun}", "{noun} of the {adj} Heart", "Walking in {noun}",
            "A {adj} Journey Through {noun}", "{noun} for Every Season",
            "The {noun} Within", "Voices of {noun}", "{adj} {noun}: A Devotional",
        ],
    },
    "politics": {
        "adjectives": ["Divided", "United", "Fragile", "Radical", "Silent", "Modern",
                       "Enduring", "Contested", "Global", "Broken", "Reform", "New"],
        "nouns": ["Democracy", "Power", "Republic", "Nation", "Diplomacy", "Election",
                  "Liberty", "Congress", "Sovereignty", "Rebellion", "Policy", "Empire",
                  "Constitution", "Dissent", "State", "Coalition", "Revolution"],
        "templates": [
            "The {adj} {noun}", "{noun} in Crisis", "A History of {adj} {noun}",
            "The Rise and Fall of {noun}", "Inside the {adj} {noun}",
            "{noun}: Who Really Decides", "Notes on {adj} {noun}",
        ],
    },
    "history": {
        "adjectives": ["Ancient", "Forgotten", "Lost", "Golden", "Dark", "Imperial",
                       "Medieval", "Colonial", "Silent", "Distant", "Early", "Vanished"],
        "nouns": ["Empire", "Dynasty", "Conquest", "Civilization", "Kingdom", "Frontier",
                  "Ruins", "Voyage", "Chronicle", "Legacy", "Siege", "Expedition",
                  "Uprising", "Archive", "Age", "Crossing"],
        "templates": [
            "The {adj} {noun}", "A {adj} History of {noun}", "{noun} of the {adj} Age",
            "Chronicles of the {adj} {noun}", "The Last {noun}",
            "{adj} {noun}: A Retelling", "Echoes of {noun}",
        ],
    },
    "economics": {
        "adjectives": ["Invisible", "Global", "Rational", "Behavioral", "Free", "Digital",
                       "Emerging", "Volatile", "Structural", "Marginal", "Informal"],
        "nouns": ["Markets", "Capital", "Trade", "Inflation", "Growth", "Currency",
                  "Supply", "Demand", "Wealth", "Labor", "Debt", "Innovation",
                  "Recession", "Equilibrium", "Incentives", "Exchange"],
        "templates": [
            "The {adj} {noun}", "Understanding {adj} {noun}", "{noun} and the {adj} Economy",
            "A Short History of {noun}", "{adj} {noun}: Principles and Practice",
            "The Logic of {noun}", "Rethinking {adj} {noun}",
        ],
    },
    "sorcery": {
        "adjectives": ["Forbidden", "Shadow", "Arcane", "Ember", "Moonlit", "Cursed",
                       "Silver", "Whispering", "Runed", "Feral", "Ashen", "Ancient"],
        "nouns": ["Grimoire", "Spellbook", "Coven", "Sorcerer", "Ritual", "Amulet",
                  "Familiar", "Enchantment", "Wardstone", "Hexcraft", "Conjurer",
                  "Talisman", "Incantation", "Sorcery", "Wyrding", "Sanctum"],
        "templates": [
            "The {adj} {noun}", "{noun} of the {adj} Realm", "A {adj} {noun}",
            "Tales of the {adj} {noun}", "{noun} and Shadow",
            "The Last {noun}", "{adj} {noun}: A Chronicle of Magic",
        ],
    },
    "science": {
        "adjectives": ["Quantum", "Cellular", "Cosmic", "Genetic", "Neural", "Elemental",
                       "Synthetic", "Orbital", "Molecular", "Evolutionary", "Subatomic"],
        "nouns": ["Physics", "Biology", "Genome", "Universe", "Particle", "Ecosystem",
                  "Algorithm", "Species", "Reaction", "Signal", "Circuit", "Theory",
                  "Galaxy", "Organism", "Field", "Matter"],
        "templates": [
            "The {adj} {noun}", "Understanding {adj} {noun}", "{noun}: A Field Guide",
            "The Hidden Life of {noun}", "{adj} {noun} Explained",
            "Frontiers of {adj} {noun}", "A Brief History of {noun}",
        ],
    },
    "sports": {
        "adjectives": ["Relentless", "Golden", "Underdog", "Unbeaten", "Final", "Champion",
                       "Legendary", "Home", "Away", "Record-Breaking", "Rookie"],
        "nouns": ["Season", "Match", "Playbook", "Rivalry", "Championship", "Draft",
                  "Sprint", "Marathon", "Coach", "Training", "Victory", "Comeback",
                  "League", "Tournament", "Arena", "Team"],
        "templates": [
            "The {adj} {noun}", "{noun} of a Lifetime", "Behind the {adj} {noun}",
            "{adj} {noun}: An Inside Story", "The Making of a {adj} {noun}",
            "Chasing the {adj} {noun}", "{noun}: Stories From the Field",
        ],
    },
}

GENRE_TAGS = {
    "christian": ["faith", "devotional", "scripture", "spirituality", "prayer", "theology"],
    "politics": ["government", "policy", "democracy", "current affairs", "power", "diplomacy"],
    "history": ["ancient", "war", "civilization", "biography", "empire", "archives"],
    "economics": ["markets", "finance", "trade", "policy", "growth", "money"],
    "sorcery": ["magic", "fantasy", "spells", "witchcraft", "mythical", "occult"],
    "science": ["research", "discovery", "technology", "biology", "physics", "space"],
    "sports": ["athletics", "competition", "teamwork", "training", "championship", "fitness"],
}

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Linda", "Michael", "Barbara",
    "David", "Elizabeth", "William", "Susan", "Richard", "Jessica", "Joseph", "Sarah",
    "Thomas", "Karen", "Charles", "Nancy", "Daniel", "Margaret", "Amara", "Chidi",
    "Kwame", "Fatima", "Olumide", "Ngozi", "Wei", "Mei", "Hiro", "Yuki", "Arjun",
    "Priya", "Diego", "Sofia", "Lucas", "Elena", "Anders", "Ingrid", "Klaus", "Greta",
]
LAST_NAMES = [
    "Adeyemi", "Okafor", "Nwosu", "Smith", "Johnson", "Williams", "Brown", "Davis",
    "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White",
    "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Lewis",
    "Walker", "Hall", "Allen", "Young", "King", "Wright", "Chen", "Kobayashi",
    "Nakamura", "Singh", "Kapoor", "Rossi", "Novak", "Larsen", "Hoffmann", "Dubois",
]


def make_title(genre: str) -> str:
    parts = TITLE_PARTS[genre]
    template = random.choice(parts["templates"])
    return template.format(
        adj=random.choice(parts["adjectives"]),
        noun=random.choice(parts["nouns"]),
    )


def make_author() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_isbn13(n: int) -> str:
    """Builds a structurally valid ISBN-13 (correct check digit) from a running counter."""
    prefix = "978"
    group = "0"
    body = f"{n:09d}"  # publisher+title block, 9 digits
    digits = [int(d) for d in (prefix + group + body)]
    checksum = sum(d if i % 2 == 0 else d * 3 for i, d in enumerate(digits))
    check_digit = (10 - (checksum % 10)) % 10
    raw = prefix + group + body + str(check_digit)
    return f"{raw[0:3]}-{raw[3]}-{raw[4:7]}-{raw[7:12]}-{raw[12]}"


def make_tags(genre: str) -> list[str]:
    pool = GENRE_TAGS[genre]
    k = random.randint(2, min(4, len(pool)))
    return random.sample(pool, k)


def generate_catalog(total: int) -> dict:
    per_genre = total // len(GENRES)
    remainder = total - per_genre * len(GENRES)

    counts = {g: per_genre for g in GENRES}
    for g in GENRES[:remainder]:
        counts[g] += 1

    catalog = {}
    counter = 1
    seen_titles = set()

    for genre in GENRES:
        made = 0
        while made < counts[genre]:
            title = make_title(genre)
            key = (genre, title)
            # allow repeated titles across different authors (real catalogs do this),
            # but avoid the exact same (genre, title) pair colliding too much
            if key in seen_titles and random.random() < 0.7:
                continue
            seen_titles.add(key)

            isbn = make_isbn13(counter)
            counter += 1

            catalog[isbn] = {
                "title": title,
                "author": make_author(),
                "isbn": isbn,
                "genre": genre,
                "tags": make_tags(genre),
                "available_copies": random.choices(
                    [0, 1, 2, 3, 4, 5], weights=[10, 20, 25, 20, 15, 10]
                )[0],
            }
            made += 1

    return catalog


if __name__ == "__main__":
    catalog = generate_catalog(TARGET_TOTAL)
    with open("books.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(catalog)} books -> books.json")
    from collections import Counter
    genre_counts = Counter(b["genre"] for b in catalog.values())
    for g, c in genre_counts.items():
        print(f"  {g}: {c}")
