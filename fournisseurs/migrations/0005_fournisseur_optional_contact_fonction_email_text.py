from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fournisseurs", "0004_userprofile"),
    ]

    operations = [
        migrations.AlterField(
            model_name="fournisseur",
            name="contact",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="fournisseur",
            name="fonction",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="fournisseur",
            name="email",
            field=models.CharField(blank=True, db_index=True, max_length=254),
        ),
    ]
