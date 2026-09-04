import os
import subprocess
import argparse

def generate_frames(input_file, num_frames=300):
    tmp_dir = "renders/frames"
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"Generating {num_frames} frames from {input_file} using OpenSCAD...")

    for frame in range(num_frames):
        t = frame / (num_frames - 1)
        # 360 rotation around Z
        rot_z = 360 * t

        # Camera string: trans_x,trans_y,trans_z,rot_x,rot_y,rot_z,distance
        camera_str = f"0,0,30,60,0,{rot_z},250"

        output_png = os.path.join(tmp_dir, f"frame_{frame:03d}.png")

        cmd = [
            "openscad",
            "--camera", camera_str,
            "--imgsize", "1920,1080",
            "--colorscheme", "DeepOcean",
            "-D", f"$t={t}",
            "-o", output_png,
            input_file
        ]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if frame % 30 == 0:
                print(f"  Processed frame {frame}/{num_frames}")
        except FileNotFoundError:
            if frame == 0:
                print("OpenSCAD not found in PATH. Skipping frame generation.")
            break
        except subprocess.CalledProcessError as e:
            print(f"Error generating frame {frame}: {e}")
            break

def encode_video(output_webm, output_mp4, framerate=30):
    tmp_dir = "renders/frames"
    input_pattern = os.path.join(tmp_dir, "frame_%03d.png")

    print("\nEncoding WebM...")
    cmd_webm = [
        "ffmpeg", "-y", "-framerate", str(framerate),
        "-i", input_pattern,
        "-c:v", "libvpx-vp9", "-b:v", "2M",
        output_webm
    ]
    try:
        subprocess.run(cmd_webm, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Saved: {output_webm}")
    except FileNotFoundError:
        print("FFmpeg not found in PATH. Skipping WebM encoding.")
    except subprocess.CalledProcessError as e:
        print(f"Error encoding WebM: {e}")

    print("\nEncoding MP4...")
    cmd_mp4 = [
        "ffmpeg", "-y", "-framerate", str(framerate),
        "-i", input_pattern,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        output_mp4
    ]
    try:
        subprocess.run(cmd_mp4, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Saved: {output_mp4}")
    except FileNotFoundError:
        print("FFmpeg not found in PATH. Skipping MP4 encoding.")
    except subprocess.CalledProcessError as e:
        print(f"Error encoding MP4: {e}")


def main():
    os.makedirs("renders", exist_ok=True)

    input_scad = "openscad-legacy/sentinel_nanopore_reader.scad"
    output_webm = "renders/openscad_animation.webm"
    output_mp4 = "renders/openscad_animation.mp4"

    generate_frames(input_scad, num_frames=300)
    encode_video(output_webm, output_mp4)

    print("\nOpenSCAD Animation Pipeline Complete!")

if __name__ == "__main__":
    main()
