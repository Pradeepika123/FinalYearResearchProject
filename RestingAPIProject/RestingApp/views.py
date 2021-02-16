import json
import os
from datetime import timedelta

import lm as lm
import model.imagegenerator as im
from background_task import background
from background_task.models import Task
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from numba.cuda import const
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Dog, RestingActivityPerDay, Position, Breed, DogStatus, RestingActivity
from .serializers import DogSerializer, RestingActivityPerDaySerializer, PositionSerializer, BreedSerializer, \
    DogStatusSerializer, RestingActivitySerializer
from .serializers import UserSerializer
import calendar
import requests
from django.http import HttpResponse, response, request
from apscheduler.schedulers.background import BackgroundScheduler
from csv import writer
import joblib
import pandas as pd
import numpy as np
from sympy import fft
from datetime import datetime
from rest_framework.authtoken.models import Token
from django_file_md5 import calculate_md5
import cv2
from imutils.video import FileVideoStream
from glob import glob

def index(request):
    return render(request, 'user_example/index.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('user_example/index.html')

    else:
        form = UserCreationForm()
    context = {'form': form}
    return render(request, 'registration/register.html', context)


@api_view(["POST"])
@csrf_exempt
def registerUser(request):
    payload = json.loads(request.body)
    try:
        user = authenticate(username=payload['username'], password=payload['password'])

        userObject = User.objects.create(
            username=payload["username"],
            password=payload['password'],
            email=payload["email"]
        )
        serializer = UserSerializer(userObject)
        user = authenticate(username=payload['username'], password=payload['password'])
        login(request, user)
        return JsonResponse({'user': 'data', 'error': 'No'}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'NoUserError': 'error'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserRecordView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, format=None):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=ValueError):
            serializer.create(validated_data=request.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "error": True,
                "error_msg": serializer.error_messages,
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })

# DOGS
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getDogsBasedOnUser(request):
    payload = json.loads(request.body)
    dog = Dog.objects.filter(user_id=payload['userId'])
    serializer = DogSerializer(dog, many=True)
    return JsonResponse([{'dog': serializer.data[0]}], safe=False, status=status.HTTP_200_OK)


