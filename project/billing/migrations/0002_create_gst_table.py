from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS billing_gst (
                id SERIAL PRIMARY KEY,
                cgst NUMERIC(10, 2),
                sgst NUMERIC(10, 2),
                total_gst NUMERIC(10, 2)
            );
            CREATE INDEX IF NOT EXISTS billing_gst_cgst_idx ON billing_gst (cgst);
            CREATE INDEX IF NOT EXISTS billing_gst_sgst_idx ON billing_gst (sgst);
            CREATE INDEX IF NOT EXISTS billing_gst_total_gst_idx ON billing_gst (total_gst);
            """,
            reverse_sql="DROP TABLE IF EXISTS billing_gst;"
        )
    ]