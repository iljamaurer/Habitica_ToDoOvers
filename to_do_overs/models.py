# -*- coding: utf-8 -*-
"""Django Models - Habitica To Do Over tool
"""
from __future__ import unicode_literals
from builtins import str
from datetime import date
from django.db import models


class Users(models.Model):
    """Model for the users of the tool.

    Fields:
        username (str): Username from Habitica.
        user_id (str): User ID from Habitica.
        api_key (str): API token from Habitica.
    """

    user_id = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=255)
    username = models.CharField(max_length=255)

    def __str__(self):
        return str(self.pk) + ":" + str(self.user_id) + ":" + str(self.username)

    def __unicode__(self):
        return str(self.pk) + ":" + str(self.user_id) + ":" + str(self.username)


class Tags(models.Model):
    tag_id = models.CharField(max_length=255, unique=True)
    tag_text = models.CharField(max_length=255)
    tag_owner = models.ForeignKey(Users, on_delete=models.CASCADE)

    def __str__(self):
        return self.tag_text.decode("unicode_escape")

    def __unicode__(self):
        return self.tag_text.decode("unicode_escape")


class Tasks(models.Model):
    """Model for the tasks created by users.

    Fields:
        task_id (str): Task ID from Habitica.
        name (str): Name/title of task.
        notes (str): The notes/description of the task.
        priority (str): Difficulty of task.
        days (int): Number of days until task expires from the creation.
        owner (int/Foreign Key): The owner from the users model.
    """

    task_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    TRIVIAL = "0.1"
    EASY = "1.0"
    MEDIUM = "1.5"
    HARD = "2"
    PRIORITY_CHOICES = (
        (TRIVIAL, "Trivial"),
        (EASY, "Easy"),
        (MEDIUM, "Medium"),
        (HARD, "Hard"),
    )
    priority = models.CharField(
        max_length=3, choices=PRIORITY_CHOICES, blank=False, default=EASY
    )
    TYPE_CHOICES = (
        ("0", "Day"),
        ("1", "Week"),
        ("2", "Month"),
    )
    type = models.CharField(
        max_length=3, choices=TYPE_CHOICES, blank=False, default="0"
    )
    days = models.IntegerField(default=0)
    delay = models.PositiveIntegerField(default=0)

    DAYS_CHOICES = (
        ("0", "Monday"),
        ("1", "Tuesday"),
        ("2", "Wednesday"),
        ("3", "Thursday"),
        ("4", "Friday"),
        ("5", "Saturday"),
        ("6", "Sunday"),
    )
    weekday = models.CharField(
        max_length=3, choices=DAYS_CHOICES, blank=False, default="0"
    )
    monthday = models.CharField(
        max_length=2, choices=((str(x), str(x)) for x in range(1, 32)), default="0"
    )
    owner = models.ForeignKey(Users, on_delete=models.CASCADE)

    tags = models.ManyToManyField(Tags)

    def __str__(self):
        return str(self.pk) + ":" + str(self.name) + ":" + str(self.task_id)

    def __unicode__(self):
        return str(self.pk) + ":" + str(self.name) + ":" + str(self.task_id)
