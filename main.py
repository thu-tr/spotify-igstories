import argparse
import sys
import os
import time
import json
import spotify_pull
import compose_story
import publish_ig as pub

def load_json(path: str) -> dict:
    if not os.path.isfile(path):
        sys.exit(f"[error] credentials file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    tracks = spotify_pull.get_data()
    compose_story.generate_story(tracks)

    creds_path = "credentials.json"
    image_path = os.path.join("images", "story.jpeg")   # hardcoded
    expires = 300  # presigned URL TTL in seconds
    stage_only = False  # flip to True if you want to test staging only

    if not os.path.isfile(image_path):
        sys.exit(f"[error] Image not found: {image_path}")

    creds = load_json(creds_path)

    # Build Graph API base
    graph_base = pub.build_graph_base(creds)

    # Image URL (use public_image_url if provided, else S3 presigned)
    image_url = creds.get("public_image_url")
    if not image_url:
        aws_cfg = creds["aws"]
        image_url = pub.s3_upload_and_presign(image_path, aws_cfg, expires=expires)

    # Stage
    creation_id = pub.ig_stage_story(
        graph_base,
        creds["instagram"]["user_id"],
        creds["instagram"]["access_token"],
        image_url,
    )

    if stage_only:
        print(f"[info] Stage-only mode. Save creation_id: {creation_id}")
        return

    time.sleep(1.0)  # give IG time to fetch
    pub.ig_publish_story(graph_base, creds["instagram"]["user_id"], creds["instagram"]["access_token"], creation_id)


if __name__ == "__main__":
    main()
