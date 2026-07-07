shader_type canvas_item;
render_mode blend_add;


// The amount of horizontal tapering at the top and bottom (0.0 = rectangle, 0.5 = rhombus)
uniform float taper_amount : hint_range(0.0, 0.5) = 0.2;
// Edge smoothing for anti-aliasing
uniform float smoothing : hint_range(0.0, 0.1) = 0.01;

void fragment() {
    vec4 color = texture(TEXTURE, UV);
    
    // UV centered at 0,0, abs makes it symmetric for all 4 quadrants
    vec2 pos = abs(UV - vec2(0.5));
    
    // The maximum allowed X at this Y.
    // At pos.y = 0 (center vertical), X can go up to 0.5 (full width).
    // At pos.y = 0.5 (top/bottom), X is reduced by taper_amount.
    // Interpolate linearly:
    float edge_x = 0.5 - (taper_amount * (pos.y / 0.5));
    
    // Smooth step for anti-aliased edge
    float alpha = 1.0 - smoothstep(edge_x - smoothing, edge_x + smoothing, pos.x);
    
    COLOR = vec4(color.rgb, color.a * alpha);
}
