"""Render the immutable image and apply both manifests without editing source."""
import argparse
from pathlib import Path
import re
import subprocess


def render(image):
    if not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*/[a-z0-9]+(?:[._-][a-z0-9]+)*:[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}", image):
        raise ValueError("Use a Docker Hub image USERNAME/REPOSITORY:IMMUTABLE_TAG")
    if image.rsplit(":", 1)[1] in {"latest", "REPLACE_WITH_IMMUTABLE_TAG"}:
        raise ValueError("Use a unique build or commit tag instead of latest.")
    root = Path(__file__).resolve().parents[1]
    deployment = (root / "k8s/deployment.yaml").read_text()
    return deployment.replace("YOUR_DOCKERHUB_USERNAME/task-manager:REPLACE_WITH_IMMUTABLE_TAG", image) + "\n---\n" + (root / "k8s/service.yaml").read_text()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--context", default="minikube")
    parser.add_argument("--dry-run", choices=["client", "server"])
    parser.add_argument("--output", action="store_true", help="Print rendered YAML without kubectl")
    args = parser.parse_args()
    try:
        yaml = render(args.image)
    except ValueError as error:
        parser.error(str(error))
    if args.output:
        print(yaml)
    else:
        command = ["kubectl", "--context", args.context, "apply", "-f", "-"]
        if args.dry_run:
            command.append(f"--dry-run={args.dry_run}")
        subprocess.run(command, input=yaml, text=True, check=True)
