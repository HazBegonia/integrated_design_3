from django.shortcuts import render
import requests
from .models import Form


# Create your views here.

def Index(request):
    return render(request, "index.html")

# -*- coding: utf-8 -*-
class Z:
    def __init__(self, address1, address2, travel_mode, preference, avoid_highway, API_KEY=None):
        self.address1 = address1
        self.address2 = address2
        self.travel_mode = travel_mode
        self.preference = preference
        self.avoid_highway = avoid_highway
        self.API_KEY = API_KEY or 'b00bc866aa48f53ba8fd21e3cdeb1c94'

    def get_geolocation(self, address):
        url = f'https://restapi.amap.com/v3/geocode/geo?address={address}&key={self.API_KEY}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'geocodes' in data and data['geocodes']:
                location = data['geocodes'][0]['location']
                lng, lat = location.split(',')
                return float(lat), float(lng)
            else:
                if 'info' in data:
                    print(f"Error Info: {data['info']}")
                return None
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None

    def get_route(self, origin, destination, mode, avoid_highway=3):
        if mode == 'driving':
            strategy = '3' if avoid_highway else '0'
            url = f'https://restapi.amap.com/v3/direction/driving?origin={origin}&destination={destination}&strategy={strategy}&key={self.API_KEY}'
        elif mode == 'walking':
            url = f'https://restapi.amap.com/v3/direction/walking?origin={origin}&destination={destination}&key={self.API_KEY}'
        elif mode == 'bicycling':
            url = f'https://restapi.amap.com/v4/direction/bicycling?origin={origin}&destination={destination}&key={self.API_KEY}'
        else:
            print(f"Invalid mode: {mode}")
            return None

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('status', '') == '1' or data.get('errcode', '') == 0:
                return data['route']
            else:
                print(f"Error Info: {data.get('info', 'No info available')}")
                return None
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None

    def parse_route(self, route, preference='fastest'):
        paths = route['paths']

        if preference == 'fastest':
            selected_path = min(paths, key=lambda x: int(x['duration']))
        elif preference == 'shortest':
            selected_path = min(paths, key=lambda x: int(x['distance']))
        else:
            selected_path = paths[0]

        total_distance = selected_path['distance']
        total_duration = selected_path['duration']
        steps = selected_path['steps']

        total_distance_km = float(total_distance) / 1000
        total_duration_min = int(total_duration) / 60

        travel_instructions = []
        for step in steps:
            instruction = step['instruction']
            distance = step['distance']
            duration = step['duration']
            travel_instructions.append(f"action: {instruction}, distance: {distance} m, time: {duration} s")

        return total_distance_km, total_duration_min, travel_instructions

    def insert_route_to_db(self, start_location, start_longitude, start_latitude, destination_location,
                           destination_longitude, destination_latitude, travel_mode, is_highway, distance, duration,
                           travel_instructions):
        try:
            formatted_duration = self.convert_minutes_to_hours_minutes(duration)

            form_instance = Form.objects.create(
                start_location=start_location,
                start_longitude=start_longitude,
                start_latitude=start_latitude,
                destination_location=destination_location,
                destination_longitude=destination_longitude,
                destination_latitude=destination_latitude,
                travel_mode=travel_mode,
                is_highway=is_highway,
                distance=distance,
                travel_time=formatted_duration,
                travel_instructions=travel_instructions,
            )
            print(f"Route saved to database with ID: {form_instance.id}")
        except Exception as e:
            print(f"Error saving route to database: {str(e)}")

    def convert_minutes_to_hours_minutes(self, minutes):
        hours = int(minutes // 60)
        remaining_minutes = int(minutes % 60)

        return f"{hours:02}:{remaining_minutes:02}"

    def Start(self):
        location1 = self.get_geolocation(self.address1)
        location2 = self.get_geolocation(self.address2)

        if location1 and location2:
            origin = f"{location1[1]},{location1[0]}"
            destination = f"{location2[1]},{location2[0]}"
            route = self.get_route(origin, destination, self.travel_mode, self.avoid_highway)
            if route:
                total_distance_km, total_duration_min, travel_instructions = self.parse_route(route,
                                                                                              self.preference)
                self.insert_route_to_db(
                    self.address1, location1[1], location1[0], self.address2, location2[1], location2[0],
                    self.travel_mode, self.avoid_highway, total_distance_km, total_duration_min, travel_instructions
                )
                print('ok')
            else:
                print("Failed to get route.")
        else:
            print("Failed to get one or both locations.")


def Info(request, address1, address2, travel_mode, preference, avoid_highway):
    z = Z(address1, address2, travel_mode, preference, avoid_highway)
    z.Start()
    context = {
        'a' : z.address1,
        'b' : z.address2,
        'c' : z.travel_mode,
        'd' : z.preference,
        'e' : z.avoid_highway,
    }
    return render(request, "info.html", context=context)