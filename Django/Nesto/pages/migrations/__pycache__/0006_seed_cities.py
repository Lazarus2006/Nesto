from django.db import migrations


def create_initial_cities(apps, schema_editor):
    City = apps.get_model("pages", "City")

    cities = [
        ("Indore", "indore"),
        ("Kota", "kota"),
        ("New Delhi", "new-delhi"),
    ]

    for name, slug in cities:
        City.objects.get_or_create(
            name=name,
            slug=slug,
        )


def remove_initial_cities(apps, schema_editor):
    City = apps.get_model("pages", "City")

    City.objects.filter(
        slug__in=["indore", "kota", "new-delhi"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0005_city"),
    ]

    operations = [
        migrations.RunPython(
            create_initial_cities,
            remove_initial_cities,
        ),
    ]