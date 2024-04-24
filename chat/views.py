# chat > views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import HttpResponse, JsonResponse
from .forms import SignupForm
from . models import CustomUser, Message

def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return HttpResponse('로그인 실패')
    else:
        return render(request, 'login.html')
    
def logout_view(request):
    logout(request)
    return redirect('index')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(user.password)
            user.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def count_message(request):
    unread_count = request.user.message_set.filter(is_read=False).count()
    return render(request, 'index.html', {'unread_count': unread_count})