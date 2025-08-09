from django.urls import path,include
from . import views
from rest_framework.routers import DefaultRouter

app_name = "accounts_app"

urlpatterns = [
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('create_view/',views.create_view,name='create_view'),
    path('api/createuser/', views.CreateUserAPI.as_view(), name='createuser'),
    path('api/deleteuser/', views.DeleteUserAPI.as_view(), name='deleteuser'),
    path('api/updateuser/', views.UpdateUserAPI.as_view(), name='updateuser'),
]