class DogList(APIView):
    def get(self, request):
        dogs = Dog.objects.all()
        serializer = DogSerializer(dogs, many=True)
        return Response(serializer.data)

    def post(self):
        pass


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_DogProfile(request):
    payload = json.loads(request.body)
    user = request.user
    try:
        dog = Dog.objects.create(
            name=payload["name"],
            birthday=payload["birthday"],
            breed=payload["breed"],
            gender=payload["gender"],
            user=user,
            imageUrl=payload['imageUrl']
        )
        serializer = DogSerializer(dog)
        return JsonResponse({'dog': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["PUT"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def update_DogProfile(request, dog_id):
    payload = json.loads(request.body)
    try:
        item = Dog.objects.filter(id=dog_id)
        # returns 1 or 0
        item.update(**payload)
        dog = Dog.objects.get(id=dog_id)
        serializer = DogSerializer(dog)
        return JsonResponse({'dog': serializer.data}, safe=False, status=status.HTTP_200_OK)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': Exception}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_DogProfile(request):
    payload = json.loads(request.body)
    try:
        dog = Dog.objects.get(id=payload["id"])
        dog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		
		
# POSITION
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_Position(request):
    payload = json.loads(request.body)
    try:
        position = Position.objects.create(
            name=payload["name"],
            position_id=payload["position_id"],

        )
        serializer = PositionSerializer(position)
        return JsonResponse({'position': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR) @ api_view(["POST"])


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getPositionNameById(request):
    payload = json.loads(request.body)
    position = Position.objects.filter(position_id=payload['id'])
    serializer = PositionSerializer(position, many=True)
    return JsonResponse([{'position': serializer.data[0]['name']}], safe=False, status=status.HTTP_200_OK)
	
	
# RESTING ACTIVITY PER DAY
@api_view(["GET"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def DataBasedOnPosition(request, position_id):
    positions = RestingActivityPerDay.objects.filter(postion_id=position_id)
    serializer = RestingActivityPerDaySerializer(positions, many=True)
    return JsonResponse({'positions': serializer.data}, safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_restingActivityPerDay(request):
    payload = json.loads(request.body)
    user = request.user
    dog = Dog.objects.get(id=payload["dog"])
    position = Position.objects.get(position_id=payload["position"])
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    month = ConvertedDate.month
    year = ConvertedDate.year
    try:
        resting = RestingActivityPerDay.objects.create(
            user=user,
            dog=dog,
            date=payload["date"],
            position=payload["position"],
            timePeriod=payload["timePeriod"],
            week=week,
            month=month,
            year=year
        )
        serializer = RestingActivityPerDaySerializer(resting)
        return JsonResponse({'resting': serializer.data}, safe=False, status=status.HTTP_201_CREATED)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({Exception}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR) @ api_view(["POST"])


@api_view(["PUT"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def update_RestingActivityPerDay(request, id):
    payload = json.loads(request.body)
    try:
        item = RestingActivityPerDay.objects.filter(id=id)
        # returns 1 or 0
        ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
        item.week = ConvertedDate.isocalendar()[1]
        item.month = ConvertedDate.month
        item.year = ConvertedDate.year
        item.update(**payload)
        resting = RestingActivityPerDay.objects.get(id=id)
        serializer = RestingActivityPerDaySerializer(resting)
        return JsonResponse({'resting': serializer.data}, safe=False, status=status.HTTP_200_OK)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something terrible went wrong'}, safe=False,
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RestingActivityPerDayList(APIView):
    def get(self, request):
        positions = RestingActivityPerDay.objects.all()
        serializer = RestingActivityPerDaySerializer(positions, many=True)
        return Response(serializer.data)


@api_view(["DELETE"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def delete_restingActivityPerDay(request, resting_id):
    try:
        resting = RestingActivityPerDay.objects.get(id=resting_id)
        resting.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': str(e)}, safe=False, status=status.HTTP_404_NOT_FOUND)
    except Exception:
        return JsonResponse({'error': 'Something went wrong'}, safe=False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		

# DAILY
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerDay(request):
    payload = json.loads(request.body)
    minutes = RestingActivity.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  date=payload['date'])
    serializer = RestingActivitySerializer(minutes, many=True)

    if len(serializer.data) > 0:
        dailyTotal = 0
        for i in range(len(serializer.data)):
            dailyTotal += 1
        return JsonResponse([{'minutes per day': dailyTotal}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'minutes per day': 0}], safe=False,
                            status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerHour(request):
    payload = json.loads(request.body)
    n = 24
    hours = [None] * n
    for i in range(24):
        period = RestingActivity.objects.filter(position=payload['position'], dog=payload['dog'],
                                               date=payload['date'], hour=i)
        serializer1 = RestingActivitySerializer(period, many=True)

        hourlyTotal = 0
        if len(serializer1.data) > 0:
            for j in range(len(serializer1.data)):
                hourlyTotal += 1

            hours[i] = hourlyTotal

    return JsonResponse({'hour array': hours, 'date': payload['date']}, safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerDay(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    yesterday = ConvertedDate - timedelta(days=1)
    todayActivity = RestingActivity.objects.filter(position=payload['position'], dog=payload['dog'],
                                                        date=payload['date'])
    yesterdayActivity = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                            date=yesterday)
    serializer1 = RestingActivitySerializer(todayActivity, many=True)
    serializer2 = RestingActivityPerDaySerializer(yesterdayActivity, many=True)

    if len(serializer1.data) == 0:
        today = 0
    if len(serializer2.data) == 0:
        yesterdayTime = 0
    if len(serializer2.data) != 0:
        yesterdayTime = serializer2.data[0]['timePeriod']

    dailyTotal = 0
    for i in range(len(serializer1.data)):
        dailyTotal += 1

    if dailyTotal > yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is higher than yesterday'}], safe=False,
            status=status.HTTP_200_OK)
    elif dailyTotal < yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is lower than yesterday'}], safe=False,
            status=status.HTTP_200_OK)
    elif dailyTotal == yesterdayTime:
        return JsonResponse(
            [{'TODAY': dailyTotal, 'YESTERDAY': yesterdayTime, 'Highlights':
                'time is equal to yesterday'}], safe=False,
            status=status.HTTP_200_OK)
			
			
# WEEKLY
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  week=week)
    serializer = RestingActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'week': week, 'minutes per week': totalSum}], safe=False, status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'minutes per week': 0}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerDayInWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  week=week)
    entries = entries.order_by('date')
    serializer = RestingActivityPerDaySerializer(entries, many=True)
    return JsonResponse([{'week': week, 'data': serializer.data}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerWeek(request):
    payload = json.loads(request.body)
    ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    week = ConvertedDate.isocalendar()[1]
    thisWeekEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                          week=week)
    previousWeek = week - 1
    lastWeekEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                          week=previousWeek)
    serializer1 = RestingActivityPerDaySerializer(thisWeekEntries, many=True)
    serializer2 = RestingActivityPerDaySerializer(lastWeekEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'greater than last Week'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'lesser than last Week'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this Week': totalSum1, 'last Week': totalSum2, 'Highlights':
                'equal to last Week'}], safe=False,
            status=status.HTTP_200_OK)


# MONTHLY
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getWeeklyDetailsInMonth(request):
    global range
    payload = json.loads(request.body)
    year = payload['year']
    month = payload['month']
    ending_day = calendar.monthrange(year, month)[1]  # get the last day of month
    initial_week = datetime(year, month, 1).isocalendar()[1]
    ending_week = datetime(year, month, ending_day).isocalendar()[1]
    weeks = []
    for i in range(initial_week, ending_week + 1):
        weeks.append(i)
    weekArray, minutes = [], []
    for i in weeks:
        weekArray.append(i)
        entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                      week=i)

        serializer = RestingActivityPerDaySerializer(entries, many=True)
        totalSum = 0
        for j in range(len(serializer.data)):
            value = serializer.data[j]['timePeriod']
            totalSum += float(value)
        minutes.append(totalSum)

    return JsonResponse([{'month': payload['month'], 'initial week': initial_week, 'final week': ending_week,
                          'weeks': weekArray, 'minutes': minutes}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerMonth(request):
    payload = json.loads(request.body)

    entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  month=payload['month'])
    serializer = RestingActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'month': payload['month'], 'minutes per month': totalSum}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'month': payload['month'], 'minutes per month': 0}], safe=False,
                            status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerMonth(request):
    payload = json.loads(request.body)
    month = payload['month']
    thisMonthEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                           month=month)
    previousMonth = int(month) - 1
    lastMonthEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                           month=previousMonth)
    serializer1 = RestingActivityPerDaySerializer(thisMonthEntries, many=True)
    serializer2 = RestingActivityPerDaySerializer(lastMonthEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'greater than last month'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'lesser than last month'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this month': totalSum1, 'last month': totalSum2, 'Highlights':
                'equal to last month'}], safe=False,
            status=status.HTTP_200_OK)


