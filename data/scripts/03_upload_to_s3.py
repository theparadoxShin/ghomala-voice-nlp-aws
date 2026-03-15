"""
============================================================================
Script 03: Upload training data to Amazon S3
============================================================================
Uploads train.jsonl and val.jsonl to your S3 bucket for Bedrock fine-tuning.

Prerequisites:
  - AWS CLI configured: `aws configure`
  - S3 bucket created (script creates it if needed)

Usage:
  python 03_upload_to_s3.py
============================================================================
"""

import boto3
import json
import os
from pathlib import Path
from botocore.exceptions import ClientError

# ============================================================================
# CONFIGURATION — Modify these values for your AWS account
# ============================================================================
AWS_REGION = "us-east-1"  # Bedrock fine-tuning is available here
BUCKET_NAME = "nam-sa-ghomala-training"  # Change to your unique bucket name
S3_PREFIX = "fine-tuning/ghomala-v1"      # Folder inside the bucket

# Local paths
PROCESSED_DIR = Path(__file__).parent.parent / "processed"
TRAIN_FILE = PROCESSED_DIR / "train.jsonl"
VAL_FILE = PROCESSED_DIR / "val.jsonl"


def create_bucket_if_needed(s3_client, bucket_name, region):
    """Create the S3 bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"   ✅ Bucket '{bucket_name}' exists")
    except ClientError:
        print(f"   📦 Creating bucket '{bucket_name}' in {region}...")
        if region == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"   ✅ Bucket created!")


def upload_file(s3_client, local_path, bucket, s3_key):
    """Upload a single file to S3 with progress info."""
    file_size = local_path.stat().st_size / 1024
    print(f"   ⬆️  Uploading {local_path.name} ({file_size:.1f} KB) → s3://{bucket}/{s3_key}")
    
    s3_client.upload_file(
        str(local_path), 
        bucket, 
        s3_key,
        ExtraArgs={"ContentType": "application/jsonl"}
    )
    print(f"   ✅ Uploaded!")
    return f"s3://{bucket}/{s3_key}"


def validate_jsonl(file_path):
    """Quick validation that the JSONL is well-formed."""
    print(f"   🔍 Validating {file_path.name}...")
    line_count = 0
    errors = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                obj = json.loads(line.strip())
                # Check required Bedrock fields
                assert "schemaVersion" in obj, "Missing schemaVersion"
                assert "messages" in obj, "Missing messages"
                assert len(obj["messages"]) >= 2, "Need at least user + assistant"
                assert obj["messages"][0]["role"] == "user", "First message must be user"
                assert obj["messages"][-1]["role"] == "assistant", "Last message must be assistant"
                line_count += 1
            except Exception as e:
                print(f"      ❌ Line {i}: {e}")
                errors += 1
    
    if errors == 0:
        print(f"   ✅ Validation passed: {line_count} valid conversations")
    else:
        print(f"   ⚠️  {errors} errors found out of {line_count + errors} lines")
    
    return errors == 0


def main():
    print("🌍 NAM SA' — S3 Upload Pipeline")
    print("=" * 60)
    
    # Check files exist
    if not TRAIN_FILE.exists():
        print(f"❌ {TRAIN_FILE} not found. Run 02_transform_to_jsonl.py first!")
        return
    
    # Validate before uploading
    print("\n📋 Validating JSONL files...")
    if not validate_jsonl(TRAIN_FILE):
        print("❌ Training file has errors. Fix them before uploading.")
        return
    
    if VAL_FILE.exists():
        validate_jsonl(VAL_FILE)
    
    # Initialize S3
    print("\n📡 Connecting to AWS S3...")
    s3 = boto3.client("s3", region_name=AWS_REGION)
    
    # Create bucket
    create_bucket_if_needed(s3, BUCKET_NAME, AWS_REGION)
    
    # Upload files
    print("\n⬆️  Uploading files...")
    train_s3_uri = upload_file(
        s3, TRAIN_FILE, BUCKET_NAME, 
        f"{S3_PREFIX}/train.jsonl"
    )
    
    val_s3_uri = None
    if VAL_FILE.exists():
        val_s3_uri = upload_file(
            s3, VAL_FILE, BUCKET_NAME,
            f"{S3_PREFIX}/val.jsonl"
        )
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 UPLOAD SUMMARY")
    print("=" * 60)
    print(f"   Bucket:    {BUCKET_NAME}")
    print(f"   Region:    {AWS_REGION}")
    print(f"   Train URI: {train_s3_uri}")
    if val_s3_uri:
        print(f"   Val URI:   {val_s3_uri}")
    
    print(f"\n   📋 Save these URIs for the fine-tuning step:")
    print(f"      TRAIN_S3_URI = \"{train_s3_uri}\"")
    if val_s3_uri:
        print(f"      VAL_S3_URI   = \"{val_s3_uri}\"")
    
    print(f"\n   ➡️  Next step: python 04_launch_fine_tuning.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
