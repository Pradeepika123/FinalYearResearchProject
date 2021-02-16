from django.urls import include, path
from . import views
from .views import UserRecordView

app_name = 'api'
urlpatterns = [

  path('', views.index, name='index'),
  path('register', views.register, name='register'),
  path('registerUser', views.registerUser),
  path('user/', UserRecordView.as_view(), name='users'),

  path('dogs/', views.DogList.as_view()),
  path('addDogProfile', views.add_DogProfile),
  path('getDogsBasedOnUser', views.getDogsBasedOnUser),  path('updateDogProfile/<int:dog_id>', views.update_DogProfile),
  path('deleteDogProfile', views.delete_DogProfile),

  path('addRestingActivityPerDay', views.add_restingActivityPerDay),
  path('updateRestingActivityPerDay/<int:id>', views.update_RestingActivityPerDay),
  path('restingActivityPerDay', views.RestingActivityPerDayList.as_view()),
  path('deleteRestingActivityPerDay/<int:resting_id>', views.delete_restingActivityPerDay),

  path('addPosition', views.add_Position),
  path('getPositionData/<int:position_id>', views.DataBasedOnPosition),
  path('getPositionNameById', views.getPositionNameById),

  # Daily
  path('getTotalMinutesPerDay', views.getTotalMinutesPerDay),
  path('getTotalMinutesPerHour', views.getTotalMinutesPerHour),
  path('highlightsPerDay', views.highlightsPerDay),

  # Weekly
  path('getTotalMinutesPerWeek', views.getTotalMinutesPerWeek),
  path('getTotalMinutesPerDayInWeek', views.getTotalMinutesPerDayInWeek),
  path('highlightsPerWeek', views.highlightsPerWeek),

  # Monthly
  path('getTotalMinutesPerMonth', views.getTotalMinutesPerMonth),
  path('getWeeklyDetailsInMonth', views.getWeeklyDetailsInMonth),
  path('highlightsPerMonth', views.highlightsPerMonth),

  # Annually
  path('getTotalMinutesPerYear', views.getTotalMinutesPerYear),
  path('getMonthlyDetailsInYear', views.getMonthlyDetailsInYear),
  path('highlightsPerYear', views.highlightsPerYear),

  # getting the readings
  path('readings', views.readings),
  path('trainingReadings', views.trainingReadings),
  path('endOfEachDay', views.endOfEachDay),
  path('compare', views.compare)

]
