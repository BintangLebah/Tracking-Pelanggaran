from django.db import migrations, models


def copy_wali_kelas(apps, schema_editor):
    Kelas = apps.get_model('academics', 'Kelas')
    User = apps.get_model('accounts', 'User')
    # Loop through existing kelas and copy the related user's name into the new text field
    for k in Kelas.objects.all():
        uid = getattr(k, 'wali_kelas_id', None)
        name = None
        if uid:
            try:
                user = User.objects.get(pk=uid)
                full = (user.get_full_name() or user.username).strip()
                if full:
                    name = full
            except User.DoesNotExist:
                name = None
        if name:
            k.wali_kelas_text = name
            k.save(update_fields=['wali_kelas_text'])


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_alter_kelas_tingkat'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Add a temporary text field to hold the wali_kelas name
        migrations.AddField(
            model_name='kelas',
            name='wali_kelas_text',
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
        # Copy data from the existing FK column (wali_kelas_id) into wali_kelas_text
        migrations.RunPython(copy_wali_kelas, reverse_code=migrations.RunPython.noop),
        # Remove the old FK field
        migrations.RemoveField(
            model_name='kelas',
            name='wali_kelas',
        ),
        # Rename the temp field to the final field name
        migrations.RenameField(
            model_name='kelas',
            old_name='wali_kelas_text',
            new_name='wali_kelas',
        ),
    ]