# ANNUALLY
@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getTotalMinutesPerYear(request):
    payload = json.loads(request.body)
    # ConvertedDate = datetime.strptime(payload['date'], "%Y-%m-%d").date()
    # year = ConvertedDate.year
    entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  year=payload['year'])
    serializer = RestingActivityPerDaySerializer(entries, many=True)
    totalSum = 0
    for i in range(len(serializer.data)):
        value = serializer.data[i]['timePeriod']
        totalSum += float(value)

    if len(serializer.data) > 0:
        return JsonResponse([{'year': payload['year'], 'minutes per year': totalSum}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'year': payload['year'], 'minutes per year': 0}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def getMonthlyDetailsInYear(request):
    global range
    payload = json.loads(request.body)
    year = payload['year']
    minutes = []
    for i in range(1, 13):
        entries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                      month=i, year=year)
        serializer = RestingActivityPerDaySerializer(entries, many=True)
        totalSum = 0
        for j in range(len(serializer.data)):
            value = serializer.data[j]['timePeriod']
            totalSum += float(value)
        minutes.append(totalSum)

    return JsonResponse([{'year': payload['year'], 'minutes': minutes}], safe=False, status=status.HTTP_200_OK)


@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def highlightsPerYear(request):
    payload = json.loads(request.body)

    thisWeekEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                          year=payload['year'])
    previousYear = int(payload['year']) - 1
    lastWeekEntries = RestingActivityPerDay.objects.filter(position=payload['position'], dog=payload['dog'],
                                                          year=previousYear)
    serializer1 = RestingActivityPerDaySerializer(thisWeekEntries, many=True)
    serializer2 = RestingActivityPerDaySerializer(lastWeekEntries, many=True)

    totalSum1 = 0
    for i in range(len(serializer1.data)):
        value = serializer1.data[i]['timePeriod']
        totalSum1 += float(value)

    totalSum2 = 0
    for i in range(len(serializer2.data)):
        value = serializer2.data[i]['timePeriod']
        totalSum2 += float(value)

    if totalSum1 > totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'greater than last year'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 < totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'lesser than last year'}], safe=False,
            status=status.HTTP_200_OK)
    elif totalSum1 == totalSum2:
        return JsonResponse(
            [{'this year': totalSum1, 'last year': totalSum2, 'Highlights':
                'equal to last year'}], safe=False,
            status=status.HTTP_200_OK)



