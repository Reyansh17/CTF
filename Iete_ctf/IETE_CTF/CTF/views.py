from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpResponse
from django.core.cache import cache
import datetime
from django.contrib.sessions.models import Session
# from django.views.decorators.csrf import csrf_exempt
import time
from .models import UserProfile, Questions, Submission
from django.contrib.auth.models import User, auth

endtime = 54952
duration = 27000




def index(request):
    return render(request, 'ctf/index.html')
 

def error(request):
    return render(request, 'ctf/404.html')


def about(request):
    return render(request, 'ctf/about.html')


def inst(request):
    return render(request, 'ctf/instructions.html')

def team(request):
    return render (request,'ctf/team.html')


def hint(request):
    if request.method == 'POST':
        question_id = request.POST.get('id')
        question = Questions.objects.get(Qid=question_id)
        hint = question.Hint
        question_points = question.points
        user = User.objects.get(username=request.user.username)
        userprofile = UserProfile.objects.get(user=user)
        try:
            solved = Submission.objects.get(question=question, user=userprofile)
            return HttpResponse(hint)
        except Submission.DoesNotExist:
            if userprofile.score >= question_points * 0.1:  # Check if user has enough score to deduct
                if not cache.get(f"hint_deducted_{question_id}_{userprofile.user.id}"):  # Check if hint deduction has already been made
                    userprofile.score -= question_points * 0.1  # Deduct 10% of question points for viewing the hint
                    cache.set(f"hint_deducted_{question_id}_{userprofile.user.id}", True)  # Mark hint deduction as made
                else:
                    return HttpResponse("You have already viewed the hint.")  # Return if hint has already been viewed
                # Deducted 10% from the total score allotted to the question, so adding only 90% to the user's total score
                userprofile.score += question_points * 0.9
                userprofile.save()

                solved = Submission.objects.create(
                    question=question,
                    user=userprofile,
                    curr_score=userprofile.score
                )
                return HttpResponse(hint)
            else:
                return HttpResponse("You don't have enough score to view this hint!")
    return render(request, 'ctf/404.html')
    
def check(request):
    user = User.objects.get(username=request.user.username)
    userprofile = UserProfile.objects.get(user=user)
    questions = Questions.objects.all().order_by('Qid')
    if request.method == 'POST':
        req = request.POST
        Qid = req.get('Qid')
        flag = req.get('flag')
        level = req.get('customRadio')
        quest = Questions.objects.get(Qid=int(Qid))
        quest.Qid = Qid
        if level is None:
            return HttpResponse("-1")
        else:
            quest.level = level
            if level == 'E':
                quest.Easy += 1
            elif level == 'M':
                quest.Med += 1
            else:
                quest.Hard += 1
            print(quest.Easy, quest.Med, quest.Hard)
            quest.save()

            solved = Submission.objects.filter(question=quest, user=userprofile)

            if flag == quest.flag:
                if not solved:  # Check if the question is not already solved by the user
                    # Proceed with marking the question as solved
                    solved = Submission()
                    userprofile.score += quest.points
                    solved.question = quest
                    solved.user = userprofile
                    solved.curr_score = userprofile.score

                    sec = calc()
                    sec = duration - sec
                    solved.sub_time = time.strftime("%H:%M:%S", time.gmtime(sec))
                    userprofile.latest_sub_time = solved.sub_time
                    quest.solved_by += 1
                    solved.solved = 1
                    userprofile.totlesub += 1
                    userprofile.save()
                    solved.save()
                    quest.save()
                    print(userprofile.score)
                    print("FLAG IS CORRECT!")
                    return HttpResponse('1')  # Return success code indicating correct flag submission
                else:
                    # If the question is already solved, but the flag is correct, return '1'
                    return HttpResponse('1')  # Return code indicating correct flag submission
            else:
                print("INCORRECT")
                return HttpResponse('0')  # Return code indicating incorrect flag submission
    return HttpResponse("")

