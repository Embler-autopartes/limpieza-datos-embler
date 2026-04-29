"""
Sube los 12 CSVs de final-con-imagenes/ al bucket R2 embler-productos
bajo el prefijo csvs/.
"""
import boto3
import os
import sys
from botocore.config import Config

BUCKET = "embler-productos"
PREFIX = "csvs"
LOCAL_DIR = "final-con-imagenes"
PUBLIC_BASE = "https://pub-7f4859912bd64708bc328970b6821976.r2.dev"


def main():
    s3 = boto3.client(
        "s3",
        endpoint_url="https://245a6740c0624e4eacaf1c8fc3cf4840.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )

    files = sorted(f for f in os.listdir(LOCAL_DIR) if f.endswith(".csv"))
    print(f"Subiendo {len(files)} archivos a {BUCKET}/{PREFIX}/...")
    print()

    for fname in files:
        local_path = os.path.join(LOCAL_DIR, fname)
        key = f"{PREFIX}/{fname}"
        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        sys.stdout.write(f"  {fname:<30} ({size_mb:6.1f} MB) ... ")
        sys.stdout.flush()
        s3.upload_file(
            local_path,
            BUCKET,
            key,
            ExtraArgs={"ContentType": "text/csv; charset=utf-8"},
        )
        print("OK")
        print(f"     {PUBLIC_BASE}/{key}")
    print(f"\nTodos los CSVs subidos.")


if __name__ == "__main__":
    main()
