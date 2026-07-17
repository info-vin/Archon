shader_type canvas_item;

uniform vec4 bg_color : source_color = vec4(0.08, 0.14, 0.22, 0.95);
uniform vec4 cyan_color : source_color = vec4(0.2, 0.8, 1.0, 1.0);
uniform vec4 red_color : source_color = vec4(1.0, 0.35, 0.35, 1.0);
uniform vec4 grid_color : source_color = vec4(0.2, 0.5, 0.8, 0.15);

uniform float aspect_ratio = 1.777; // Roughly 16:9
uniform float time_scale = 1.0;

// Rotate 2D vector
vec2 rotate(vec2 p, float angle) {
    float s = sin(angle);
    float c = cos(angle);
    return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}

void fragment() {
    // 1. Setup Coordinates and Scale (Shrink by 30%)
    vec2 uv = (UV - 0.5) / 0.7;
    uv.x *= aspect_ratio;
    vec2 abs_uv = abs(uv);
    
    vec4 final_color = bg_color;
    
    // 2. Background Grid (Thinner, more subtle)
    vec2 grid_uv = fract(uv * 40.0); // Denser grid
    float grid_line = smoothstep(0.03, 0.01, grid_uv.x) + smoothstep(0.97, 0.99, grid_uv.x) +
                      smoothstep(0.03, 0.01, grid_uv.y) + smoothstep(0.97, 0.99, grid_uv.y);
    final_color.rgb = mix(final_color.rgb, grid_color.rgb, clamp(grid_line, 0.0, 1.0) * grid_color.a);
    
    float red_elements = 0.0;
    float cyan_elements = 0.0;
    float red_glow = 0.0;
    float cyan_glow = 0.0;
    
    // 3. Center Diamond (Red)
    float diamond_dist = abs_uv.x + abs_uv.y;
    // Hollow diamond (thinner)
    float diamond = smoothstep(0.052, 0.048, diamond_dist) - smoothstep(0.042, 0.038, diamond_dist);
    float d_glow = smoothstep(0.08, 0.01, abs(diamond_dist - 0.045));
    red_elements = max(red_elements, diamond);
    red_glow = max(red_glow, d_glow);
    
    // Center Dot
    float center_dot = smoothstep(0.006, 0.002, length(uv));
    float c_glow = smoothstep(0.03, 0.0, length(uv));
    
    // Cross marks (thinner)
    if (abs_uv.x < 0.002 && abs_uv.y > 0.07 && abs_uv.y < 0.12) {
        red_elements = 1.0;
        red_glow = max(red_glow, 1.0 - (abs_uv.x / 0.01));
    }
    if (abs_uv.y < 0.002 && abs_uv.x > 0.07 && abs_uv.x < 0.12) {
        red_elements = 1.0;
        red_glow = max(red_glow, 1.0 - (abs_uv.y / 0.01));
    }
    
    // 4. Red Arcs (thinner)
    float arc_radius = 0.28;
    float arc_dist = abs(length(uv) - arc_radius);
    float arc_line = smoothstep(0.004, 0.001, arc_dist);
    float a_glow = smoothstep(0.03, 0.0, arc_dist);
    // Mask to only show left and right
    float arc_mask = smoothstep(0.40, 0.35, abs_uv.y);
    // Only outer edges
    float arcs = arc_line * arc_mask * smoothstep(0.12, 0.15, abs_uv.x);
    red_elements = max(red_elements, arcs);
    red_glow = max(red_glow, a_glow * arc_mask * smoothstep(0.12, 0.15, abs_uv.x));
    
    // Arc equator ticks (thinner)
    if (abs_uv.y < 0.002 && abs_uv.x > 0.26 && abs_uv.x < 0.30) {
        red_elements = 1.0;
        red_glow = max(red_glow, 1.0 - (abs_uv.y / 0.01));
    }
    
    // 5. Red Top/Bottom Rulers (thinner)
    float ruler_y = 0.38;
    if (abs_uv.y > ruler_y && abs_uv.y < ruler_y + 0.03 && abs_uv.x < 0.25) {
        // Base line
        if (abs_uv.y < ruler_y + 0.002) red_elements = 1.0;
        
        // Ticks
        float tick_space = uv.x * 30.0;
        float tick_pos = fract(tick_space);
        if (tick_pos < 0.1) {
            float is_long = step(0.9, fract(tick_space * 0.2));
            float tick_len = mix(0.01, 0.025, is_long);
            if (abs_uv.y < ruler_y + tick_len) red_elements = 1.0;
        }
    }
    
    // 6. Cyan Brackets (Half as thick)
    vec2 bracket_pos = vec2(0.55, 0.35);
    
    // Outer L-shape
    if (abs_uv.x > bracket_pos.x && abs_uv.x < bracket_pos.x + 0.005 && abs_uv.y < bracket_pos.y + 0.005) {
        cyan_elements = 1.0;
    }
    if (abs_uv.y > bracket_pos.y && abs_uv.y < bracket_pos.y + 0.005 && abs_uv.x > bracket_pos.x - 0.06 && abs_uv.x < bracket_pos.x + 0.005) {
        cyan_elements = 1.0;
    }
    // Add glow to brackets based on distance
    float cb_dist = min(abs(abs_uv.x - bracket_pos.x), abs(abs_uv.y - bracket_pos.y));
    if (abs_uv.x > bracket_pos.x - 0.08 && abs_uv.y < bracket_pos.y + 0.03) {
        cyan_glow = max(cyan_glow, smoothstep(0.03, 0.0, cb_dist));
    }
    
    // Inner angled accent (thinner)
    vec2 p = abs_uv - vec2(bracket_pos.x - 0.02, bracket_pos.y - 0.02);
    vec2 rot_p = rotate(p, 0.785398); // 45 degrees
    if (rot_p.x > 0.0 && rot_p.x < 0.003 && rot_p.y > -0.03 && rot_p.y < 0.03) {
        cyan_elements = 1.0;
    }
    
    // Side Red Dashes (Half amount)
    if (abs_uv.x > bracket_pos.x - 0.04 && abs_uv.x < bracket_pos.x - 0.025) {
        float dash_y = abs_uv.y * 10.0;
        if (fract(dash_y) < 0.15 && abs_uv.y < 0.3) {
            red_elements = 1.0;
        }
    }
    
    // Enhance Colors with Glow (HDR style multipliers) to make it HIGHLY BRIGHT
    vec3 glowing_red = red_color.rgb * 3.0;
    vec3 glowing_cyan = cyan_color.rgb * 3.0;
    
    // Apply Glows (Additive blending for bloom effect) - stronger glow
    final_color.rgb += glowing_red * (red_glow * 0.8);
    final_color.rgb += glowing_cyan * (cyan_glow * 0.8);
    
    // Combine sharp elements
    vec3 sharp_red = mix(glowing_red, vec3(1.0, 0.9, 0.9), red_elements * 0.8);
    vec3 sharp_cyan = mix(glowing_cyan, vec3(0.9, 1.0, 1.0), cyan_elements * 0.8);
    
    final_color.rgb = mix(final_color.rgb, sharp_red, clamp(red_elements, 0.0, 1.0));
    final_color.a = max(final_color.a, clamp(red_elements + red_glow, 0.0, 1.0) * red_color.a);
    
    final_color.rgb = mix(final_color.rgb, vec3(1.0), center_dot); // Pure white dot
    final_color.rgb += glowing_red * (c_glow * 0.8); // Stronger Red halo around dot
    final_color.a = max(final_color.a, center_dot + c_glow);
    
    final_color.rgb = mix(final_color.rgb, sharp_cyan, clamp(cyan_elements, 0.0, 1.0));
    final_color.a = max(final_color.a, clamp(cyan_elements + cyan_glow, 0.0, 1.0) * cyan_color.a);
    
    // Vignette
    float vignette = smoothstep(1.2, 0.4, length(uv));
    final_color.a *= vignette;
    
    // No more 50% transparency reduction to keep it bright!
    
    COLOR = final_color;
}
