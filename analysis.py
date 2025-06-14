import json
import os
import re
from rapidfuzz import fuzz, process

# List of common color-related words to remove from guitar titles
COLOR_TERMS = {
    "red", "black", "blue", "white", "green", "yellow", "purple", "orange", "brown", "pink", "silver", "gold",
    "charcoal", "wine", "burst", "natural", "sunburst", "metallic", "maple", "pearl", "translucent", "vintage"
}

# List of common terms to remove from guitar titles (keeping model, series, custom, etc.)
COMMON_TERMS = {
    "guitar", "instrument", "electric guitar", "acoustic guitar", "bass guitar"
}

# Important model/series terms to focus on for matching
MODEL_SERIES = [
    "american professional", "american vintage", "vintera", "american standard", "american ultra", "american performer",
    "player", "mim", "75th anniversary", "commemorative", "custom shop", "artist series", "les paul studio",
    "les paul standard", "les paul tribute", "sg standard", "sg special", "flying v", "explorer", "custom shop",
    "slash", "inspired by gibson", "se", "mark holcomb", "s2", "mccarty", "private stock", "hellraiser", 
    "sun valley super shredder", "reaper", "blackjack", "c-1", "pro series", "sl2", "soloist", "rhoads", 
    "dinky", "evh", "wolfgang", "rg", "s", "prestige", "jem"
]

def load_json_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def remove_color_terms(title):
    """Remove color-related terms from guitar title."""
    words = title.split()
    filtered_words = [word for word in words if word.lower() not in COLOR_TERMS]
    return " ".join(filtered_words)

def remove_common_terms(title, brand=None):
    """Remove common and irrelevant terms from the guitar title, like 'electric guitar' and brand names."""
    words = title.split()

    # Remove common terms like "electric guitar", "acoustic guitar"
    filtered_words = [word for word in words if word.lower() not in COMMON_TERMS]
    
    # Remove the brand name if it's present in the title
    if brand:
        filtered_words = [word for word in filtered_words if word.lower() != brand.lower()]
    
    return " ".join(filtered_words)

def normalize_title(title, brand=None):
    """Normalize title by removing special characters, common terms, color terms, and brand names."""
    if not isinstance(title, str):
        title = str(title) if title is not None else ""
    
    # Remove common terms and brand name from the title
    title = remove_common_terms(title, brand)
    
    # Remove color terms completely
    title = remove_color_terms(title)
    
    # Lowercase and remove non-alphanumeric characters (except spaces)
    return re.sub(r'[^a-z0-9 ]', '', title.lower())

def calculate_match_score(used_title, new_title, used_price, new_price, brand, threshold=80):
    """
    Calculate match score considering model/series match, fuzzy title match, and price difference.
    This version applies a dynamic penalty based on the price difference percentage.
    """
    # Normalize the titles by removing color terms, common terms, and brand names
    used_title_norm = normalize_title(used_title, brand)
    new_title_norm = normalize_title(new_title, brand)
    
    # Fuzzy title matching score using token_set_ratio
    fuzzy_score = fuzz.token_set_ratio(used_title_norm, new_title_norm)

    # Core Model/Series Terms - the important parts of the title that should match more heavily
    model_series_terms = [
        "american professional", "american vintage", "vintera", "american standard", "american ultra", "american performer",
        "player", "mim", "75th anniversary", "commemorative", "custom shop", "artist series", "les paul studio",
        "les paul standard", "les paul tribute", "sg standard", "sg special", "flying v", "explorer", "custom shop",
        "slash", "inspired by gibson", "se", "mark holcomb", "s2", "mccarty", "private stock", "hellraiser", 
        "sun valley super shredder", "reaper", "blackjack", "c-1", "pro series", "sl2", "soloist", "rhoads", 
        "dinky", "evh", "wolfgang", "rg", "s", "prestige", "jem"
    ]

    # Add a bonus for core model/series match
    model_bonus = 0
    for term in model_series_terms:
        if term in used_title.lower() and term in new_title.lower():
            model_bonus += 5
        elif term in used_title.lower() or term in new_title.lower():
            model_bonus -= 5

    # Calculate price difference percentage for scoring
    price_diff_percent = (new_price - used_price) / new_price * 100

    # Initialize price score to 0
    price_score = 0

    # Apply dynamic penalty based on price difference percentage
    if price_diff_percent > 80:
        price_score = price_diff_percent * 0.6
    elif price_diff_percent > 70:
        price_score = price_diff_percent * 0.45
    elif price_diff_percent > 60:
        price_score = price_diff_percent * 0.3
    elif price_diff_percent > 50:
        price_score = price_diff_percent * 0.15
    elif price_diff_percent > 40:
        price_score = price_diff_percent * 0.08
    elif price_diff_percent > 30:
        price_score = price_diff_percent * 0.04
    elif price_diff_percent > 20:
        price_score = price_diff_percent * 0.02
    elif price_diff_percent > 10:
        price_score = price_diff_percent * 0.01

    # Apply penalty for fuzzy score when used title is too short
    if len(used_title.split()) <= 2:  # If the used title is short (e.g., "Stratocaster")
        fuzzy_score -= 10  # Apply a penalty to the fuzzy score

    # Apply a weight to the model bonus if the match is with a shorter title
    if len(used_title.split()) <= 2:
        model_bonus *= 1.5  # Increase importance of the model match for short titles
    
    final_score = fuzzy_score + model_bonus - price_score

    # Final match score should not exceed 100
    final_score = min(final_score, 100)  

    return final_score

