from django.shortcuts import render,HttpResponse,redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login,logout
from helper.Get_Username_Object import GetUserObject
from .forms import CreateUser,AuthenticationForm
from helper.logger_setup import setup_logger
from django.contrib import messages
from .serializers import UserSerializer
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


###Initiate the model accounts_app logger opject
logger=setup_logger('accounts_app')


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request.POST)
        if form.is_valid():
            get_user_parameters=GetUserObject()
            username,password=get_user_parameters.get_user_from_form(form)
            if username is None:
                messages.error(request,"This User not exist you need to Register First")
                return render(request, 'login.html', {'form': form})
            #Check login
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('/home')
            else:
                messages.error(request,"Th Password is not valid")
                return render(request, 'login.html', {'form': form})
        else:
            messages.error(request,"InValid form return to Admin")
            return render(request, 'login.html', {'form': form})
    else:
        form = AuthenticationForm()
        if 'next' in request.GET:
            messages.warning(request,'You must login first to access this link')
        return render(request, 'login.html', {'form': form})

def create_view(request):
    if request.method=="POST":
        form=CreateUser(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('User Created Sucessfully')
        else:
            return HttpResponse(f'User Creation Failed {form.errors.as_json()}')
    form=CreateUser()
    return render(request,'create_user.html',{'form':form})

def logout_view(request):
    logout(request)
    messages.info(request,"User logout successfully...")
    return HttpResponse('This Should be application Main Page')


class CreateUserAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Attempting to create user with data: {request.data}")
        serializer = UserSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            logger.info(f"User created with ID: {user.id}")
            return Response({'message': 'User created successfully', 'user_id': user.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        serializer = UserSerializer()
        return Response({
            'message': 'This endpoint is for creating users only. Use POST method.',
            'fields_required': list(serializer.fields.keys())
        }, status=status.HTTP_200_OK)


class UpdateUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'User updated successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating user {user.id}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeleteUserAPI(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        try:
            user.delete()
            logger.info(f"User {user.id} deleted.")
            return Response({'message': 'User deleted successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error deleting user {user.id}: {e}")
            return Response({'error': 'Failed to delete user.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
