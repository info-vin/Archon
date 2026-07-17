shader_type canvas_item;

uniform vec4 base_color : source_color = vec4(0.2, 0.8, 0.7, 0.5);
uniform vec4 accent_color : source_color = vec4(0.9, 0.3, 0.2, 0.5);
uniform vec4 bg_color : source_color = vec4(0.02, 0.08, 0.1, 0.0);
uniform float line_thickness = 0.005;
uniform float time_scale = 1.0;
uniform sampler2D screen_texture : hint_screen_texture;

void fragment() {
    // Generate a subtle animated background noise or scanline effect
    vec2 uv = UV;
    
    // Scanlines
    float scanline = sin(uv.y * 800.0) * 0.04;
    
    // Vignette / gradient masking
    float dist = distance(uv, vec2(0.5, 0.5));
    float vignette = smoothstep(0.8, 0.2, dist);
    
    // Safely read the screen texture without mipmap LOD to avoid macOS Metal driver crashes
    vec4 tex = texture(screen_texture, SCREEN_UV);
    
    // Darken and apply vignette
    COLOR = mix(tex, bg_color, 0.7) - vec4(scanline) * vignette;
    COLOR.a = 0.5; // Overall opacity
}
