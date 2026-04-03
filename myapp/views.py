from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status   
from .models import User
from .serializers import AdminRegisterSerializer, StudentSignUpsertializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import permission_classes    
from rest_framework.permissions import IsAuthenticated, AllowAny
# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_student(request):
    serializer = StudentSignUpsertializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Student Registered Successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_admin(request):
    if not request.user.is_superuser:
        return Response(
        {"error": "Only Superusers can create admins"},
        status=status.HTTP_403_FORBIDDEN
        )

    serializer = AdminRegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Admin registered successfully."},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if request.user.role != 'admin':
        return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({"message": f"welcome {request.user.user_name}, you are an admin"})
    