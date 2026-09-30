from django.db import migrations, models
import django.db.models.deletion


def migrate_post_cities(apps, schema_editor):
    Post = apps.get_model("pages", "Post")
    Profile = apps.get_model("pages", "Profile")

    for post in Post.objects.select_related("author"):
        if not post.author:
            continue

        try:
            profile = post.author.profile
        except Profile.DoesNotExist:
            continue

        if profile.city_new:
            post.city_id = profile.city_new_id
            post.save(update_fields=["city"])


def migrate_profile_cities(apps, schema_editor):
    City = apps.get_model("pages", "City")
    Profile = apps.get_model("pages", "Profile")

    for profile in Profile.objects.all():

        old_city = profile.city_old

        if not old_city:
            continue

        city = City.objects.filter(
            name__iexact=old_city.strip()
        ).first()

        if city:
            profile.city_id = city.id
            profile.save(update_fields=["city"])


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0007_migrate_profile_cities"),
    ]

    operations = [

        # 1. Add Post.city as a completely new column.
        migrations.AddField(
            model_name="post",
            name="city",
            field=models.ForeignKey(
                "pages.city",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="posts",
                null=True,
                blank=True,
            ),
        ),

        # 2. Copy existing post cities.
        migrations.RunPython(
            migrate_post_cities,
            migrations.RunPython.noop,
        ),

        # 3. Remove the temporary Profile.city_new field.
        migrations.RemoveField(
            model_name="profile",
            name="city_new",
        ),

        # 4. Rename the OLD text field.
        migrations.RenameField(
            model_name="profile",
            old_name="city",
            new_name="city_old",
        ),

        # 5. Create a brand-new Profile.city ForeignKey.
        migrations.AddField(
            model_name="profile",
            name="city",
            field=models.ForeignKey(
                "pages.city",
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="residents",
                null=True,
                blank=True,
            ),
        ),

        # 6. Convert the old text values into City IDs.
        migrations.RunPython(
            migrate_profile_cities,
            migrations.RunPython.noop,
        ),

        # 7. Delete the old text column.
        migrations.RemoveField(
            model_name="profile",
            name="city_old",
        ),
    ]