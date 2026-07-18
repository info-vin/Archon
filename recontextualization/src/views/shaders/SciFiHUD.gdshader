shader_type canvas_item;

// --- 參數 ---
uniform bool is_mirrored = false;
uniform float glitch_intensity : hint_range(0.0, 1.0) = 0.0;

uniform float purity_pct : hint_range(0.0, 1.0) = 0.5;
uniform float hp_pct : hint_range(0.0, 1.0) = 0.75;
uniform int ap_current = 6;
uniform int ap_max = 10;

uniform vec4 primary_color : source_color = vec4(0.0, 0.85, 1.0, 1.0);
uniform vec4 bg_panel_color : source_color = vec4(0.0, 0.1, 0.15, 0.6);
uniform float line_thickness = 0.005;
uniform float glow_strength = 1.5;

// === SDF 基礎函式 ===
float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

mat2 rot(float a) {
    float s = sin(a), c = cos(a);
    return mat2(vec2(c, -s), vec2(s, c));
}

void fragment() {
    vec2 uv = UV;
    if (is_mirrored) {
        uv.x = 1.0 - uv.x;
    }
    
    if (glitch_intensity > 0.0) {
        uv.x += sin(uv.y * 50.0 + TIME * 10.0) * glitch_intensity * 0.01;
    }
    
    vec2 p = uv * vec2(3.333, 1.0);
    
    vec3 col = vec3(0.0);
    float alpha = 0.0;
    
    // 1. 左側巨型圓環系統
    vec2 center = vec2(0.5, 0.5);
    float d_center = length(p - center);
    float angle = atan(p.y - center.y, p.x - center.x);
    
    float ring_thick = 0.025; // 總粗細改為 0.05
    float inner_radius = 0.38;
    float inner_ring = abs(d_center - inner_radius) - ring_thick;
    
    float outer_radius = 0.465;
    float outer_ring = abs(d_center - outer_radius) - ring_thick;
    
    // 圓環開口 (精確水平裁切，完全切齊主體 0.25 和 0.75)
    if (p.x > center.x && p.y > 0.25 && p.y < 0.75) {
        outer_ring = 999.0;
        inner_ring = 999.0;
    }
    
    for(int i=0; i<8; i++) {
        float a = float(i) * 3.14159 / 4.0;
        if (cos(a) > 0.0 && sin(a) > -0.4 && sin(a) < 0.4) continue; // 避開右側開口
        if (a > 6.28 - 0.4) continue;
        
        vec2 dir = vec2(cos(a), sin(a));
        vec2 notch_p = center + dir * outer_radius;
        vec2 local_p = p - notch_p;
        local_p = rot(-a) * local_p;
        if(local_p.x > 0.0 && local_p.x < 0.06 && abs(local_p.y) < (0.06 - local_p.x)) {
            outer_ring = min(outer_ring, -0.01);
        }
    }
    
    float normalized_angle = (angle + 3.14159) / (2.0 * 3.14159);
    float ring_alpha = 0.3;
    if (normalized_angle <= purity_pct) {
        ring_alpha = 1.0;
    }
    float ring_intensity = (1.0 - smoothstep(0.0, 0.01, inner_ring)) * ring_alpha;
    ring_intensity += (1.0 - smoothstep(0.0, 0.01, outer_ring));
    
    // 2. 右側主體框架 (區分粗水平線與細斜線)
    float d_thick = 999.0;
    float d_thin = 999.0;
    
    // Thick (Horizontal lines)
    d_thick = min(d_thick, sdSegment(p, vec2(0.80, 0.25), vec2(1.15, 0.25))); // Top arm + Top main
    d_thick = min(d_thick, sdSegment(p, vec2(1.25, 0.10), vec2(2.70, 0.10))); // Top text module
    d_thick = min(d_thick, sdSegment(p, vec2(2.80, 0.25), vec2(2.90, 0.25))); // Top main after module
    d_thick = min(d_thick, sdSegment(p, vec2(2.90, 0.75), vec2(2.30, 0.75))); // Bottom main before module
    d_thick = min(d_thick, sdSegment(p, vec2(2.20, 0.90), vec2(1.30, 0.90))); // Bottom text module
    d_thick = min(d_thick, sdSegment(p, vec2(1.20, 0.75), vec2(0.80, 0.75))); // Bottom main + Bottom arm
    
    // Thin (Slanted/Vertical lines)
    d_thin = min(d_thin, sdSegment(p, vec2(1.15, 0.25), vec2(1.25, 0.10))); // Top module step up
    d_thin = min(d_thin, sdSegment(p, vec2(2.70, 0.10), vec2(2.80, 0.25))); // Top module step down
    d_thin = min(d_thin, sdSegment(p, vec2(2.90, 0.25), vec2(3.20, 0.50))); // Arrow top
    d_thin = min(d_thin, sdSegment(p, vec2(3.20, 0.50), vec2(2.90, 0.75))); // Arrow bot
    d_thin = min(d_thin, sdSegment(p, vec2(2.30, 0.75), vec2(2.20, 0.90))); // Bottom module step down
    d_thin = min(d_thin, sdSegment(p, vec2(1.30, 0.90), vec2(1.20, 0.75))); // Bottom module step up
    
    // 非血條的水平線變粗兩倍，斜線維持原樣且亮度降至 0.8
    float thick_intensity = 1.0 - smoothstep(0.0, 0.01, d_thick - line_thickness * 2.0);
    float thin_intensity = (1.0 - smoothstep(0.0, 0.01, d_thin - line_thickness)) * 0.8;
    float frame_intensity = max(thick_intensity, thin_intensity);
    
    float right_bound_x = 3.2;
    if (p.y < 0.5) right_bound_x = 2.9 + (p.y - 0.25) * ((3.2 - 2.9) / 0.25);
    else right_bound_x = 3.2 - (p.y - 0.50) * ((3.2 - 2.9) / 0.25);
    
    // 3. HP 水平血條 (粗細減半, 脫鉤極限距離 0.1)
    float hp_intensity = 0.0;
    float hp_glow = 0.0;
    float bar_x_start = 0.95;
    
    for(int i=0; i<3; i++) {
        float y_top = 0.33 + float(i) * 0.08;
        float y_bot = y_top + 0.04; // 粗細為一半 (0.04)
        
        float bar_x_end = right_bound_x - 0.10; // 保留 0.1 的極限距離
        
        if(p.y > y_top && p.y < y_bot && p.x > bar_x_start && p.x < bar_x_end) {
            float fill_threshold = 1.0;
            if(i == 0) fill_threshold = clamp(hp_pct * 3.0, 0.0, 1.0);
            else if(i == 1) fill_threshold = clamp(hp_pct * 3.0 - 1.0, 0.0, 1.0);
            else fill_threshold = clamp(hp_pct * 3.0 - 2.0, 0.0, 1.0);
            
            float current_x_pct = (p.x - bar_x_start) / (bar_x_end - bar_x_start);
            float border = min(min(p.x - bar_x_start, bar_x_end - p.x), min(p.y - y_top, y_bot - p.y));
            
            if(border < line_thickness * 1.5) {
                hp_intensity += 1.0;
            } else if(current_x_pct < fill_threshold) {
                hp_intensity += 0.8;
                hp_glow += 0.5;
            } else {
                hp_intensity += 0.2;
            }
        }
    }
    
    // 4. AP 底部三角形陣列
    float ap_intensity = 0.0;
    float ap_y_top = 0.60;
    float ap_y_bot = 0.70;
    float ap_start = 0.95;
    float ap_width = 1.8;
    
    if (p.y > ap_y_top && p.y < ap_y_bot && p.x > ap_start && p.x < (ap_start + ap_width)) {
        float cell_w = ap_width / float(ap_max);
        float local_x = (p.x - ap_start) / cell_w;
        int index = int(floor(local_x));
        float fract_x = fract(local_x);
        
        float tri_y = (p.y - ap_y_top) / (ap_y_bot - ap_y_top);
        float tri_x = abs(fract_x - 0.5) * 2.0;
        
        if(tri_x < (1.0 - tri_y)) {
            float tri_border = (1.0 - tri_y) - tri_x;
            if(tri_border < 0.1 || p.y < (ap_y_top + 0.015)) {
                ap_intensity += 1.0;
            } else if(index < ap_current) {
                ap_intensity += 0.9;
                hp_glow += 0.5;
            } else {
                ap_intensity += 0.15;
            }
        }
    }
    
    float total_intensity = ring_intensity + frame_intensity + hp_intensity + ap_intensity;
    vec3 base_col = primary_color.rgb;
    
    if (glitch_intensity > 0.0 && total_intensity > 0.5) {
        base_col.r += sin(TIME * 25.0) * 0.2 * glitch_intensity;
        base_col.b += cos(TIME * 30.0) * 0.2 * glitch_intensity;
    }
    
    float glow = exp(-d_center * 2.0) * 0.1 + hp_glow * 0.5;
    col = base_col * clamp(total_intensity, 0.0, 1.0) + base_col * glow * glow_strength;
    alpha = clamp(total_intensity + glow, 0.0, 1.0) * primary_color.a;
    
    // 背景填充 (包含主體與上下文字模組)
    bool inside_main = p.x > 0.80 && p.x < right_bound_x && p.y > 0.25 && p.y < 0.75;
    bool inside_top = p.x > 1.25 && p.x < 2.70 && p.y > 0.10 && p.y <= 0.25;
    bool inside_bot = p.x > 1.30 && p.x < 2.20 && p.y >= 0.75 && p.y < 0.90;
    
    if((inside_main || inside_top || inside_bot) && total_intensity < 0.1) {
        col = mix(bg_panel_color.rgb, col, alpha);
        alpha = max(alpha, bg_panel_color.a);
    }
    
    COLOR = vec4(col, alpha);
}