# load model
model, graph = lm.ModelInitializer()


#Video Processing and resting state prediction
@csrf_exempt
def restStatePrediction():
    cap = cv2.VideoCapture('rtsp://admin:UEWOMQ@192.168.0.100:554/H.264')
    results = []
    i = 0
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        cv2.imwrite('kang' + str(i) + '.jpg', frame)
        i += 1
        img_tensor = im.InputImageGeneratorVideo(frame)
        prediction = pd.Predict(img_tensor, model, graph)
        prediction['frame'] = frame
        results.append(prediction)

        Data.append_list_as_row(Reading.csv,frame,results)
    cap.release()
    cv2.destroyAllWindows()

def append_list_as_row(file_name, list_of_elem):
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        csv_writer.writerow(list_of_elem)

class Data:
    data = ''
    Read = []

    def __init__(self, data):
        self.data = data

    def ReadData(self):
        self.Read = pd.read_csv(self.data)
        return self.Read

    def append_list_as_row(self, file_name, list_of_elem):
        # Open file in append mode
        with open(file_name, 'a+', newline='') as write_obj:
            # Create a writer object from csv module
            csv_writer = writer(write_obj)
            # Add contents of list as last row in the csv file
            csv_writer.writerow(list_of_elem)

#sensor resting time and calculate mean resting time
def getSensorRestTime(rest):
    activity = rest
    sensorData = Walk.objects.filter(activity=activity)
    serializer = WalkSerializer(sensorData, many=True)

    for i in range(len(serializer.data)):
        value = serializer.data[i]['positionPerDay']
    return value

@api_view(["POST"])
@csrf_exempt
@permission_classes([IsAuthenticated])
def calcMeanRestingTime(request):
    payload = json.loads(request.body)
    minutes = RestingActivity.objects.filter(position=payload['position'], dog=payload['dog'],
                                                  date=payload['date'])
    serializer = RestingActivitySerializer(minutes, many=True)

    if len(serializer.data) > 0:
        dailyTotal = 0
        for i in range(len(serializer.data)):
            dailyTotal += 1
        return JsonResponse([{'minutes per day': dailyTotal}], safe=False,
                            status=status.HTTP_200_OK)
    else:
        return JsonResponse([{'minutes per day': 0}], safe=False,
                            status=status.HTTP_200_OK)

