import requests as r
import os
from pydub import AudioSegment
import time

# Directory where the MP3 files are saved
source_directory = "F:\\Call Recordings\\"
# Directory where the WAV files will be saved
output_directory = "F:\\Call Recordings\\data\\"

# Ensure output directory exists
os.makedirs(output_directory, exist_ok=True)

numbers = [
    638, 4065, 4074, 4077, 4092, 4093, 4104, 4112, 4145, 4156, 4157, 4170, 4183, 4184, 4234,
    4245, 4247, 4248, 4289, 4290, 4310, 4315, 4316, 4325, 4335, 4365, 4371, 4390, 4404, 4415,
    4431, 4432, 4459, 4484, 4485, 4490, 4507, 4520, 4521, 4522, 4537, 4543, 4544, 4547, 4556,
    4560, 4564, 4569, 4571, 4574, 4576, 4577, 4580, 4595, 4601, 4604, 4610, 4612, 4616, 4622,
    4623, 4624, 4628, 4629, 4660, 4665, 4666, 4673, 4677, 4683, 4686, 4689, 4694, 4702, 4705,
    4721, 4726, 4753, 4776, 4790, 4792, 4801, 4802, 4807, 4808, 4822, 4824, 4829, 4838, 4844,
    4852, 4854, 4861, 4875, 4886, 4887, 4902, 4908, 4910, 4913, 4926, 4927, 4938, 4941, 4966,
    4967, 4968, 5011, 5017, 5020, 5023, 5046, 5166, 5208, 5242, 5254, 5273, 5278, 5352, 5373,
    5388, 5495, 5532, 5551, 5573, 5648, 5700, 5712, 5713, 5736, 5777, 5788, 5866, 5872, 5888,
    5907, 5931, 6033, 6045, 6047, 6067, 6071, 6079, 6100, 6107, 6130, 6161, 6165, 6179, 6183,
    6189, 6217, 6252, 6265, 6267, 6274, 6282, 6298, 6313, 6314, 6348, 6408, 6447, 6456, 6467,
    6474, 6479, 6489, 6521, 6625, 6658, 6785, 6825, 6861, 6880, 6912
]

# for n in numbers:
#     url = f"https://media.talkbank.org/ca/CallHome/eng/{n}"
#     res = r.get(url)
    
#     with open(f"{n}.mp3", "wb") as f:
#         f.write(res.content)
    
#     print(f"Downloaded {n}.mp3")
# print(os.listdir(source_directory))

for n in numbers:
    mp3_path = os.path.join(source_directory, f"{n}.mp3")
    wav_path = os.path.join(output_directory, f"{n}.wav")

    if os.path.exists(mp3_path):
        try:
            audio = AudioSegment.from_mp3(mp3_path)
            audio.export(wav_path, format="wav")
            print(f"Converted {n}.mp3 to WAV")

            # Delete the MP3 file (optional)
            # os.remove(mp3_path)
            # print(f"Deleted {n}.mp3")

        except Exception as e:
            print(f"Error converting {n}.mp3: {e}")
    else:
        print(f"File {n}.mp3 not found, skipping conversion.")