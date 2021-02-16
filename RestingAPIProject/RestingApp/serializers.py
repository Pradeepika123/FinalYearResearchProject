from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth.models import User
from .models import Dog, RestingActivityPerDay, Position, RestingActivity, DogStatus, Breed


class UserSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
        )
        validators = [
            UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=['username', 'email']
            )
        ]


class DogSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dog
        fields = ('id', 'name', 'birthday', 'breed', 'gender', 'user', 'imageUrl')


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ('name', 'position_id')


class RestingActivityPerDaySerializer(serializers.ModelSerializer):

    class Meta:
        model = RestingActivityPerDay
        fields = ('user', 'dog', 'date', 'position', 'timePeriod', 'week', 'month', 'year')


class RestingActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = RestingActivity
        fields = ('user_id', 'dog_id', 'date', 'time', 'hour', 'position')


class DogStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = DogStatus
        fields = ('user_id', 'dog_id', 'date', 'position', 'status')


class BreedSerializer(serializers.ModelSerializer):

    class Meta:
        model = Breed
        fields = ('name', 'slug', 'restingMinutes', 'restingPerDay', 'restingPerWeek')




