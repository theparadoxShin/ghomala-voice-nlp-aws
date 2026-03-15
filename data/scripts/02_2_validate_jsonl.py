"""
============================================================================
Script 02_2: Validate JSONL files for Nova Lite 2 fine-tuning
============================================================================
Validates that train.jsonl and val.jsonl conform to Amazon Bedrock's
Nova converse format before uploading to S3.

Based on the official AWS validation script:
  aws-samples/amazon-bedrock-samples/custom-models/bedrock-fine-tuning/
  nova/understanding/dataset_validation

Checks:
  - Valid JSONL (each line is valid JSON)
  - Correct schema: schemaVersion, system, messages
  - Role alternation: user → assistant → user → assistant ...
  - Last message has assistant role
  - Minimum 2 messages per sample
  - Sample count within bounds (8 - 20,000 for Nova Lite)
  - No empty text content

Usage:
  python 02_2_validate_jsonl.py
  python 02_2_validate_jsonl.py --file train.jsonl
  python 02_2_validate_jsonl.py --file val.jsonl --model lite
============================================================================
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ValidationError, ValidationInfo, field_validator, model_validator


# ============================================================================
# CONFIGURATION
# ============================================================================
PROCESSED_DIR = Path(__file__).parent.parent / "processed"

IMAGE_FORMATS = ["jpeg", "png", "gif", "webp"]
VIDEO_FORMATS = ["mov", "mkv", "mp4", "webm"]
MAX_NUM_IMAGES = 10
MODEL_TO_NUM_SAMPLES_MAP = {"micro": (8, 20000), "lite": (8, 20000), "pro": (8, 20000)}


# ============================================================================
# ROLES
# ============================================================================
class ConverseRoles:
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


CONVERSE_ROLES_WITHOUT_SYSTEM = [ConverseRoles.USER, ConverseRoles.ASSISTANT]


# ============================================================================
# EXCEPTIONS
# ============================================================================
class NovaClientError(ValueError):
    def __init__(self, message):
        super().__init__(message)


class NovaInternalError(Exception):
    pass


# ============================================================================
# FILE LOADING
# ============================================================================
def check_jsonl_file(file_path):
    if not file_path.endswith(".jsonl"):
        raise NovaClientError(f"File is not jsonl: {file_path}")


def load_jsonl_data(file_path: str):
    try:
        check_jsonl_file(file_path)
        data = []
        with open(file_path, "r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, 1):
                try:
                    parsed_line = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(
                        f"Line {line_number}: Invalid JSON syntax - {str(e)}\nLine content: {line}"
                    )
                data.append(parsed_line)
        return data
    except NovaClientError:
        raise
    except Exception as e:
        raise NovaClientError(f"Error loading data from {file_path}: {str(e)}")


# ============================================================================
# PYDANTIC MODELS (from AWS official validator)
# ============================================================================
class S3Location(BaseModel):
    uri: str

    @field_validator("uri")
    def validate_format(cls, uri):
        if not uri.startswith("s3://"):
            raise ValueError("Invalid S3 URI, must start with 's3://'")
        is_valid_path(uri.replace("s3://", ""))
        return uri


class Source(BaseModel):
    s3Location: S3Location


class ImageContent(BaseModel):
    format: str
    source: Source

    @field_validator("format")
    def validate_format(cls, image_format):
        if image_format.lower() not in IMAGE_FORMATS:
            raise ValueError(f"Invalid image format, supported formats are {IMAGE_FORMATS}")
        return image_format


class VideoContent(BaseModel):
    format: str
    source: Source

    @field_validator("format")
    def validate_format(cls, video_format):
        if video_format.lower() not in VIDEO_FORMATS:
            raise ValueError(f"Invalid video format, supported formats are {VIDEO_FORMATS}")
        return video_format


class ContentItem(BaseModel):
    text: Optional[str] = None
    image: Optional[ImageContent] = None
    video: Optional[VideoContent] = None

    @model_validator(mode="after")
    def validate_model_fields(cls, values):
        if not any(getattr(values, field) is not None for field in cls.model_fields.keys()):
            raise ValueError(
                f"Invalid content, at least one of {list(cls.model_fields.keys())} must be provided"
            )
        return values


class Message(BaseModel):
    role: str
    content: List[ContentItem]

    @field_validator("role")
    def validate_role(cls, role):
        if role.lower() not in CONVERSE_ROLES_WITHOUT_SYSTEM:
            raise ValueError(
                f"Invalid value for role, valid values are {CONVERSE_ROLES_WITHOUT_SYSTEM}"
            )
        return role

    @model_validator(mode="after")
    def validate_content_rules(cls, values):
        content_items = values.content
        has_video = any(item.video is not None for item in content_items)
        has_image = any(item.image is not None for item in content_items)

        if has_image or has_video:
            if values.role.lower() == "assistant":
                raise ValueError(
                    "Invalid content, image/video cannot be included when role is 'assistant'"
                )
        return values

    @field_validator("content")
    def validate_content(cls, content, info: ValidationInfo):
        has_text = any(item.text is not None for item in content)
        has_video = any(item.video is not None for item in content)
        has_image = any(item.image is not None for item in content)

        total_text_length = sum(len(item.text) for item in content if item.text is not None)
        if has_text and not (has_image or has_video) and total_text_length == 0:
            raise ValueError("Invalid content, empty text content")

        if not info.context:
            raise NovaInternalError("context is not set for validating model type")

        is_micro_model = "micro" in info.context["model_name"]
        if is_micro_model and (has_image or has_video):
            raise ValueError(
                "Invalid content, image/video samples not supported by Nova Micro model"
            )

        if sum(1 for item in content if item.video is not None) > 1:
            raise ValueError("Only one video is allowed per sample")

        if has_video and has_image:
            raise ValueError(
                "'content' list cannot contain both video items and image items for a given sample"
            )

        num_images = sum(1 for item in content if item.image is not None)
        if num_images > MAX_NUM_IMAGES:
            raise ValueError(
                f"Invalid content, number of images {num_images} exceed maximum allowed limit of {MAX_NUM_IMAGES}"
            )

        return content


class SystemMessage(BaseModel):
    text: str


class ConverseDatasetSample(BaseModel):
    schemaVersion: Optional[str] = None
    system: Optional[List[SystemMessage]] = None
    messages: List[Message]

    @field_validator("messages")
    def validate_data_sample_rules(cls, messages):
        check_roles_order(messages)
        return messages


# ============================================================================
# VALIDATION HELPERS
# ============================================================================
def check_roles_order(messages):
    if len(messages) < 2:
        raise ValueError(
            f"Invalid messages, both {CONVERSE_ROLES_WITHOUT_SYSTEM} are needed in sample"
        )

    for i, message in enumerate(messages):
        if i % 2 == 0 and message.role != ConverseRoles.USER:
            raise ValueError(
                f"Invalid messages, expected {ConverseRoles.USER} role but found {message.role}"
            )
        elif i % 2 == 1 and message.role != ConverseRoles.ASSISTANT:
            raise ValueError(
                f"Invalid messages, expected {ConverseRoles.ASSISTANT} role but found {message.role}"
            )

    if messages[-1].role != ConverseRoles.ASSISTANT:
        raise ValueError(f"Invalid messages, last turn should have {ConverseRoles.ASSISTANT} role")


def is_valid_path(file_path):
    pattern = r"^[\w\-/\.]+$"
    if not re.match(pattern, file_path):
        raise ValueError(
            "Invalid characters in 'uri'. Only alphanumeric, underscores, hyphens, slashes, and dots are allowed"
        )


def get_data_record_bounds(model_name: str):
    return MODEL_TO_NUM_SAMPLES_MAP[model_name]


def validate_data_record_bounds(num_samples: int, model_name: str):
    data_record_bounds = get_data_record_bounds(model_name)
    if num_samples < data_record_bounds[0] or num_samples > data_record_bounds[1]:
        raise NovaClientError(
            f"Number of samples {num_samples} out of bounds between "
            f"{data_record_bounds[0]} and {data_record_bounds[1]} for {model_name}"
        )


# ============================================================================
# MAIN VALIDATION
# ============================================================================
def validate_converse_dataset(file_path: str, model_name: str):
    """Validates the entire conversation dataset against Nova format requirements."""
    print(f"\n🔍 Validating: {file_path}")
    print(f"   Model target: Nova {model_name}")

    samples = load_jsonl_data(file_path)
    num_samples = len(samples)
    print(f"   Total samples: {num_samples}")

    validate_data_record_bounds(num_samples, model_name)

    error_message = ""
    failed_samples_id_list = []

    for i, sample in enumerate(samples):
        try:
            ConverseDatasetSample.model_validate(sample, context={"model_name": model_name})
        except ValidationError as e:
            failed_samples_id_list.append(i)
            error_message += f"Sample {i} - "
            for err in e.errors():
                err["msg"] = err["msg"].replace("Value error, ", "")
                sample_error_message = f"{err['loc']}: {err['msg']} (type={err['type']}). "
                error_message += sample_error_message
        except Exception as e:
            raise NovaInternalError(f"Error occurred: {e}")

    if error_message:
        prefix_str = "Problematic samples: "

        if len(failed_samples_id_list) > 3:
            first_sample_id = failed_samples_id_list[0]
            second_sample_id = failed_samples_id_list[1]
            last_sample_id = failed_samples_id_list[-1]
            failed_samples_str = f"[{first_sample_id}, {second_sample_id}, ...{last_sample_id}]. "
        else:
            failed_samples_str = f"{failed_samples_id_list}. "

        final_err_msg = prefix_str + failed_samples_str + error_message
        raise NovaClientError(final_err_msg)
    else:
        print(f"   ✅ Validation passed — all {num_samples} samples are valid for Nova {model_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSONL files for Amazon Bedrock Nova fine-tuning",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Specific JSONL file to validate. If omitted, validates both train.jsonl and val.jsonl",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        choices=["micro", "lite", "pro"],
        default="lite",
        help="Target Nova model (default: lite)",
    )

    args = parser.parse_args()

    print("🌍 NAM SA' — JSONL Validation for Bedrock Nova Fine-Tuning")
    print("=" * 60)

    files_to_validate = []

    if args.file:
        files_to_validate.append(args.file)
    else:
        train_path = PROCESSED_DIR / "train.jsonl"
        val_path = PROCESSED_DIR / "val.jsonl"

        if train_path.exists():
            files_to_validate.append(str(train_path))
        else:
            print(f"   ⚠️  {train_path} not found")

        if val_path.exists():
            files_to_validate.append(str(val_path))
        else:
            print(f"   ⚠️  {val_path} not found")

    if not files_to_validate:
        print("❌ No files to validate. Run 02_transform_to_jsonl.py first!")
        return

    all_passed = True

    for file_path in files_to_validate:
        try:
            validate_converse_dataset(file_path, args.model)
        except NovaClientError as e:
            print(f"\n   ❌ VALIDATION FAILED: {e}")
            all_passed = False
        except Exception as e:
            print(f"\n   ❌ UNEXPECTED ERROR: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL FILES PASSED VALIDATION")
        print(f"   Ready for upload to S3 → python 03_upload_to_s3.py")
    else:
        print("❌ SOME FILES FAILED VALIDATION")
        print("   Fix the errors above and re-run 02_transform_to_jsonl.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
