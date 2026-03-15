"""
============================================================================
Script 04: Launch Fine-Tuning Job on Amazon Bedrock
============================================================================
Launches a Supervised Fine-Tuning (SFT) job for Nova 2 Lite on Bedrock.

SFT vs RFT — What's the difference?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SFT (Supervised Fine-Tuning):
  ─────────────────────────────
  HOW:    You give the model PAIRS of (input → expected output)
  LIKE:   A student learning from a textbook with answers
  DATA:   "Question: X" → "Answer: Y" (labeled pairs)
  GOOD:   Teaching domain-specific knowledge (Ghomala' vocabulary)
  COST:   Lower, faster training
  
  RFT (Reinforcement Fine-Tuning):
  ─────────────────────────────────
  HOW:    The model GENERATES answers, then a GRADER scores them
  LIKE:   A student practicing with a teacher who gives feedback
  DATA:   Just prompts + a Lambda function that scores responses
  GOOD:   Improving quality AFTER SFT (polishing responses)
  COST:   Higher, longer training, but +66% accuracy improvement
  
  OUR STRATEGY:
  1. First: SFT with our MAFAND-MT + dictionary data (teach knowledge)
  2. Then:  RFT on top of SFT model (polish quality) — if time allows

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Prerequisites:
  - AWS CLI configured with Bedrock access
  - Training data uploaded to S3 (run 03_upload_to_s3.py first)
  - IAM role with Bedrock + S3 permissions

Usage:
  python 04_launch_fine_tuning.py --mode sft     # Supervised Fine-Tuning
  python 04_launch_fine_tuning.py --mode rft     # Reinforcement Fine-Tuning
============================================================================
"""

import boto3
import json
import time
import argparse
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================
AWS_REGION = "us-east-1"
BUCKET_NAME = "nam-sa-ghomala-training"
S3_PREFIX = "fine-tuning/ghomala-v1"

# S3 URIs (from script 03)
TRAIN_S3_URI = f"s3://{BUCKET_NAME}/{S3_PREFIX}/train.jsonl"
OUTPUT_S3_URI = f"s3://{BUCKET_NAME}/output/ghomala-model-v1"

# Model identifiers
BASE_MODEL_ID = "amazon.nova-lite-v1:0"  # Nova Lite (Nova 1.0)
# For Nova 2 Lite, use: "amazon.nova-2-lite-v1:0:256k"
# Check availability in your region - Nova 2 may require specific access

# IAM Role ARN — REPLACE WITH YOUR ROLE ARN
# You need to create this role with Bedrock + S3 permissions
# See: docs/fine-tuning/iam_setup.md
ROLE_ARN = "arn:aws:iam::YOUR_ACCOUNT_ID:role/BedrockFineTuningRole"


