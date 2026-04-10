from django.urls import path
from .views import register_admin, register_student, admin_dashboard, create_election, list_elections, open_election, close_election, reset_election
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # for AUTH
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    # for REGISTRATION
    path('admin/register/', register_admin),
    path('student/register/', register_student),

    # protected admin dashboard
    path('admin/dashboard/', admin_dashboard),

    #Elections
    path('elections/create/', create_election),
    path('elections/', list_elections),

    path('elections/<int:pk>/open/', open_election),
    path('elections/<int:pk>/close/', close_election),
    path('elections/<int:pk>/reset/', reset_election),
]