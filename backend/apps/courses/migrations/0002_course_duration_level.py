from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='duration_days',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='course',
            name='level',
            field=models.CharField(
                blank=True,
                choices=[
                    ('BEGINNER', 'Beginner'),
                    ('INTERMEDIATE', 'Intermediate'),
                    ('ADVANCED', 'Advanced'),
                    ('ALL_LEVELS', 'All Levels'),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
