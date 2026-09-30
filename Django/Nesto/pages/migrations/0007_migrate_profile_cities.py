from django.db import migrations


def migrate_profile_cities(apps, schema_editor):
    City = apps.get_model("pages", "City")
    Profile = apps.get_model("pages", "Profile")

    # Create the initial Nesto cities
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

    # Convert existing Profile.city strings
    # into Profile.city_new foreign keys
    for profile in Profile.objects.all():

        if not profile.city:
            continue

        city = City.objects.filter(
            name__iexact=profile.city.strip()
        ).first()

        if city:
            profile.city_new = city
            profile.save(update_fields=["city_new"])


def reverse_migrate_profile_cities(apps, schema_editor):
    Profile = apps.get_model("pages", "Profile")

    for profile in Profile.objects.select_related("city_new"):
        if profile.city_new:
            profile.city = profile.city_new.name
            profile.save(update_fields=["city"])


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0006_profile_city_new"),
    ]

    operations = [
        migrations.RunPython(
            migrate_profile_cities,
            reverse_migrate_profile_cities,
        ),
    ]