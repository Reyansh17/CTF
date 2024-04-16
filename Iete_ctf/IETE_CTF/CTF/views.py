from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpResponse
import datetime
from django.views.decorators.csrf import csrf_exempt
import time
from .models import UserProfile, Questions, Submission
from django.contrib.auth.models import User, auth

endtime = 0
duration = 2700

@csrf_exempt
def index(request):
    return render(request, 'ctf/index.html')

@csrf_exempt
def error(request):
    return render(request, 'ctf/404.html')

@csrf_exempt
def about(request):
    return render(request, 'ctf/about.html')

@csrf_exempt
def instructions(request):
    return render(request, 'ctf/instructions.html')

@csrf_exempt
def hint(request):
    if request.method == 'POST':
        question_id = request.POST.get('id')
        try:
            question = Questions.objects.get(Qid=question_id)
            hint = question.Hint
            question_points = question.points
            user = User.objects.get(username=request.user.username)
            user_profile = UserProfile.objects.get(user=user)
            solved = Submission.objects.filter(question=question, user=user_profile).exists()
            if not solved:
                user_profile.score -= question_points * 0.1
                user_profile.save()
                Submission.objects.create(question=question, user=user_profile, curr_score=user_profile.score)
            return HttpResponse(hint)
        except Questions.DoesNotExist:
            return HttpResponse("Question not found")
    return HttpResponse("Method not allowed")

@csrf_exempt
def check(request):
    if request.method == 'POST':
        user = User.objects.get(username=request.user.username)
        user_profile = UserProfile.objects.get(user=user)
        qid = request.POST.get('Qid')
        flag = request.POST.get('flag')
        level = request.POST.get('customRadio')

        try:
            question = Questions.objects.get(Qid=qid)
            if level not in ['E', 'M', 'H']:
                return HttpResponse("-1")
            question.level = level
            if level == 'E':
                question.Easy += 1
            elif level == 'M':
                question.Med += 1
            else:
                question.Hard += 1
            question.save()

            solved = Submission.objects.filter(question=question, user=user_profile).exists()

            if flag == question.flag:
                if not solved:
                    user_profile.score += question.points
                    user_profile.save()
                    Submission.objects.create(question=question, user=user_profile, curr_score=user_profile.score)
                    return HttpResponse('1')
                else:
                    return HttpResponse('2')
            else:
                return HttpResponse('0')
        except Questions.DoesNotExist:
            return HttpResponse("Question not found")
    return HttpResponse("Method not allowed")

@csrf_exempt
def timer(request):
    start_time = datetime.datetime.now()
    global endtime
    endtime = start_time + datetime.timedelta(seconds=duration)
    return HttpResponse(start_time)

@csrf_exempt
def calc(request):
    now = datetime.datetime.now()
    if now <= endtime:
        diff = endtime - now
        return HttpResponse(diff.total_seconds())
    else:
        return HttpResponse("0")

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        rec_id = request.POST.get('receipt_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        score = 0

        try:
            User.objects.get(username=username)
            return render(request, 'ctf/register.html', {'error': "Username already exists"})
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password=password)
            user_profile = UserProfile.objects.create(user=user, Rid=rec_id, score=score)
            login(request, user)
            return redirect("instructions")

    elif request.method == 'GET':
        return render(request, 'ctf/register.html')

@csrf_exempt
def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            user_profile = UserProfile.objects.get(user=user)
            user_profile.time = timer()
            user_profile.save()
            return redirect("instructions")
        else:
            messages.error(request, 'Invalid credentials!')

    return render(request, 'ctf/login.html')

@csrf_exempt
def quest(request):
    remaining_time = calc()
    if remaining_time != "0":
        user = User.objects.get(username=request.user.username)
        user_profile = UserProfile.objects.get(user=user)
        questions = Questions.objects.all().order_by('Qid')
        submissions = Submission.objects.filter(user=user_profile).order_by('question_id')
        return render(request, 'ctf/quests.html', {'questions': questions, 'userprofile': user_profile, 'time': remaining_time, 'submission': submissions})
    else:
        return HttpResponse("Time is up!")

@csrf_exempt
def logout(request):
    auth.logout(request)
    return redirect("/")

@csrf_exempt
def leaderboard(request):
    sorted_users = UserProfile.objects.order_by("-score", "latest_sub_time")[:5]
    user_submissions = []
    for user in sorted_users:
        submissions = Submission.objects.filter(user=user)
        user_submissions.append(submissions)
    return render(request, 'ctf/hackerboard.html', context={'sub': user_submissions, 'user': sorted_users})
