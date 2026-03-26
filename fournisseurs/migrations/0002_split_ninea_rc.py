from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fournisseurs", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="fournisseur",
            old_name="ninea_rc",
            new_name="ninea",
        ),
        migrations.AddField(
            model_name="fournisseur",
            name="rc",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]

