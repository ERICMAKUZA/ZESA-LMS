from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0008_qualification_configuration"),
    ]

    operations = [
        migrations.AddField(
            model_name="courseschedule",
            name="payment_due_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
