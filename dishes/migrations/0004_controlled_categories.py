from django.db import migrations
from django.utils.text import slugify


CATEGORIES = (
    "Staple",
    "Soup",
    "Stew",
    "Sauce or condiment",
    "Snack",
    "Beverage",
    "Dessert",
    "Porridge",
    "Side dish",
    "Other",
)


def create_categories(apps, schema_editor):
    DishCategory = apps.get_model("dishes", "DishCategory")
    for name in CATEGORIES:
        DishCategory.objects.get_or_create(
            name=name,
            defaults={"slug": slugify(name)},
        )


class Migration(migrations.Migration):
    dependencies = [("dishes", "0003_dish_image_fields")]
    operations = [migrations.RunPython(create_categories, migrations.RunPython.noop)]
