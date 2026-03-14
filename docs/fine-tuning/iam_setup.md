# IAM Setup for Bedrock Fine-Tuning

## Step 1: Create the IAM Role

Go to AWS Console → IAM → Roles → Create role

**Trust Policy** (allows Bedrock to assume this role):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

## Step 2: Attach Permissions

Create an inline policy named `BedrockFineTuningAccess`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::nam-sa-ghomala-training",
        "arn:aws:s3:::nam-sa-ghomala-training/*"
      ]
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:CreateModelCustomizationJob",
        "bedrock:GetModelCustomizationJob",
        "bedrock:ListCustomModels",
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 3: Note the Role ARN

Copy the ARN (format: `arn:aws:iam::ACCOUNT_ID:role/BedrockFineTuningRole`)
and paste it in `04_launch_fine_tuning.py` → `ROLE_ARN` variable.

## Step 4: Enable Model Access in Bedrock

1. Go to AWS Console → Amazon Bedrock → Model access
2. Click "Manage model access"
3. Enable: Amazon Nova Lite, Amazon Nova 2 Lite
4. Wait for approval (usually instant)
