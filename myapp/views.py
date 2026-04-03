from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status   
from .models import User, Election
from .serializers import AdminRegisterSerializer, StudentSignUpsertializer, ElectionSerializer
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
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_election(request):
    if nor request.user.role != 'admin':
        return Response(
            {"error": "Only admins can create elections"},
            status=status.HTTP_403_FORBIDDEN
        )
    serializer = ElectionSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(
            {"message": "Election Created Successfully"}
            status=status.HTTP_201_CREATED
        )
    return(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_elections(request):
    elections = Election.object.all()
    serializer = ElectionSerializer(elections, many=True)
    return Response(serializer.data)

    