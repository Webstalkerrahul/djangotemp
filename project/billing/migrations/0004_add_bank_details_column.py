from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('billing', 'previous_migration'),  # Replace with your last migration
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE billing_invoice 
            ADD COLUMN bank_details_id INTEGER REFERENCES company_bankdetail(id);
            CREATE INDEX billing_invoice_bank_details_id_idx ON billing_invoice (bank_details_id);
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS billing_invoice_bank_details_id_idx;
            ALTER TABLE billing_invoice DROP COLUMN bank_details_id;
            """
        ),
    ]