def find_best_match(used_guitar, new_guitars_by_brand, threshold=80):
    """
    Find the best fuzzy title match among new guitars of the same brand.
    Return matched new guitar dict and score if above threshold, else None.
    """
    brand = used_guitar.get('brand')
    if not brand or brand not in new_guitars_by_brand:
        return None, 0
    
    used_title_norm = normalize_title(used_guitar.get('title', ''), brand)
    choices = [(g['title'], g) for g in new_guitars_by_brand[brand]]

    # Apply fuzzy matching to find the best match
    best_match = process.extractOne(used_title_norm, [normalize_title(c[0], brand) for c in choices], scorer=fuzz.token_set_ratio)
    
    if best_match and best_match[1] >= threshold:
        # Find matched guitar dict
        idx = best_match[2]
        matched_guitar = choices[idx][1]

        # Calculate match score using the function you provided
        used_price = used_guitar.get('price') or 0
        new_price = matched_guitar.get('price') or 0

        score = calculate_match_score(
            used_title=used_guitar.get('title'),
            new_title=matched_guitar.get('title'),
            used_price=used_price,
            new_price=new_price,
            brand=used_guitar.get('brand')
        )

        return matched_guitar, score

    return None, 0

def generate_used_url(used, base_url="https://www.sweetwater.com"):
    """Generate the correct used guitar URL based on the store and guitar title."""
    store = used.get('store', 'Guitar Center')
    used_url = used.get('slug')
    
    if store == "Sweetwater" and used_url:
        if not used_url.startswith("/used/listings/"):
            used_url = "/used/listings/" + used_url
        used_url = f"https://www.sweetwater.com{used_url}"
    
    elif store == "Guitar Center" and used_url:
        if not used_url.startswith("http"):
            used_url = "https://www.guitarcenter.com" + used_url
    
    return used_url

if __name__ == "__main__":
    try:
        used_guitars = load_json_file('./data/combined/used_guitars_combined.json')
        new_guitars = load_json_file('./data/combined/new_guitars_combined.json')

        # Index new guitars by brand for faster lookup
        new_guitars_by_brand = {}
        for g in new_guitars:
            brand = g.get('brand')
            if brand:
                new_guitars_by_brand.setdefault(brand, []).append(g)

        BASE_URLS = {
            "Guitar Center": "https://www.guitarcenter.com",
            "Sweetwater": "https://www.sweetwater.com/used/listings"
        }

        matches = []
        for used in used_guitars:
            new_match, score = find_best_match(used, new_guitars_by_brand)
            if new_match:
                used_price = used.get('price') or 0
                new_price = new_match.get('price') or 0
                
                used_shipping = used.get('shipping_price', 0)
                if used.get('store') == "Sweetwater":
                    if used_shipping == 0:
                        used_shipping = 0
                    else:
                        used_shipping = used_shipping
                else:
                    used_shipping = used_shipping or 30  # Default to $30 shipping fee if not set

                used_total_price = used_price + used_shipping
                discount = new_price - used_total_price
                
                if discount > 0:
                    store = used.get('store', 'Guitar Center')
                    base_url = BASE_URLS.get(store, BASE_URLS["Guitar Center"])
                    used_url = generate_used_url(used, base_url)
                    
                    matches.append({
                        'used_title': used.get('title'),
                        'used_price': used_price,
                        'used_condition': used.get('condition'),
                        'used_store': used.get('store'),
                        'new_title': new_match.get('title'),
                        'new_price': new_price,
                        'new_store': new_match.get('store'),
                        'price_difference': discount,
                        'match_score': score,
                        'new_url': new_match.get('url'),
                        'used_url': used_url,
                        'used_shipping': used_shipping
                    })

        # Continue sorting and filtering...
        top_matches = sorted(matches, key=lambda x: x['match_score'], reverse=True)
        top_matches = [match for match in top_matches if 500 < match['used_price'] < 900]
        top_matches = [match for match in top_matches if 800 < match['new_price'] < 1500]
        top_matches = [match for match in top_matches if match['match_score'] > 70]
        top_matches = top_matches[:100]

        # Output results
        for idx, match in enumerate(top_matches, 1):
            print(f"{idx}. Used: {match['used_title']} (${match['used_price']} + ${match['used_shipping']} shipping) [{match['used_condition']}, {match['used_store']}]")
            print(f"    New:  {match['new_title']} (${match['new_price']}) [{match['new_store']}]")
            print(f"    Price difference (new - used): ${match['price_difference']:.2f} (Match score: {match['match_score']})")
            print(f"    New URL: {match['new_url']}")
            print(f"    Used URL/Slug: {match['used_url']}")
            print()

    except Exception as e:
        print(f"Error: {e}")
