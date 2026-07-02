import os
import glob
from moviepy import VideoFileClip

def convert_to_ogv(input_path, output_path):
    # 定義目標長度 (秒)
    TARGET_DURATIONS = {
        "transition_battle_intro": 3.0,
        "transition_victory": 5.0,
        "transition_defeat_glitch": 2.0,
        "transition_defeat_shutdown": 3.0,
        "transition_os_boot": 6.0,  # 上限 6 秒
    }
    
    filename_no_ext = os.path.basename(input_path).rsplit('.', 1)[0]
    target_duration = TARGET_DURATIONS.get(filename_no_ext, None)
    
    print(f"Processing {input_path}...")
    try:
        clip = VideoFileClip(input_path)
        
        # 檢查是否需要加速
        if target_duration and clip.duration > target_duration:
            speed_factor = clip.duration / target_duration
            print(f"  -> Original duration: {clip.duration:.2f}s. Scaling speed by {speed_factor:.2f}x to fit {target_duration}s.")
            clip = clip.with_speed_scaled(speed_factor)
        else:
            print(f"  -> Duration {clip.duration:.2f}s is within target limits.")
            
        # Godot requires theora codec and vorbis audio for .ogv playback
        clip.write_videofile(
            output_path, 
            codec='libtheora', 
            audio_codec='libvorbis',
            bitrate='2000k'
        )
        clip.close()
        print(f"✅ Success! Created {output_path}")
    except Exception as e:
        print(f"❌ Error during conversion: {e}")

if __name__ == "__main__":
    # Path to VFX directory
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recontextualization", "assets", "vfx"))
    print(f"Scanning directory for .mp4 files: {assets_dir}")
    
    mp4_files = glob.glob(os.path.join(assets_dir, "*.mp4"))
    if not mp4_files:
        print("No .mp4 files found.")
    
    for mp4_file in mp4_files:
        ogv_file = mp4_file.rsplit('.', 1)[0] + '.ogv'
        convert_to_ogv(mp4_file, ogv_file)
