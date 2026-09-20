extends Node3D

func _ready() -> void:
	# Lighting is calibrated for Compatibility without post-process tint.
	$Sun.light_color = Color(1.0, 0.80, 0.63)
	$Sun.light_energy = 0.65
	$Sun.shadow_opacity = 0.48
	if RenderingServer.get_current_rendering_method() == "gl_compatibility":
		$Sun.light_energy = 0.38
		$Environment.environment.background_energy_multiplier = 0.8
	var hazard := preload("res://materials/dusk_hazard.tres")
	for platform in $World.get_children():
		if platform.scene_file_path == "res://objects/platform_falling.tscn":
			for mesh in platform.find_children("*", "MeshInstance3D", true, false):
				mesh.material_override = hazard