def timer():
    start = datetime.datetime.now()
    starttime = start.hour * 60 * 60 + start.minute * 60 + start.second
    global duration
    global endtime
    endtime = starttime + int(duration)
    print(starttime)
    return start


def calc():
    global endtime
    now = datetime.datetime.now()
    nowsec = now.hour * 60 * 60 + now.minute * 60 + now.second
    diff = endtime - nowsec
    print(nowsec, endtime)
    if nowsec < endtime:  # Change the comparison from <= to <
        return diff
    else:
        return 0



def signup(request):
    if request.method == 'POST':
        recid = request.POST.get('reciept_id')
        username = request.POST.get('username')
        password = request.POST.get('password')
        score = 0

        try:
            user = User.objects.get(username=username)
            return render(request, 'ctf/register.html', {'error': "Username Has Already Been Taken"})
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, password=password)
            # time = timer()
            userprofile = UserProfile(user=user, Rid=recid, score=score)
            userprofile.save()
            timer()
            login(request, user)

            return redirect("inst")

    elif request.method == 'GET':
        return render(request, 'ctf/register.html')


def login1(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            userprofile = UserProfile.objects.get(user=user)
            userprofile.time = timer()
            userprofile.save()
            return redirect("inst")
        else:
            messages.error(request, 'Invalid credentials!')

    return render(request, 'ctf/login.html')


def Quest(request):
    timer()  # Start the timer automatically when the user reaches the quest page
    var = calc()
    if var != 0:
        user = User.objects.get(username=request.user.username)
        userprofile = UserProfile.objects.get(user=user)
        questions = Questions.objects.all().order_by('Qid')
        submission = Submission.objects.values().filter(user=userprofile).order_by('question_id')
        print(submission)

        return render(request, 'ctf/quests.html',
                      {'questions': questions, 'userprofile': userprofile, 'time': var, 'submission': submission})
    else:
        return HttpResponse("<img src='https://images.unsplash.com/photo-1498811008858-d95a730b2ffc?q=80&w=1000&auto=format&fit=crop&ixlib=rb-4.0.3'>")


def logout(request):
    auth.logout(request)
    return redirect("/")


def leaderboard(request):
    # data = Submission.objects.all().order_by("-curr_score", "-sub_time")
    sorteduser = UserProfile.objects.all().order_by("-score","latest_sub_time")
    sub = Submission.objects.values().order_by('-user__score', 'user', 'sub_time')
    print(sub)
    count = 4
    sub_list = []
    for element in sorteduser:
        if count <= 4:
            sub = Submission.objects.values().filter(user_id=element.id)
            # sub.submission_set.all()
            # print(sub.submission_set)
            sub_list.append(sub)
            print(sub_list)
            count -= 1
        else:
            return render(request, 'ctf/hackerboard.html', context={'sub': sub_list, 'user': sorteduser})

    return render(request, 'ctf/hackerboard.html', context={'sub': sub_list, 'user': sorteduser})

from django.shortcuts import get_object_or_404
from django.shortcuts import render, HttpResponse
from django.http import FileResponse


def download_que_files(request,qid):
    if qid == '':
        return Response("No Question id found")
    que = get_object_or_404(Questions, pk=qid)
    file_path = que.file.path
    response = FileResponse(open(file_path, 'rb'))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{que.file.name}"'
    return response

'''''def first(request):
    var = calc()
    if var != 0:
        return render(request, 'ctf/.html', context={'time': var})
    else:
        return HttpResponse("time is 0:0")'''
# def leaderboard(request):
#     #data = Submission.objects.all().order_by("-curr_score", "-sub_time")
#     sorteduser = UserProfile.objects.all().order_by("-score")
# if user is not None:
#             auth.login(request, user)
#             try:
#                 userprofile = UserProfile.objects.get(user=user)
#                 userprofile.time = timer()
#                 userprofile.save()
#                 return redirect("inst")
#             except user.DoesNotExist:
#                 return render(request, 'CTF/404.html')
#
#         else:
#             return render(request, 'ctf/404.html')
