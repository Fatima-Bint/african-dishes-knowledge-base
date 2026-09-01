from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dishes", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dish",
            name="wikidata_id",
            field=models.CharField(
                blank=True,
                max_length=24,
                null=True,
                unique=True,
            ),
        ),
    ]