# ============================================================================
# SFT: Supervised Fine-Tuning
# ============================================================================
def launch_sft_job(bedrock_client):
    """
    Launch a Supervised Fine-Tuning job on Amazon Bedrock.
    
    What happens behind the scenes:
    1. Bedrock reads your train.jsonl from S3
    2. For each conversation pair, it adjusts the model weights
       so the model learns to respond like the assistant in your data
    3. After N epochs (passes through the data), it saves the tuned model
    4. You get a custom model ID to use for inference
    
    Typical duration: 30 minutes to 2 hours depending on data size.
    Cost: ~$5-15 for our dataset size.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"nam-sa-ghomala-sft-{timestamp}"
    model_name = f"nam-sa-ghomala-v1-{timestamp}"
    
    print(f"\nLaunching SFT Job: {job_name}")
    print(f"   Base model:  {BASE_MODEL_ID}")
    print(f"   Train data:  {TRAIN_S3_URI}")
    print(f"   Output:      {OUTPUT_S3_URI}")
    
    try:
        response = bedrock_client.create_model_customization_job(
            jobName=job_name,
            customModelName=model_name,
            roleArn=ROLE_ARN,
            baseModelIdentifier=BASE_MODEL_ID,
            customizationType="FINE_TUNING",
            trainingDataConfig={
                "s3Uri": TRAIN_S3_URI
            },
            outputDataConfig={
                "s3Uri": OUTPUT_S3_URI
            },
            hyperParameters={
                "epochCount": "3",         # Number of passes through data
                "batchSize": "4",          # Samples per training step
                "learningRate": "0.00001", # How fast the model learns
            }
        )
        
        job_arn = response["jobArn"]
        print(f"\n   ✅ SFT Job created!")
        print(f"   Job ARN: {job_arn}")
        print(f"   Model name: {model_name}")
        
        return job_arn, model_name
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        print(f"\n   Common fixes:")
        print(f"   1. Check IAM role ARN is correct")
        print(f"   2. Ensure Bedrock model access is enabled in your region")
        print(f"   3. Verify S3 bucket permissions")
        print(f"   4. Check if Nova 2 Lite requires model access request")
        raise


# ============================================================================
# RFT: Reinforcement Fine-Tuning
# ============================================================================
def launch_rft_job(bedrock_client, base_model=None):
    """
    Launch a Reinforcement Fine-Tuning job on Amazon Bedrock.
    
    RFT is different from SFT:
    - SFT: "Here's the right answer, learn it" (imitation)
    - RFT: "Generate an answer, I'll tell you if it's good" (feedback loop)
    
    For RFT, you need a GRADER — a Lambda function that scores responses.
    Our grader checks:
    1. Does the response contain Ghomala' words?
    2. Is the translation accurate?
    3. Does it include cultural context?
    
    ⚠️ IMPORTANT: You need to deploy the grader Lambda first!
    See: backend/rft_grader/README.md
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"nam-sa-ghomala-rft-{timestamp}"
    model_name = f"nam-sa-ghomala-rft-v1-{timestamp}"
    
    # Use the SFT model as base if available, otherwise use default
    model_id = base_model or "amazon.nova-2-lite-v1:0:256k"
    
    # Lambda ARN for the grader function — REPLACE WITH YOUR LAMBDA ARN
    grader_lambda_arn = "arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ghomala-rft-grader"
    
    print(f"\nLaunching RFT Job: {job_name}")
    print(f"   Base model:     {model_id}")
    print(f"   Grader Lambda:  {grader_lambda_arn}")
    
    try:
        response = bedrock_client.create_model_customization_job(
            jobName=job_name,
            customModelName=model_name,
            roleArn=ROLE_ARN,
            baseModelIdentifier=model_id,
            customizationType="REINFORCEMENT_FINE_TUNING",
            trainingDataConfig={
                "s3Uri": TRAIN_S3_URI
            },
            outputDataConfig={
                "s3Uri": OUTPUT_S3_URI
            },
            customizationConfig={
                "rftConfig": {
                    "graderConfig": {
                        "lambdaGrader": {
                            "lambdaArn": grader_lambda_arn
                        }
                    },
                    "hyperParameters": {
                        "batchSize": 16,
                        "epochCount": 2,
                        "evalInterval": 10,
                        "inferenceMaxTokens": 2048,
                        "learningRate": 0.00001,
                        "maxPromptLength": 1024,
                        "reasoningEffort": "medium",
                        "trainingSamplePerPrompt": 4
                    }
                }
            }
        )
        
        job_arn = response["jobArn"]
        print(f"\n   ✅ RFT Job created!")
        print(f"   Job ARN: {job_arn}")
        
        return job_arn, model_name
        
    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        raise


