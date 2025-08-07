from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# === CSV ma'lumotlarni dastlab yuklab olamiz ===
tours = pd.read_csv("tours.csv")
hotels = pd.read_csv("samarkand_hotels_100.csv")
restaurants = pd.read_csv("restaurants.csv")
extra_costs = pd.read_csv("extra_costs.csv")
attractions = pd.read_csv("attractions.csv")
airports = pd.read_csv("airports.csv")


@app.route('/api/tour-suggestion', methods=['POST'])
def suggest_tour():
    data = request.json

    try:
        # === Foydalanuvchi ma'lumotlari ===
        start = datetime.strptime(data["start_date"], "%Y-%m-%d")
        end = datetime.strptime(data["end_date"], "%Y-%m-%d")
        adults = int(data["adults"])
        children = int(data["children"])
        budget = float(data["budget"])
        total_people = adults + children
        duration = (end - start).days

        # === Mos turlar ===
        suitable_tours = tours[
            (tours["duration_days"] <= duration) &
            (tours["min_budget_per_person"] <= budget)
        ]

        # === Mehmonxonalar ===
        hotels_filtered = hotels[
            hotels["hotel_price_per_night"] * duration <= budget
        ]

        if not hotels_filtered.empty:
            selected_hotel = hotels_filtered.iloc[0]
            avg_hotel_price = selected_hotel["hotel_price_per_night"]
            hotel_cost = avg_hotel_price * duration * total_people
        else:
            selected_hotel = None
            avg_hotel_price = 0.0
            hotel_cost = 0.0

        # === Ovqatlanish ===
        restaurants["daily_meal_cost"] = (
            restaurants["restaurant_avg_meal_price"] * restaurants["meals_per_day"]
        )
        avg_meal_cost = restaurants["daily_meal_cost"].mean()
        total_food_cost = avg_meal_cost * duration * total_people
        best_restaurant = restaurants.sort_values(by="daily_meal_cost").iloc[0]

        # === Tarixiy joylar ===
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

        # === Taksi narxi ===
        taxi_avg = airports["taxi_to_hotel_price"].mean()
        main_airport = airports.iloc[0]

        # === Umumiy hisob ===
        total_estimate = hotel_cost + total_food_cost + attraction_cost + taxi_avg
        user_total_budget = budget * total_people

        if total_estimate <= user_total_budget:
            response = {
                "success": True,
                "total_estimate": round(total_estimate, 2),
                "budget": round(user_total_budget, 2),
                "days": duration,
                "people": total_people,
                "services": {
                    "hotel": {
                        "name": selected_hotel["hotel_name"] if selected_hotel is not None else None,
                        "location": selected_hotel["hotel_location_name"] if selected_hotel is not None else None,
                        "price_total": round(hotel_cost, 2),
                        "lat": selected_hotel["hotel_lat"] if selected_hotel is not None else None,
                        "lng": selected_hotel["hotel_lng"] if selected_hotel is not None else None,
                    },
                    "restaurant": {
                        "name": best_restaurant["restaurant_name"],
                        "lat": best_restaurant["restaurant_lat"],
                        "lng": best_restaurant["restaurant_lng"],
                        "daily_meal_cost": round(avg_meal_cost, 2),
                        "total_food_cost": round(total_food_cost, 2)
                    },
                    "airport": {
                        "name": main_airport["airport_name"],
                        "taxi_price": round(taxi_avg, 2),
                        "lat": main_airport["airport_lat"],
                        "lng": main_airport["airport_lng"],
                    },
                    "attraction": {
                        "name": main_attraction["attraction_name"],
                        "type": main_attraction["attraction_type"],
                        "lat": main_attraction["attraction_lat"],
                        "lng": main_attraction["attraction_lng"],
                        "total_cost": round(attraction_cost, 2)
                    }
                },
                "suggested_tour": suitable_tours.iloc[0].to_dict() if not suitable_tours.empty else None
            }
        else:
            response = {
                "success": False,
                "message": "Kechirasiz, byudjetga mos keladigan tur topilmadi.",
                "total_estimate": round(total_estimate, 2),
                "budget": round(user_total_budget, 2)
            }

        return jsonify(response)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
