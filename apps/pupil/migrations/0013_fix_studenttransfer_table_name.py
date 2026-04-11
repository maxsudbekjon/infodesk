"""
Fix mismatch between model class name and DB table.

After migration 0011, the DB table is 'pupil_studnettransfer' but the model
class was renamed back to StudentTransfer in code without a migration.
This migration:
  1. Pins the explicit db_table so RenameModel won't touch the DB.
  2. Renames the migration-state model from StudnetTransfer → StudentTransfer.

No SQL is executed against the database.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pupil', '0012_merge_20260409_1313'),
    ]

    operations = [
        # Step 1: record the explicit table name in migration state.
        # This prevents the subsequent RenameModel from issuing an
        # ALTER TABLE statement.
        migrations.AlterModelTable(
            name='studnettransfer',
            table='pupil_studnettransfer',
        ),
        # Step 2: rename the migration-state model to match the code.
        # Because db_table is now explicit, Django won't touch the DB table.
        migrations.RenameModel(
            old_name='StudnetTransfer',
            new_name='StudentTransfer',
        ),
    ]
