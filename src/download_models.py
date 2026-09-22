import os
import sys
import shutil
import argparse

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Error: huggingface_hub library is missing. Install it using: pip install huggingface_hub", file=sys.stderr)
    sys.exit(1)

DEFAULT_CONFIG_YAML = """# Pyannote offline configuration template.
pipeline:
  name: pyannote.audio.pipelines.SpeakerDiarization
  params:
    clustering: AgglomerativeClustering
    embedding: pyannote/wespeaker-voxceleb-resnet34-LM
    segmentation: pyannote/segmentation-3.0

params:
  segmentation:
    min_duration_off: 0.0
  clustering:
    threshold: 0.7153814330596601
"""

def main():
    parser = argparse.ArgumentParser(description="Download Pyannote offline models directly into the build models directory.")
    parser.add_argument("pos_token", nargs="?", default=None, help="Hugging Face access token (optional if passed via --token or HF_TOKEN env var)")
    parser.add_argument("--token", dest="opt_token", default=None, help="Hugging Face access token")
    parser.add_argument(
        "--dest_dir",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist", "models")),
        help="Destination directory for models (defaults to dist/models)"
    )
    args = parser.parse_args()

    token = args.opt_token or args.pos_token or os.environ.get("HF_TOKEN")
    if not token:
        print("Note: Pyannote models are gated. If download fails, provide your Hugging Face token:")
        print("  python src/download_models.py <YOUR_HF_TOKEN>")
        print("Or set the environment variable: $env:HF_TOKEN=\"<YOUR_HF_TOKEN>\"")
        print("Token page: https://huggingface.co/settings/tokens\n")

    dest_dir = os.path.abspath(args.dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    print(f"Target model directory: {dest_dir}\n")

    # 1. Download Pyannote Segmentation 3.0 model
    print("Checking/Downloading Pyannote Segmentation 3.0 model...")
    try:
        seg_path = hf_hub_download(
            repo_id="pyannote/segmentation-3.0",
            filename="pytorch_model.bin",
            local_dir=dest_dir,
            token=token
        )
        final_seg_path = os.path.join(dest_dir, "segmentation-3.0.bin")
        if os.path.abspath(seg_path) != os.path.abspath(final_seg_path):
            if os.path.exists(final_seg_path):
                os.remove(final_seg_path)
            shutil.move(seg_path, final_seg_path)
        print(f"Successfully saved segmentation model to: {final_seg_path}")
    except Exception as e:
        print(f"Error downloading segmentation model: {str(e)}", file=sys.stderr)
        print("Note: You may need to accept the model license agreement at https://huggingface.co/pyannote/segmentation-3.0", file=sys.stderr)

    # 2. Download Pyannote WeSpeaker Embedding model
    print("\nChecking/Downloading Pyannote WeSpeaker Embedding model...")
    try:
        embed_path = hf_hub_download(
            repo_id="pyannote/wespeaker-voxceleb-resnet34-LM",
            filename="pytorch_model.bin",
            local_dir=dest_dir,
            token=token
        )
        final_embed_path = os.path.join(dest_dir, "wespeaker-voxceleb-resnet34-LM.bin")
        if os.path.abspath(embed_path) != os.path.abspath(final_embed_path):
            if os.path.exists(final_embed_path):
                os.remove(final_embed_path)
            shutil.move(embed_path, final_embed_path)
        print(f"Successfully saved embedding model to: {final_embed_path}")
    except Exception as e:
        print(f"Error downloading embedding model: {str(e)}", file=sys.stderr)
        print("Note: You may need to accept the model license agreement at https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM", file=sys.stderr)

    # 3. Ensure config.yaml is present in the build models directory
    config_path = os.path.join(dest_dir, "config.yaml")
    if not os.path.exists(config_path):
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_YAML)
        print(f"\nCreated config.yaml at {config_path}")
    else:
        # Normalize any onnx references in existing config.yaml to .bin
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "wespeaker-voxceleb-resnet34-LM.onnx" in content:
                content = content.replace("wespeaker-voxceleb-resnet34-LM.onnx", "wespeaker-voxceleb-resnet34-LM.bin")
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"\nUpdated model paths in existing config.yaml.")
        except Exception as e:
            print(f"Warning: Could not update existing config.yaml: {e}", file=sys.stderr)

    print(f"\nAll models downloaded and configured in: {dest_dir}")

if __name__ == "__main__":
    main()
