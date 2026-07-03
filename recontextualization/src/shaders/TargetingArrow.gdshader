shader_type canvas_item;

uniform float speed = 3.0;
uniform vec4 arrow_color : source_color = vec4(1.0, 0.2, 0.2, 1.0);
uniform float segment_length = 0.1;
uniform float gap_length = 0.1;

void fragment() {
	float total_length = segment_length + gap_length;
	float pattern = fract((UV.x - TIME * speed) / total_length);
	
	// Create dashed line pattern
	float dash = step(gap_length / total_length, pattern);
	
	// Fade edges for glowing effect
	float edge = smoothstep(0.0, 0.3, UV.y) * smoothstep(1.0, 0.7, UV.y);
	
	vec4 color = arrow_color;
	color.a *= dash * edge;
	
	COLOR = color;
}
