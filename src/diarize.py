import os
import sys
import json
import argparse
import warnings
import wave
import numpy as np

# Suppress warnings for cleaner console output
warnings.filterwarnings("ignore")

def load_wav_as_tensor(wav_path, torch_module):
    with wave.open(wav_path, "rb") as w:
        sample_rate = w.getframerate()
        n_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        n_frames = w.getnframes()
        
        data = w.readframes(n_frames)
        
        if sampwidth == 1:
            dtype = np.uint8
        elif sampwidth == 2:
            dtype = np.int16
        elif sampwidth == 4:
            dtype = np.int32
        else:
            raise ValueError(f"Unsupported sample width: {sampwidth}")
            
        waveform = np.frombuffer(data, dtype=dtype)
        
        if n_channels > 1:
            waveform = waveform.reshape(-1, n_channels)
            
        if dtype == np.uint8:
            waveform = (waveform.astype(np.float32) - 128.0) / 128.0
        elif dtype == np.int16:
            waveform = waveform.astype(np.float32) / 32768.0
        elif dtype == np.int32:
            waveform = waveform.astype(np.float32) / 2147483648.0
            
        waveform_tensor = torch_module.tensor(waveform, dtype=torch_module.float32)
        if n_channels > 1:
            waveform_tensor = waveform_tensor.T
        else:
            waveform_tensor = waveform_tensor.unsqueeze(0)
            
        return waveform_tensor, sample_rate

def resolve_output_json(wav_path, output_path):
    if not output_path:
        output_path = "output"
    if os.path.isdir(output_path) or not output_path.lower().endswith(".json"):
        os.makedirs(output_path, exist_ok=True)
        base = os.path.splitext(os.path.basename(wav_path))[0]
        return os.path.join(output_path, f"{base}_diarization.json")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    return output_path

def diarize(wav_path, output_path, model_dir, threshold=0.90, device="auto"):
    if not os.path.exists(wav_path):
        print(f"Error: Audio file not found: {wav_path}", file=sys.stderr)
        sys.exit(1)

    if not model_dir or not os.path.exists(model_dir):
        print(f"Error: Model directory not found: {model_dir}", file=sys.stderr)
        sys.exit(1)

    output_json = resolve_output_json(wav_path, output_path)

    config_path = os.path.join(model_dir, "config.yaml")
    if not os.path.exists(config_path):
        print(f"Error: Model config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    # Configure local Hugging Face cache if present in model directory for offline inference
    hf_cache_dir = os.path.join(model_dir, "huggingface")
    if os.path.exists(hf_cache_dir) and "HF_HOME" not in os.environ:
        os.environ["HF_HOME"] = os.path.abspath(hf_cache_dir)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    try:
        import torch
        # PyTorch 2.6+ defaults weights_only=True which blocks loading Pyannote checkpoints
        _orig_torch_load = torch.load
        def _safe_torch_load(*args, **kwargs):
            kwargs["weights_only"] = False
            return _orig_torch_load(*args, **kwargs)
        torch.load = _safe_torch_load

        from pyannote.audio import Model, Pipeline
        from pyannote.audio.pipelines import SpeakerDiarization
    except ImportError as e:
        print(f"Error: Required Python dependencies missing: {str(e)}. Please install torch and pyannote.audio.", file=sys.stderr)
        sys.exit(1)

    try:
        seg_bin = os.path.join(model_dir, "segmentation-3.0.bin")
        emb_bin = os.path.join(model_dir, "wespeaker-voxceleb-resnet34-LM.bin")

        # Load offline model directly if weights exist in model_dir
        if os.path.exists(seg_bin) and os.path.exists(emb_bin):
            emb_model = Model.from_pretrained(emb_bin)
            pipeline = SpeakerDiarization(
                segmentation=seg_bin,
                embedding=emb_model,
                clustering="AgglomerativeClustering"
            )
        else:
            pipeline = Pipeline.from_pretrained(config_path)
        
        # Instantiate pipeline parameters programmatically with supported schema
        try:
            instantiate_params = {
                "segmentation": {
                    "min_duration_off": 0.5
                },
                "clustering": {
                    "threshold": float(threshold) if threshold is not None else 0.90,
                    "method": "centroid",
                    "min_cluster_size": 1
                }
            }
            pipeline.instantiate(instantiate_params)
        except Exception as inst_err:
            print(f"Warning: Failed to instantiate parameters: {str(inst_err)}", file=sys.stderr)
        
        if device == "cuda":
            if not torch.cuda.is_available():
                print("Error: --device cuda requested but CUDA is not available", file=sys.stderr)
                sys.exit(1)
            torch_device = torch.device("cuda")
        elif device == "mps":
            if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                print("Error: --device mps requested but MPS is not available", file=sys.stderr)
                sys.exit(1)
            torch_device = torch.device("mps")
        elif device == "auto":
            if torch.cuda.is_available():
                torch_device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch_device = torch.device("mps")
            else:
                torch_device = torch.device("cpu")
        else:
            torch_device = torch.device("cpu")

        if torch_device.type == "cuda":
            pipeline.to(torch_device)
            print(f"[GPU ACTIVE] Using CUDA device: {torch.cuda.get_device_name(0)}")
        elif torch_device.type == "mps":
            pipeline.to(torch_device)
            print("[GPU ACTIVE] Using Apple MPS (Metal Performance Shaders)")
        else:
            print("[INFO] Running diarization on CPU")

        # Decode WAV using Python standard wave module to avoid torchaudio loader DLL issues
        waveform, sample_rate = load_wav_as_tensor(wav_path, torch)
        if torch_device.type != "cpu":
            waveform = waveform.to(torch_device)
            
        print(f"Processing diarization for {wav_path}...")

        diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
        
        # Unwrap DiarizeOutput to Annotation if needed
        if hasattr(diarization, "speaker_diarization"):
            diarization = diarization.speaker_diarization
            
        # Format segments
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            # Ignore tiny segments (< 0.2s) that are likely noise spikes
            if (turn.end - turn.start) < 0.2:
                continue
            segments.append({
                "speaker": speaker,
                "start": round(turn.start, 2),
                "end": round(turn.end, 2)
            })
            
        # Write to JSON
        with open(output_json, "w") as f:
            json.dump(segments, f, indent=2)
            
        print(f"Diarization completed successfully. Saved to {output_json}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error during diarization: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ilvi - Offline Speaker Diarization Engine (https://ilvi.ai/)")
    parser.add_argument("--audio_path", "--wav_path", dest="audio_path", required=True, help="Path to the input WAV audio file")
    parser.add_argument("--output_dir", required=True, help="Directory to save the output diarization JSON")
    parser.add_argument("--model_dir", required=True, help="Directory containing the offline pyannote models and config.yaml")
    parser.add_argument("--threshold", type=float, default=0.90, help="Clustering distance threshold (default 0.90)")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cpu", "cuda", "mps"], help="Device to run on: 'auto' (use GPU if available), 'cpu', 'cuda' (NVIDIA GPU), or 'mps' (Apple Silicon GPU) (default: auto)")

    args = parser.parse_args()

    diarize(args.audio_path, args.output_dir, args.model_dir, args.threshold, args.device)
