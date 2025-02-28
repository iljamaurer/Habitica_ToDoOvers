# -*- coding: utf-8 -*-
"""Django Views - Habitica To Do Over tool
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from django.shortcuts import render, redirect
from .app_functions.to_do_overs_data import ToDoOversData
from .forms import TasksModelForm
from .models import Users, Tasks, Tags
import django.contrib.messages as messages
import jsonpickle
from .app_functions.cipher_functions import encrypt_text
from django.http import HttpResponseServerError
import json
from datetime import datetime


def index(request):
    """Homepage/Index View

    Args:
        request: the request from user.

    Returns:
        Rendering of the index page.
    """
    return render(request, "to_do_overs/index.html")


def login(request):
    """Login request with username and password.

    This view will never actually be displayed.

    Args:
        request: the request from user.

    Returns:
        Redirects the index page on error. Redirects to the dashboard on success.
    """
    session_class = ToDoOversData()

    session_class.username = request.POST.get("username", False)
    password = request.POST.get("password", False)

    if session_class.login(password):
        request.session["session_data"] = jsonpickle.encode(session_class)
        request.session.create()
        return redirect("to_do_overs:dashboard")
    else:
        messages.warning(request, "Login failed.")
        return redirect("to_do_overs:index")


def login_api_key(request):
    """Login request with user ID and API token.

    This view will never actually be displayed.

    Args:
        request: the request from user.

    Returns:
        Redirects the index page on error. Redirects to the dashboard on success.
    """
    session_class = ToDoOversData()

    session_class.hab_user_id = request.POST.get("user_id", False)
    session_class.api_token = encrypt_text(request.POST.get("api_token"))

    if session_class.login_api_key():
        request.session["session_data"] = jsonpickle.encode(session_class)
        request.session.create()
        return redirect("to_do_overs:dashboard")
    else:
        messages.warning(request, "Login failed.")
        return redirect("to_do_overs:index")


def dashboard(request):
    """The dashboard view once a user has logged in.

    Args:
        request: the request from user.

    Returns:
        Renders the dashboard if user is logged in. Redirects to index if user is not logged in.
    """
    if "session_data" in request.session:
        session_class = jsonpickle.decode(request.session["session_data"])
    else:
        messages.warning(request, "Please log in again.")
        return redirect("to_do_overs:index")

    task_list = Tasks.objects.filter(owner__user_id=session_class.hab_user_id)

    if session_class.logged_in:
        username = session_class.username
        return render(
            request,
            "to_do_overs/dashboard.html",
            {
                "username": username,
                "tasks": task_list,
            },
        )
    else:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")


def create_task(request):
    """View to create a new task.

    Args:
        request: the request from user.

    Returns:
        Renders the create task page if user is logged in. Redirects to index if user is logged out.
    """
    if "session_data" in request.session:
        session_class = jsonpickle.decode(request.session["session_data"])
    else:
        messages.warning(request, "Please log in again.")
        return redirect("to_do_overs:index")

    if session_class.logged_in:
        # Get the user's tags
        session_class = jsonpickle.decode(request.session["session_data"])
        session_class.get_user_tags()

        form = TasksModelForm(session_class.hab_user_id)

        return render(request, "to_do_overs/create_task.html", {"form": form})

    else:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")


def create_task_action(request):
    """Action to create task. This view is never displayed.

    Args:
        request: the request from user.

    Returns:
        Redirects to index if user is logged out. Otherwise attempts to create task. If creation is successful,
        redirects to dashboard. If creation fails, redirect back to create task page.
    """
    session_class = jsonpickle.decode(request.session["session_data"])
    if session_class.logged_in:
        form = TasksModelForm(session_class.hab_user_id, request.POST)
        print(form.errors)
        if form.is_valid():
            task = Tasks()
            task.name = form.data["name"]
            task.notes = form.data["notes"]
            task.days = form.data["days"]
            task.delay = form.data["delay"]
            task.priority = form.data["priority"]
            task.type = form.data["type"]
            task.weekday = form.data["weekday"]
            task.monthday = form.data["monthday"]

            task.notes += "\n\n:repeat:Automatically created by ToDoOvers API tool."
            task.owner = Users.objects.get(user_id=session_class.hab_user_id)

            # convert tags from their DB ID to the tag UUID
            tags = request.POST.getlist("tags")
            tag_query_list = Tags.objects.filter(pk__in=set(tags)).values("tag_id")
            tag_list = []
            for tag in tag_query_list:
                tag_list.append(tag["tag_id"])

            session_class.tags = tag_list

            session_class.notes = task.notes
            session_class.task_name = task.name
            session_class.task_days = task.days
            session_class.task_delay = task.delay
            session_class.priority = task.priority
            session_class.type = task.type
            session_class.weekday = task.weekday
            session_class.monthday = task.monthday
            request.session["session_data"] = jsonpickle.encode(session_class)

            if int(session_class.task_days) < 0:
                messages.warning(request, "Invalid repeat day number.")
                return redirect("to_do_overs:create_task")
            if session_class.create_task():
                messages.success(request, "Task created successfully.")
                task.task_id = session_class.task_id

                task.save()

                # add tags
                for tag in session_class.tags:
                    tag_object = Tags.objects.get(tag_id=tag)
                    task.tags.add(tag_object)

                return redirect("to_do_overs:dashboard")
            else:
                messages.warning(request, "Task creation failed.")
                return redirect("to_do_overs:create_task")
        else:
            messages.warning(request, "Invalid form data.")
            return redirect("to_do_overs:create_task")
    else:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")


def create_daily_report_action(request):
    session_class = jsonpickle.decode(request.session["session_data"])
    if session_class.logged_in:
        todo_results = session_class.get_today_completed_tasks()
        habit_results = session_class.get_today_completed_habits()
        daily_results = session_class.get_today_completed_dailies()
        date_today = (
            f"{datetime.today().year}{datetime.today().month}{datetime.today().day}"
        )
        results = {
            "date": date_today,
            "habits": habit_results,
            "dailys": daily_results,
            "todos": todo_results,
        }
        with open("reports/" + date_today + ".txt", "w") as f:
            json.dump(results, f, default=str)
    return dashboard(request)


def logout(request):
    """Logout and clear the session.

    Args:
        request: the request from user.

    Returns:
        Renders index page.
    """
    request.session.flush()
    return render(request, "to_do_overs/index.html")


def delete_task(request, task_pk):
    """Deletes the requested task from the tool database.

    Args:
        request: the request from user.
        task_pk: the ID of the task to be deleted.

    Returns:
        Renders dashboard page with error, or confirmation page to confirm deletion.
    """
    if "session_data" in request.session:
        session_class = jsonpickle.decode(request.session["session_data"])
    else:
        messages.warning(request, "Please log in again.")
        return redirect("to_do_overs:index")

    if not session_class.logged_in:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")

    # first we need to check that this user owns this task
    task = Tasks.objects.get(pk=task_pk)
    owner = Users.objects.get(pk=task.owner.pk)

    logged_in_user = Users.objects.get(user_id=session_class.hab_user_id)
    if logged_in_user.pk == owner.pk:
        return render(request, "to_do_overs/delete_task.html", {"task": task})
    else:
        messages.warning(request, "You are not authorized to delete that task.")
        return redirect("to_do_overs:dashboard")


def delete_task_confirm(request, task_pk):
    """Actually does the task deletion.

    Args:
        request: the request from user.
        task_pk: the ID of the task to be deleted.

    Returns:
        Redirects to dashboard with success or failure.
    """
    if "session_data" in request.session:
        session_class = jsonpickle.decode(request.session["session_data"])
    else:
        messages.warning(request, "Please log in again.")
        return redirect("to_do_overs:index")

    if not session_class.logged_in:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")

    # first we need to check that this user owns this task
    task = Tasks.objects.get(pk=task_pk)
    owner = Users.objects.get(pk=task.owner.pk)

    logged_in_user = Users.objects.get(user_id=session_class.hab_user_id)
    if logged_in_user.pk == owner.pk:
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect("to_do_overs:dashboard")
    else:
        messages.warning(request, "You are not authorized to delete that task.")
        return redirect("to_do_overs:dashboard")


def edit_task(request, task_pk):
    """Edit a task.

    Args:
        request: the request from user.
        task_pk: the ID of the task to be edited.

    Returns:
        Renders the edit screen for the task.
    """
    if "session_data" in request.session:
        session_class = jsonpickle.decode(request.session["session_data"])
    else:
        messages.warning(request, "Please log in again.")
        return redirect("to_do_overs:index")

    if not session_class.logged_in:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")

    # first we need to check that this user owns this task
    task = Tasks.objects.get(pk=task_pk)
    owner = Users.objects.get(pk=task.owner.pk)

    logged_in_user = Users.objects.get(user_id=session_class.hab_user_id)
    if logged_in_user.pk == owner.pk:
        # get the user's tags
        session_class.get_user_tags()

        form = TasksModelForm(session_class.hab_user_id, instance=task)
        return render(
            request, "to_do_overs/edit_task.html", {"form": form, "task_pk": task_pk}
        )
    else:
        messages.warning(request, "You are not authorized to edit that task.")
        return redirect("to_do_overs:dashboard")


def edit_task_action(request, task_pk):
    """Actually do the task edit.

    Args:
        request: the request from user.
        task_pk: the ID of the task to be edited.

    Returns:
        Redirects to dashboard on success. Shows edit again on failure.
    """
    session_class = jsonpickle.decode(request.session["session_data"])

    if not session_class.logged_in:
        messages.warning(request, "You need to log in to view that page.")
        return redirect("to_do_overs:index")

    # first we need to check that this user owns this task
    task_lookup = Tasks.objects.get(pk=task_pk)
    session_class.task_id = task_lookup.task_id
    owner = Users.objects.get(pk=task_lookup.owner.pk)

    logged_in_user = Users.objects.get(user_id=session_class.hab_user_id)
    if logged_in_user.pk == owner.pk:
        form = TasksModelForm(session_class.hab_user_id, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            # task.notes += "\n\n:repeat:Automatically created by ToDoOvers API tool."
            # task.owner = Users.objects.get(user_id=session_class.hab_user_id)

            session_class.notes = task.notes
            session_class.task_name = task.name
            session_class.task_days = task.days
            session_class.task_delay = task.delay
            session_class.priority = task.priority
            session_class.type = task.type
            session_class.weekday = task.weekday
            session_class.monthday = task.monthday

            # convert tags from their DB ID to the tag UUID
            tags = request.POST.getlist("tags")
            tag_query_list = Tags.objects.filter(pk__in=set(tags)).values("tag_id")
            tag_list = []
            for tag in tag_query_list:
                tag_list.append(tag["tag_id"])

            session_class.tags = tag_list

            request.session["session_data"] = jsonpickle.encode(session_class)

            if int(session_class.task_days) < 0:
                messages.warning(request, "Invalid repeat day number.")
                return redirect("to_do_overs:edit_task", task_pk)
            if session_class.edit_task():
                messages.success(request, "Task edited successfully.")
                task.task_id = session_class.task_id
                task.owner = task_lookup.owner
                Tasks.objects.filter(task_id=task.task_id).update(
                    notes=task.notes,
                    name=task.name,
                    days=task.days,
                    priority=task.priority,
                    delay=task.delay,
                    type=task.type,
                    weekday=task.weekday,
                    monthday=task.monthday,
                )

                task_object = Tasks.objects.get(task_id=task.task_id)
                # clear the tags
                task_object.tags.clear()
                # re-add the tags
                for tag in tags:
                    task_object.tags.add(tag)

                return redirect("to_do_overs:dashboard")
            else:
                messages.warning(request, "Task editing failed.")
                return redirect("to_do_overs:edit_task", task_pk)
    else:
        messages.warning(request, "You are not authorized to edit that task.")
        return redirect("to_do_overs:dashboard")


def test_500_view(request):
    return HttpResponseServerError()
