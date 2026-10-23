from pydub import AudioSegment
import pyaudioop


def amplify_mp3(input_path: str, output_path: str, target_db: float = -1.0):
    """
    放大MP3音量，自动避免破音
    :param input_path: 输入mp3路径
    :param output_path: 输出放大后mp3
    :param target_db: 目标响度，一般-1~-3dB
    """
    # 读取mp3
    sound = AudioSegment.from_mp3(input_path)
    # 获取当前最大响度
    current_max_db = sound.max_dBFS
    # 计算需要增加的音量差值
    gain = target_db - current_max_db
    # 放大音频
    louder_sound = sound + gain
    # 导出mp3
    louder_sound.export(output_path, format="mp3")
    print(f"放大完成，增益 {gain:.2f} dB，保存至 {output_path}")

# 使用示例
if __name__ == "__main__":
    amplify_mp3("E:\\voice\\#1炉高压减温水调门给定.mp3", "E:\\voice\\#1炉高压减温水调门给定-1.mp3", target_db=-1.0)