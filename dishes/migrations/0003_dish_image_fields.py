from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dishes", "0002_dish_wikidata_id")]

    operations = [
        migrations.AddField(
            model_name="dish",
            name="image_url",
            field=models.URLField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="dish",
            name="image_caption",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="dish",
            name="image_credit",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="dish",
            name="image_license",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="dish",
            name="image_source_url",
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
