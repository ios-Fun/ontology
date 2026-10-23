import ffmpeg

def boost_mp3(input_path, output_path):
    (
        ffmpeg
        .input(input_path)
        .filter("loudnorm", I=-2, LRA=7, TP=-1)
        .output(output_path, audio_bitrate="192k")
        .overwrite_output()
        .run()
    )

boost_mp3(r"E:\voice\1.mp3", r"E:/voice/3.mp3")