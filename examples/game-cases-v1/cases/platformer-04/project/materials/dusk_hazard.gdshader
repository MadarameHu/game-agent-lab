shader_type spatial;
render_mode diffuse_burley;
uniform sampler2D original_colormap : source_color;
varying vec3 local_position;
varying vec3 local_normal;
void vertex() {
 local_position = VERTEX;
 local_normal = NORMAL;
}
void fragment() {
 vec3 original = texture(original_colormap, UV).rgb;
 float stripe = step(0.48, fract((local_position.x + local_position.z) * 2.5));
 vec3 hazard = mix(vec3(0.58, 0.105, 0.09), vec3(1.0, 0.70, 0.31), stripe);
 ALBEDO = local_normal.y > 0.5 ? hazard : mix(original, vec3(0.65,0.22,0.14),0.60);
 ROUGHNESS = 0.85;
}