#resting activity level changes
def compareBreedData(breed, restingMinutes):
    RestingMinutes, breedRestingMinutes = 0, 0
    print("Now comparing " + breed)
    activityStatusOfTheDog = ''

    breedRestingMinutes = getBreedActivityData(breed)


    if RestingMinutes > breedRestingMinutes:
        print("Activity level is high")             #Activity -> Resting
        activityStatusOfTheDog = 'high'
    elif RestingMinutes < breedRestingMinutes:
        print("The actual activity level of the dog is : " + str(breedRestingMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(RestingMinutes) + " minutes")
        print("Therefore .. Activity level is low")
        activityStatusOfTheDog = 'low'
    elif RestingMinutes == breedRestingMinutes:
        print("Activity level is equal")
        activityStatusOfTheDog = 'equal'

    # Add the status to the Dog Status Table
    ConvertedDate = datetime.now()

    activityStatus = DogStatus.objects.create(
        user_id=1,
        dog_id=1,
        date=ConvertedDate,
        activity=1,
        status=activityStatusOfTheDog,
    )
    DogStatusSerializer(activityStatus)


def getBreedActivityData(breed):
    name = breed
    breedData = Breed.objects.filter(name=name)
    serializer = BreedSerializer(breedData, many=True)

    for i in range(len(serializer.data)):
        value = serializer.data[i]['positionPerDay']
    return value


@api_view(["POST"])
def compare(request):
    printHello(schedule=10, repeat=Task.DAILY)
    payload = json.loads(request.body)
    breed = payload['breed']
    ActivityMinutes = payload['time']
    RestingMinutes, breedRestingMinutes = 0, 0
    activityStatusOfTheDog = ''
    print(breed)
    breedRestingMinutes = getBreedActivityData(breed)
    RestingMinutes = ActivityMinutes

    halfValue = breedRestingMinutes / 2
    if RestingMinutes > breedRestingMinutes:
        print("The actual activity level of the dog is : " + str(breedRestingMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(RestingMinutes) + " minutes")
        print("Activity level is high")
        activityStatusOfTheDog = 'high'
    elif RestingMinutes < halfValue:
        print("The actual activity level of the dog is : " + str(breedRestingMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(RestingMinutes) + " minutes")
        print("Therefore .. Activity level is low")
        activityStatusOfTheDog = 'low'
    elif (RestingMinutes <= breedRestingMinutes) and (RestingMinutes >= halfValue):
        print("The actual activity level of the dog is : " + str(breedRestingMinutes) + " minutes")
        print("But the current activity level of the dog is " + str(RestingMinutes) + " minutes")
        print("Activity level is equal")
        activityStatusOfTheDog = 'active'
    return JsonResponse({'status': activityStatusOfTheDog}, safe=False, status=status.HTTP_201_CREATED)




class Main:
    def __init__(self,obj):
        d = Data('Readings.csv')
        data = d.ReadData()
        i, j = 0, 0
        length = len(data)
        while i <= length:
            Index = []
            count = i + 30
            if j < length:
                while j <= count:
                    Index.append(j)
                    j = j + 1
                #video prediction
                videoD = restStatePrediction()
                #rest time from video
                if(videoD.prediction = 1):
                    videoRestTime = getTotalMinutesPerDay(videoD)
                #rest time from sensor
                sensorD = getSensorRestTime(0)
                #find mean rest time
                meanRestTime = (videoD+sensorD)/2
                #update db
                calcMeanRestingTime(meanRestTime)
                #resting activity change
                compare(meanRestTime)
            else:
                break
            i = i + 30
