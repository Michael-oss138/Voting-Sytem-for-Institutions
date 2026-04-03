from django.urls import path
from .views import register_admin, register_student, admin_dashboard
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
]