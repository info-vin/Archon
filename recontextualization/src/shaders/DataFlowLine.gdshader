shader_type canvas_item;

uniform float speed = 2.0;
uniform vec4 glow_color : source_color = vec4(0.0, 1.0, 1.0, 1.0);
uniform float line_thickness = 1.0;

void fragment() {
	// A simple moving dashed line effect to simulate data flow
	float dash = step(0.5, fract(UV.x * 10.0 - TIME * speed));
	
	// Fade the edges to make it look like a glowing beam
	float edge = smoothstep(0.0, 0.2, UV.y) * smoothstep(1.0, 0.8, UV.y);
	
	vec4 color = glow_color;
	color.a *= dash * edge * line_thickness;
	
	COLOR = color;
}
