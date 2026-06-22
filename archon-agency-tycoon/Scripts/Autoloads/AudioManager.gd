extends Node

# AudioManager Autoload for retro chiptune BGMs and SFX

var bgm_player: AudioStreamPlayer
var sfx_player: AudioStreamPlayer

var bgm_tracks: Dictionary = {}
var sfx_tracks: Dictionary = {}

var bgm_names: Array = ["cyberpunk", "neon_city", "hacking"]
var current_bgm_idx: int = 0
var current_bgm_name: String = "cyberpunk"

func _ready() -> void:
	# Add audio stream players to scene tree
	bgm_player = AudioStreamPlayer.new()
	bgm_player.name = "BgmPlayer"
	add_child(bgm_player)
	
	sfx_player = AudioStreamPlayer.new()
	sfx_player.name = "SfxPlayer"
	add_child(sfx_player)
	
	# Defensively load BGM tracks
	var bgm_paths = {
		"cyberpunk": "res://Assets/Sound/bgm_cyberpunk.wav",
		"neon_city": "res://Assets/Sound/bgm_neon_city.wav",
		"hacking": "res://Assets/Sound/bgm_hacking.wav"
	}
	for track in bgm_paths:
		var path = bgm_paths[track]
		if ResourceLoader.exists(path):
			var stream = load(path)
			if stream:
				bgm_tracks[track] = stream
				
	# Defensively load SFX tracks
	var sfx_paths = {
		"coin": "res://Assets/Sound/sfx_coin.wav",
		"alarm": "res://Assets/Sound/sfx_alarm.wav",
		"sigh": "res://Assets/Sound/sfx_sigh.wav"
	}
	for sfx in sfx_paths:
		var path = sfx_paths[sfx]
		if ResourceLoader.exists(path):
			var stream = load(path)
			if stream:
				sfx_tracks[sfx] = stream
	
	# Start playing default BGM if available
	if bgm_tracks.has("cyberpunk"):
		play_bgm("cyberpunk")

func play_bgm(track_name: String) -> void:
	if not bgm_tracks.has(track_name):
		if DisplayServer.get_name() != "headless":
			push_warning("AudioManager: BGM track '%s' not found" % track_name)
		return
	
	var stream = bgm_tracks[track_name]
	if stream:
		# Enable looping on loop mode properties in Godot 4.x AudioStreamWAV if possible,
		# but preloaded wav import should already handle loop flags.
		# Let's ensure looping is active by overriding loop_mode if supported.
		if stream.has_method("set_loop_mode"):
			stream.set_loop_mode(1) # LOOP_FORWARD
		bgm_player.stream = stream
		bgm_player.play()
		current_bgm_name = track_name
		current_bgm_idx = bgm_names.find(track_name)

func cycle_bgm() -> String:
	current_bgm_idx = (current_bgm_idx + 1) % bgm_names.size()
	var next_track = bgm_names[current_bgm_idx]
	play_bgm(next_track)
	return next_track

func play_sfx(sfx_name: String) -> void:
	if not sfx_tracks.has(sfx_name):
		if DisplayServer.get_name() != "headless":
			push_warning("AudioManager: SFX '%s' not found" % sfx_name)
		return
	
	var stream = sfx_tracks[sfx_name]
	if stream:
		sfx_player.stream = stream
		sfx_player.play()

func stop_bgm() -> void:
	bgm_player.stop()
