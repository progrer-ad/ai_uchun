import pandas as pd
from datetime import datetime

# === 1. CSV fayllarni yuklash ===
tours = pd.read_csv("tours.csv")
hotels = pd.read_csv("samarkand_hotels_100.csv")
restaurants = pd.read_csv("restaurants.csv")
extra_costs = pd.read_csv("extra_costs.csv")  # kerak bo‘lsa
attractions = pd.read_csv("attractions.csv")
airports = pd.read_csv("airports.csv")

# === 2. Foydalanuvchi ma'lumotlari ===
user_input = {
    "start_date": "2025-08-10",
    "end_date": "2025-08-14",
    "adults": 1,
    "children": 0,
    "budget": 600.0  # USD per person
}

total_people = user_input["adults"] + user_input["children"]

# === 3. Safar davomiyligi ===
start = datetime.strptime(user_input["start_date"], "%Y-%m-%d")
end = datetime.strptime(user_input["end_date"], "%Y-%m-%d")
duration = (end - start).days

# === 4. Mos turlarni tanlash ===
suitable_tours = tours[
    (tours["duration_days"] <= duration) &
    (tours["min_budget_per_person"] <= user_input["budget"])
]

# === 5. Mehmonxona tanlash ===
hotels_filtered = hotels[
    hotels["hotel_price_per_night"] * duration <= user_input["budget"]
]

# Agar mehmonxona topilmasa, xatolikdan qochish uchun tekshiramiz
if not hotels_filtered.empty:
    selected_hotel = hotels_filtered.iloc[0]
    avg_hotel_price = selected_hotel["hotel_price_per_night"]
    hotel_cost = avg_hotel_price * duration * total_people
else:
    selected_hotel = None
    avg_hotel_price = 0.0
    hotel_cost = 0.0

# === 6. Restoran harajatlari ===
restaurants["daily_meal_cost"] = restaurants["restaurant_avg_meal_price"] * restaurants["meals_per_day"]
avg_meal_cost = restaurants["daily_meal_cost"].mean()
total_food_cost = avg_meal_cost * duration * total_people

# Eng mos restoran (arzonroq)
best_restaurant = restaurants.sort_values(by="daily_meal_cost").iloc[0]

# === 7. Tarixiy obidalar narxi ===
attraction_cost = 0
for _, attraction in attractions.iterrows():
    try:
        entry_fee = float(attraction['attraction_entry_fee'])
    except:
        entry_fee = 0.0
    try:
        guide_required = str(attraction['guide_required']).lower() == 'yes'
    except:
        guide_required = False
    try:
        guide_fee = float(attraction['guide_price']) if guide_required else 0.0
    except:
        guide_fee = 0.0

    attraction_cost += (entry_fee + guide_fee) * total_people

main_attraction = attractions.iloc[0]

# === 8. Aeroport taksi narxi ===
taxi_avg = airports["taxi_to_hotel_price"].mean()
main_airport = airports.iloc[0]

# === 10. Umumiy hisob ===
total_estimate = hotel_cost + total_food_cost + attraction_cost + taxi_avg

# === 11. Natija ===
print("\n--- TUR TAKLIFI ---")
if total_estimate <= user_input["budget"] * total_people:
    if not suitable_tours.empty:
        print("✅ Mos tur topildi:")
        print(suitable_tours.iloc[0][["title", "region", "duration_days", "min_budget_per_person"]])
    else:
        print("⚠️ Tur topilmadi, lekin boshqa xizmatlar ko'rsatilmoqda.")

    print(f"\n💰 Umumiy taxminiy xarajat: ${total_estimate:.2f}")
    print(f"🏨 Mehmonxona: ${hotel_cost:.2f}")
    print(f"🍽️ Ovqatlanish: ${total_food_cost:.2f}")
    print(f"🏛️ Tarixiy joylar: ${attraction_cost:.2f}")
    print(f"🚖 Taksi: ${taxi_avg:.2f}")

    print(f"\n--- HISOB-KITOB DETALLARI ---")
    print(f"Kunlar soni: {duration}")
    print(f"Umumiy odamlar soni: {total_people}")
    print(f"Mehmonxona o'rtacha narxi (kechasi): {avg_hotel_price:.2f}")
    print(f"Umumiy hisob: ${total_estimate:.2f}")
    print(f"Budjet: ${user_input['budget'] * total_people:.2f}")

    print(f"\n📍 Lokatsiyalar:")
    if selected_hotel is not None:
        print(f"🏨 Mehmonxona: {selected_hotel['hotel_name']} ({selected_hotel['hotel_location_name']})")
        print(f"    Koordinatalari: {selected_hotel['hotel_lat']}, {selected_hotel['hotel_lng']}")
    else:
        print("🏨 Mehmonxona: Topilmadi.")

    print(f"🍽️ Restoran: {best_restaurant['restaurant_name']}")
    print(f"    Koordinatalari: {best_restaurant['restaurant_lat']}, {best_restaurant['restaurant_lng']}")

    print(f"🛫 Aeroport: {main_airport['airport_name']}")
    print(f"    Koordinatalari: {main_airport['airport_lat']}, {main_airport['airport_lng']}")

    print(f"🏛️ Tarixiy joy: {main_attraction['attraction_name']} ({main_attraction['attraction_type']})")
    print(f"    Koordinatalari: {main_attraction['attraction_lat']}, {main_attraction['attraction_lng']}")

else:
    print("❌ Kechirasiz, byudjetga mos keladigan tur topilmadi.")
