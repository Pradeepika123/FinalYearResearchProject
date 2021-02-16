import django
# from django.db import models
from djongo import models
from django.utils import timezone
from django.contrib.auth.models import User


class Dog(models.Model):
    GENDER_TYPES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unknown'),
    )
    name = models.CharField(max_length=50)
    birthday = models.DateField()
    breed = models.CharField(max_length=20)
    gender = models.CharField(max_length=1, choices=GENDER_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    imageUrl = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Position(models.Model):
    name = models.CharField(max_length=10)
    position_id = models.IntegerField()

    def __str__(self):
        "{}".format(self.name)


class RestingActivityPerDay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    position = models.IntegerField()
    timePeriod = models.IntegerField()
    week = models.IntegerField(null=True)
    month = models.IntegerField(null=True)
    year = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {}".format(self.dog, self.date, self.position, self.timePeriod)


class RestingActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    time = models.DateTimeField()
    hour = models.IntegerField(null=True)
    position = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {} - {}".format(self.dog, self.date, self.position, self.date, self.time)


class DogStatus(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dog = models.ForeignKey(Dog, on_delete=models.CASCADE)
    date = models.DateField(default=django.utils.timezone.now)
    position = models.IntegerField(null=True)
    status = models.CharField(null=True, max_length=25)

    def __str__(self):
        "{} - {} - {} - {} ".format(self.dog, self.date, self.position, self.date)


class Breed(models.Model):
    name = models.CharField(null=True, max_length=30)
    slug = models.CharField(null=True, max_length=20)
    restingMinutes = models.JSONField(default=list, blank=True, null=True)
    restingPerDay = models.IntegerField(null=True)
    restingPerWeek = models.IntegerField(null=True)

    def __str__(self):
        "{} - {} - {} - {} ".format(self.name, self.slug, self.restingMinutes, self.restingMinutes, self.restingPerDay,
                                    self.restingPerWeek)