# ============================================================================
# Monitor job status
# ============================================================================
def monitor_job(bedrock_client, job_arn):
    """Poll the fine-tuning job status until completion."""
    print(f"\nMonitoring job...")
    print(f"   (This can take 30 min to 2 hours. You can also check in the AWS Console)")
    print(f"   AWS Console: https://console.aws.amazon.com/bedrock/home#/custom-models\n")
    
    while True:
        response = bedrock_client.get_model_customization_job(jobIdentifier=job_arn)
        status = response["status"]
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"   [{timestamp}] Status: {status}")
        
        if status == "Completed":
            print(f"\n   Fine-tuning COMPLETE!")
            print(f"   Custom model ARN: {response.get('outputModelArn', 'N/A')}")
            print(f"   Custom model name: {response.get('outputModelName', 'N/A')}")
            return response
        elif status in ["Failed", "Stopped"]:
            print(f"\n   ❌ Job {status}!")
            failure_msg = response.get("failureMessage", "No details")
            print(f"   Reason: {failure_msg}")
            return response
        
        # Wait 60 seconds before checking again
        time.sleep(60)


# ============================================================================
# Test the fine-tuned model
# ============================================================================
def test_model(model_id):
    """
    Test the fine-tuned model with a few Ghomala' prompts.
    """
    print(f"\nTesting fine-tuned model: {model_id}")
    
    bedrock_runtime = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )
    
    test_prompts = [
        "Comment dit-on 'bonjour' en Ghomala' ?",
        "Traduis en Ghomala' : Le marché est ouvert aujourd'hui",
        "Parle-moi de la culture Bamiléké",
        "How do you say 'thank you' in Ghomala'?",
    ]
    
    for prompt in test_prompts:
        print(f"\n   USER: {prompt}")
        
        try:
            response = bedrock_runtime.converse(
                modelId=model_id,
                messages=[
                    {"role": "user", "content": [{"text": prompt}]}
                ],
                system=[{"text": "Tu es NAM SA', un agent de préservation du Ghomala'."}]
            )
            
            answer = response["output"]["message"]["content"][0]["text"]
            print(f"   ASST: {answer[:150]}...")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n   ✅ Testing complete!")


# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Launch Bedrock fine-tuning")
    parser.add_argument(
        "--mode", 
        choices=["sft", "rft", "test"],
        default="sft",
        help="sft = Supervised Fine-Tuning, rft = Reinforcement, test = Test model"
    )
    parser.add_argument("--model-id", help="Model ID for testing", default=None)
    parser.add_argument("--monitor", action="store_true", help="Wait for job completion")
    
    args = parser.parse_args()
    
    print("NAM SA' — Bedrock Fine-Tuning Pipeline")
    print("=" * 60)
    
    bedrock = boto3.client("bedrock", region_name=AWS_REGION)
    
    if args.mode == "sft":
        print("\n   Mode: Supervised Fine-Tuning (SFT)")
        print("   The model learns from example conversations")
        job_arn, model_name = launch_sft_job(bedrock)
        
        if args.monitor:
            monitor_job(bedrock, job_arn)
    
    elif args.mode == "rft":
        print("\n   Mode: Reinforcement Fine-Tuning (RFT)")
        print("   The model generates, a grader scores, and it improves")
        job_arn, model_name = launch_rft_job(bedrock)
        
        if args.monitor:
            monitor_job(bedrock, job_arn)
    
    elif args.mode == "test":
        if not args.model_id:
            print("❌ Please provide --model-id for testing")
            return
        test_model(args.model_id)
    
    print("\n" + "=" * 60)
    print("USEFUL COMMANDS:")
    print("=" * 60)
    print("   Monitor in console:")
    print("   → https://console.aws.amazon.com/bedrock/home#/custom-models")
    print("")
    print("   Monitor via CLI:")
    print("   → aws bedrock get-model-customization-job --job-identifier JOB_ARN")
    print("")
    print("   List custom models:")
    print("   → aws bedrock list-custom-models")
    print("")
    print("   Test model:")
    print("   → python 04_launch_fine_tuning.py --mode test --model-id YOUR_MODEL_ID")
    print("=" * 60)


if __name__ == "__main__":
    main()
