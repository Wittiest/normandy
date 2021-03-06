# Generated by Django 2.0.6 on 2018-06-22 19:04

from django.db import migrations
from django.db.models import F


def username_to_email(apps, schema_editor):
    """Sets the email for users that don't have an email."""
    User = apps.get_model("auth", "User")
    users = User.objects.filter(email="", username__contains="@")
    users.update(email=F("username"))


class Migration(migrations.Migration):

    dependencies = [("base", "0001_copy_email_to_username")]

    operations = [migrations.RunPython(username_to_email, migrations.RunPython.noop)]
