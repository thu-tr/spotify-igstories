#!/usr/bin/env python3
"""
publish_ig.py — Upload an image to S3 (private) and publish it as an Instagram Story.

Requirements:
  pip install boto3 requests

Config:
  credentials.json (example)
  {
    "instagram": {
      "user_id": "1784xxxxxxxxxxxx",
      "access_token": "EAAG..."
    },
    "aws": {
      "region": "us-east-1",
      "bucket": "my-ig-bot-bucket",
      "key": "stories/story.jpeg",
      "access_key_id": "AKIA...",
      "secret_access_key": "xxxxxxxx"
    },
    "meta": {
      "graph_base": "https://graph.instagram.com",
      "graph_version": "v19.0"
    },

    // Optional: skip S3 entirely and use this HTTPS URL directly
    "public_image_url": null
  }

Usage:
  python publish_ig.py --image story.jpeg --creds credentials.json
  python publish_ig.py --image story.jpeg --creds credentials.json --expires 600
  python publish_ig.py --image story.jpeg --creds credentials.json --stage-only
"""

import os
import sys
import json
import time
import mimetypes
import argparse
from typing import Optional

import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from botocore.config import Config

# --------------------------- helpers ---------------------------

def load_json(path: str) -> dict:
    if not os.path.isfile(path):
        sys.exit(f"[error] credentials file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def guess_content_type(path: str) -> str:
    ctype, _ = mimetypes.guess_type(path)
    return ctype or "image/jpeg"

def build_graph_base(creds: dict) -> str:
    meta = creds.get("meta", {}) or {}
    base = meta.get("graph_base", "https://graph.instagram.com")
    version = meta.get("graph_version", "v19.0")
    return f"{base.rstrip('/')}/{version}"

def retry_post(url: str, data: dict, max_attempts: int = 4, initial_delay: float = 1.0) -> requests.Response:
    delay = initial_delay
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.post(url, data=data, timeout=30)
            # Success
            if resp.status_code == 200:
                return resp
            # Retry on transient
            if resp.status_code in (429, 500, 502, 503, 504):
                print(f"[warn] POST {url} → {resp.status_code}; retrying in {delay:.1f}s "
                      f"(attempt {attempt}/{max_attempts})")
                time.sleep(delay)
                delay *= 2
                continue
            # Non-retryable -> return and let caller surface payload
            return resp
        except requests.RequestException as e:
            last_exc = e
            print(f"[warn] POST {url} raised {e}; retrying in {delay:.1f}s "
                  f"(attempt {attempt}/{max_attempts})")
            time.sleep(delay)
            delay *= 2
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed POST {url} after {max_attempts} attempts")


# --------------------------- S3 ---------------------------

def make_s3_client(aws_cfg: dict):
    region = aws_cfg.get("region")              # e.g. "us-east-2"
    access_key = aws_cfg.get("access_key_id")
    secret_key = aws_cfg.get("secret_access_key")

    cfg = Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"}      # -> https://<bucket>.s3.<region>.amazonaws.com
    )

    kwargs = {"config": cfg, "region_name": region}
    if access_key and secret_key:
        kwargs.update(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
    return boto3.client("s3", **kwargs)

def s3_upload_and_presign(image_path: str, aws_cfg: dict, expires: int = 300) -> str:
    s3 = make_s3_client(aws_cfg)
    bucket = aws_cfg["bucket"]
    key = aws_cfg.get("key", "stories/story.jpeg")

    ctype = guess_content_type(image_path)
    print(f"[info] Uploading {image_path} to s3://{bucket}/{key} (Content-Type: {ctype})")
    try:
        s3.upload_file(image_path, bucket, key, ExtraArgs={"ContentType": ctype})
    except (BotoCoreError, ClientError) as e:
        sys.exit(f"[error] S3 upload failed: {e}")

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires
        )
        print(f"[info] Generated presigned URL (expires in {expires}s)")
        return url
    except (BotoCoreError, ClientError) as e:
        sys.exit(f"[error] Failed to generate presigned URL: {e}")


# --------------------------- Instagram Graph API ---------------------------

def ig_stage_story(graph_base: str, ig_user_id: str, access_token: str, image_url: str) -> str:
    url = f"{graph_base}/{ig_user_id}/media"
    data = {
        "image_url": image_url,
        "media_type": "STORIES",
        "access_token": access_token
    }
    print(f"[info] Staging story…")
    resp = retry_post(url, data=data)
    if resp.status_code != 200:
        try:
            payload = resp.json()
        except Exception:
            payload = {"raw": resp.text}
        sys.exit(f"[error] Stage failed ({resp.status_code}): {json.dumps(payload, indent=2)}")

    creation_id = resp.json().get("id")
    if not creation_id:
        sys.exit(f"[error] Stage response missing 'id': {resp.text}")
    print(f"[ok] Staged. creation_id = {creation_id}")
    return creation_id

def ig_publish_story(graph_base: str, ig_user_id: str, access_token: str, creation_id: str) -> dict:
    url = f"{graph_base}/{ig_user_id}/media_publish"
    data = {
        "creation_id": creation_id,
        "access_token": access_token
    }
    print(f"[info] Publishing story…")
    resp = retry_post(url, data=data)
    if resp.status_code != 200:
        try:
            payload = resp.json()
        except Exception:
            payload = {"raw": resp.text}
        sys.exit(f"[error] Publish failed ({resp.status_code}): {json.dumps(payload, indent=2)}")

    payload = resp.json()
    print(f"[ok] Published: {json.dumps(payload)}")
    return payload


