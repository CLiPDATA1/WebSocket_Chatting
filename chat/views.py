# chat > views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

def index(request):
    return render(request, 'chat/index.html')

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
        return render(request, 'chat/login.html')
    
def logout_view(request):
    logout(request)
    return redirect('index')