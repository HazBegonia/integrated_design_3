from django.shortcuts import render
import requests
from .models import Form, User, appuser
from datetime import datetime
import xgboost as xgb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate


# Create your views here.

# -*- coding: utf-8 -*-
class T:
    def __init__(self, X_train, y_train, Start_time, predicted_location=None):
        self.X_train = X_train
        self.y_train = y_train
        self.Start_time = Start_time
        self.predicted_location = ''

    def Start_predict(self):
        import xgboost as xgb
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        L = []
        Map = {}
        idx = 0
        for item in self.y_train:
            if item not in Map:
                Map[item] = idx
                idx += 1
            L.append(Map[item])

        num_classes = idx

        print(self.X_train)
        print(L)

        model = xgb.XGBClassifier(objective='multi:softprob', num_class=num_classes, random_state=42)
        model.fit(self.X_train, L)

        user_data = [[self.Start_time]]
        predicted_probabilities = model.predict_proba(user_data)[0]
        predicted_location_encoded = int(np.argmax(predicted_probabilities))

        if predicted_location_encoded < idx:
            predicted_location = list(Map.keys())[predicted_location_encoded]
            self.predicted_location = predicted_location
        if self.predicted_location == '':
            self.predicted_location = self.y_train[0]

# -*- coding: utf-8 -*-
class Z:
    def __init__(self, address1, address2, travel_mode, preference, avoid_highway,
                 start_longitude=None, start_latitude=None,
                 destination_longitude=None,destination_latitude=None,
                 API_KEY=None, total_distance_km=None, total_duration_min=None, travel_instructions=None):
        self.address1 = address1
        self.address2 = address2
        self.travel_mode = travel_mode
        self.preference = preference
        self.avoid_highway = avoid_highway
        self.API_KEY = API_KEY or 'b00bc866aa48f53ba8fd21e3cdeb1c94'
        self.total_distance_km = 0
        self.total_duration_min = 0
        self.travel_instructions = None
        start_longitude = 0
        start_latitude = 0
        destination_longitude = 0
        destination_latitude = 0

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

        self.total_distance_km = total_distance_km
        self.total_duration_min = total_duration_min
        self.travel_instructions = travel_instructions
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
        self.start_longitude = location1[1]
        self.start_latitude = location1[0]
        location2 = self.get_geolocation(self.address2)
        self.destination_longitude = location2[1]
        self.destination_latitude = location2[0]

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

def Login(request):
    user = appuser.objects.all()
    user = list(user)
    print(type(user))
    context = {
        'user' : user
    }
    return render(request, "denglu.html", context=context)


@csrf_exempt
def validate_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # If authentication is successful
            return JsonResponse({'valid': True})
        else:
            # If authentication fails
            return JsonResponse({'valid': False})
    else:
        return JsonResponse({'valid': False}, status=400)


