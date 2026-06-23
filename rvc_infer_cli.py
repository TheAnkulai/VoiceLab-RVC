import os
import sys
import argparse
import shutil
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Run RVC inference without Gradio UI.")

    parser.add_argument("--model", required=True, help="Model file name from weights folder, for example model.pth")
    parser.add_argument("--input", required=True, help="Input WAV path")
    parser.add_argument("--output", required=True, help="Output WAV path")

    parser.add_argument("--index", default="", help="Index path. Can be empty.")
    parser.add_argument("--pitch", type=int, default=0, help="Pitch shift in semitones")
    parser.add_argument("--f0-method", default="pm", choices=["pm", "harvest", "crepe", "rmvpe"])
    parser.add_argument("--index-rate", type=float, default=0.0)
    parser.add_argument("--filter-radius", type=int, default=0)
    parser.add_argument("--resample-sr", type=int, default=0)
    parser.add_argument("--rms-mix-rate", type=float, default=1.0)
    parser.add_argument("--protect", type=float, default=0.33)
    parser.add_argument("--speaker-id", type=int, default=0)

    return parser.parse_args()


def find_latest_gradio_audio() -> Path | None:
    temp_root = Path(os.environ.get("TEMP", "")) / "gradio"

    if not temp_root.exists():
        return None

    files = list(temp_root.rglob("audio.wav"))

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def main() -> None:
    args = parse_args()

    # ВАЖНО:
    # RVC Config сам парсит sys.argv.
    # Поэтому убираем наши аргументы, чтобы Config их не увидел.
    sys.argv = [sys.argv[0]]

    now_dir = os.getcwd()
    sys.path.append(now_dir)

    from dotenv import load_dotenv

    load_dotenv()
    
    os.environ.setdefault("weight_root", "assets/weights")
    os.environ.setdefault("weight_uvr5_root", "assets/uvr5_weights")
    os.environ.setdefault("index_root", "logs")
    os.environ.setdefault("outside_index_root", "logs")
    os.environ.setdefault("rmvpe_root", "assets/rmvpe")

    from configs.config import Config
    from infer.modules.vc.modules import VC

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    config = Config()
    vc = VC(config)

    print(f"Loading model: {args.model}")
    vc.get_vc(args.model, args.protect, args.protect)

    print("Running inference...")
    result = vc.vc_single(
        args.speaker_id,
        str(input_path),
        args.pitch,
        None,
        args.f0_method,
        args.index,
        "",
        args.index_rate,
        args.filter_radius,
        args.resample_sr,
        args.rms_mix_rate,
        args.protect,
    )

    print("Raw result type:", type(result))

    if isinstance(result, (list, tuple)) and len(result) > 0:
        print("Info:")
        print(result[0])
    else:
        print("Result:")
        print(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Нормальный путь: vc_single вернул (sr, audio)
    if isinstance(result, (list, tuple)) and len(result) >= 2 and result[1] is not None:
        audio_result = result[1]

        try:
            import soundfile as sf

            sample_rate, audio = audio_result
            sf.write(str(output_path), audio, sample_rate)
            print(f"Saved output: {output_path}")
            return
        except Exception as error:
            print(f"Could not save returned audio directly: {error}")

    # Запасной путь: забираем последний temp audio.wav
    latest_audio = find_latest_gradio_audio()

    if latest_audio is None:
        raise RuntimeError("Inference finished, but no output audio was found.")

    shutil.copy2(latest_audio, output_path)

    print("Copied latest temp audio:")
    print(f"  from: {latest_audio}")
    print(f"  to:   {output_path}")


if __name__ == "__main__":
    main()