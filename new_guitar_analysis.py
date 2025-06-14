import json
import os

# Load parsed guitar data
def load_parsed_guitars(file_path='new_guitars_combined.json'):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Calculate actual discount
def calculate_discount(guitar):
    try:
        original = float(guitar.get("original_price") or 0)
        current = float(guitar.get("price") or 0)
        if original > 0 and current > 0 and current < original:
            return original - current
        else:
            return 0
    except:
        return 0

# Main analysis
if __name__ == "__main__":
    try:
        guitars = load_parsed_guitars()
        
        # Add real discount value to each guitar
        for guitar in guitars:
            guitar["real_discount"] = calculate_discount(guitar)
        
        # Filter guitars with a real discount > 0
        guitars_with_discount = [g for g in guitars if g["real_discount"] > 0]
        
        # Sort by the biggest real discount
        top_discounted = sorted(guitars_with_discount, key=lambda g: g["real_discount"], reverse=True)[:10]
        
        print("Top 10 new guitars with the biggest real discounts:\n")
        for idx, guitar in enumerate(top_discounted, 1):
            print(f"{idx}. {guitar['title']} - {guitar['brand']}")
            print(f"   Original Price: ${guitar['original_price']}")
            print(f"   Current Price:  ${guitar['price']}")
            print(f"   Discount:       ${guitar['real_discount']:.2f}")
            print(f"   Condition:      {guitar['condition']}")
            print(f"   URL:            {guitar.get('url')}")
            print()
    
    except Exception as e:
        print(f"Error: {e}")
