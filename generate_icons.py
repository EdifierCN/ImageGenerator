import os
import subprocess


def generate_ico(input_path, output_path):
    tmp_dir = "tmp_ico"
    os.makedirs(tmp_dir, exist_ok=True)
    sizes = ["16x16", "32x32", "48x48", "256x256", "512x512"]

    for size in sizes:
        subprocess.run([
            "magick", "convert", input_path,
            "-resize", f"{size}^",
            "-gravity", "center",
            "-background", "none",
            "-extent", size,
            "-quality", "100",
            f"{tmp_dir}/{size}.png"
        ])

    subprocess.run([
        "magick", "convert", f"{tmp_dir}/*.png", output_path
    ])
    os.system(f"rm -rf {tmp_dir}")


def generate_icns(input_path, output_path):
    tmp_dir = "tmp_icns"
    os.makedirs(tmp_dir, exist_ok=True)
    sizes = [16, 32, 128, 256, 512, 1024]

    for size in sizes:
        subprocess.run([
            "magick", "convert", input_path,
            "-resize", f"{size}x{size}^",
            "-gravity", "center",
            "-background", "none",
            "-extent", f"{size}x{size}",
            "-quality", "100",
            f"{tmp_dir}/icon_{size}x{size}.png"
        ])

    subprocess.run([
        "magick", "convert", f"{tmp_dir}/*.png", output_path
    ])
    os.system(f"rm -rf {tmp_dir}")


if __name__ == "__main__":
    input_file = "icon.png"
    generate_ico(input_file, "app.ico")
    generate_icns(input_file, "app.icns")
