# Generated migration to add 'organisasi' field and update foto upload (manual)
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0008_siswa_is_osis'),
    ]

    operations = [
        migrations.AddField(
            model_name='siswa',
            name='organisasi',
            field=models.CharField(default='bukan_anggota', max_length=20, choices=[('bukan_anggota', 'Bukan Anggota'), ('osis', 'OSIS'), ('mpk', 'MPK')]),
        ),
    ]