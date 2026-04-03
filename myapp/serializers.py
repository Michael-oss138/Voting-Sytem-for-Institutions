from rest_framework import serializers
from .models import User


class StudentSignUpsertializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        return User.objects.create_user(
            username = validated_data['username'],
            password = validated_data['password'],
            role = 'student'
        )


class AdminRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            role='admin',
            is_staff = True
        )