@csrf_exempt
def Zhuce(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username already exists
        if appuser.objects.filter(user=username).exists():
            return JsonResponse({'success': False, 'error': 'user has been register'})

        # Save the user to the database
        try:
            new_user = appuser(user=username, password=password)
            new_user.save()
            return JsonResponse({'success': True})
        except Exception as e:
            print("Error saving user:", e)
            return JsonResponse({'success': False, 'error': 'err'})

    return render(request, "zhuce.html")

def Index(request):
    Tc = Form.objects.all()
    List1 = []
    List2 = []
    for item in reversed(Tc):
        if len(List1) < 3 and item.start_location not in List1:
            List1.append(item.start_location)
        if len(List2) < 3 and item.destination_location not in List2:
            List2.append(item.destination_location)

    L = User.objects.all()
    now = datetime.now()
    formatted_time = now.strftime("%Hh%Mm")
    hour_index = formatted_time.find("h")
    minute_index = formatted_time.find("m")
    hours = int(formatted_time[:hour_index])
    minutes = int(formatted_time[hour_index + len("h"):minute_index])
    now = int(hours * 60 + minutes)
    X1_train = []
    X2_train = []
    y_train = []
    for item in L:
        x1 = str(item)
        wz1 = x1.find("from:")
        wz2 = x1.find("to:")
        wz3 = x1.find("time:")
        X1_train.append(x1[wz1+5:wz2])
        X2_train.append(x1[wz2+3:wz3])
        y_train.append([int(x1[wz3+5:])])
    print(X1_train, X2_train, y_train)
    Tu1 = T(y_train, X1_train, now)
    Tu2 = T(y_train, X2_train, now)
    Tu1.Start_predict()
    Tu2.Start_predict()
    # print("-------------------------------------------")
    # print(Tu1.Start_time)
    # print(Tu2.Start_time)
    # print(Tu1.predicted_location)
    # print(Tu2.predicted_location)

    context = {
        'DB1' : List1,
        'DB2' : List2,
        'address1' : Tu1.predicted_location,
        'address2' : Tu2.predicted_location,
        'time' : now
    }
    return render(request, "index.html", context=context)

def Info(request, address1, address2, travel_mode, preference, avoid_highway):
    try:
        z = Z(address1, address2, travel_mode, preference, avoid_highway)
        z.Start()
        T = Form.objects.all()
        List1 = []
        List2 = []
        for item in reversed(T):
            if len(List1) < 3 and item.start_location not in List1:
                List1.append(item.start_location)
            if len(List2) < 3 and item.destination_location not in List2:
                List2.append(item.destination_location)

        now = datetime.now()
        formatted_time = now.strftime("%Hh%Mm")
        hour_index = formatted_time.find("h")
        minute_index = formatted_time.find("m")
        hours = int(formatted_time[:hour_index])
        minutes = int(formatted_time[hour_index + len("h"):minute_index])
        now = int(hours * 60 + minutes)

        try:
            User_instance = User.objects.create(
                current = now,
                start_location = address1,
                destination_location = address2
            )
            print(f"Route saved to database with ID: {User_instance.id}")
        except Exception as e:
            print(f"Error saving route to database: {str(e)}")

        context = {
            'address1' : z.address1,
            'address2' : z.address2,
            'travel_mode' : z.travel_mode,
            'preference' : z.preference,
            'avoid_highway' : z.avoid_highway,
            'total_distance_km' : z.total_distance_km,
            'total_duration_min' : z.total_duration_min,
            'travel_instructions' : z.travel_instructions,
            'DB1': List1,
            'DB2': List2
        }
        return render(request, "info.html", context=context)
    except:
        T = Form.objects.all()
        List1 = []
        List2 = []
        for item in T:
            if len(List1) < 3 and item.start_location not in List1:
                List1.append(item.start_location)
            if len(List2) < 3 and item.destination_location not in List2:
                List2.append(item.destination_location)
        context = {
            'DB1': List1,
            'DB2': List2,
        }
        return render(request, "index.html", context=context)

def Route1(request, address1, address2, travel_mode, preference, avoid_highway):
    z = Z(address1, address2, travel_mode, preference, avoid_highway)
    z.Start()
    context = {
        'address1' : address1,
        'address2' : address2,
        'travel_mode' : travel_mode,
        'preference' : preference,
        'avoid_highway' : avoid_highway,
        'destination_longitude' : z.destination_longitude,
        'start_longitude' : z.start_longitude,
        'destination_latitude' : z.destination_latitude,
        'start_latitude' : z.start_latitude
    }
    return render(request, "Route1.html", context=context)

def Route2(request, address1, address2, travel_mode, preference, avoid_highway):
    z = Z(address1, address2, travel_mode, preference, avoid_highway)
    z.Start()
    context = {
        'address1' : address1,
        'address2' : address2,
        'travel_mode' : travel_mode,
        'preference' : preference,
        'avoid_highway' : avoid_highway,
        'destination_longitude' : z.destination_longitude,
        'start_longitude' : z.start_longitude,
        'destination_latitude' : z.destination_latitude,
        'start_latitude' : z.start_latitude
    }
    return render(request, "Route2.html", context=context)