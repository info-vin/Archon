import os

BASE_DIR = "/Users/vincenta/GoogleKwok022/Archon/recontextualization"
SHADERS_DIR = os.path.join(BASE_DIR, "src/views/shaders")
COMPONENTS_DIR = os.path.join(BASE_DIR, "src/views/components")

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# 1. Write Unified Shader
scifi_shader_content = """shader_type canvas_item;

// --- 參數 ---
uniform bool is_mirrored = false;
uniform float glitch_intensity : hint_range(0.0, 1.0) = 0.0;

uniform float purity_pct : hint_range(0.0, 1.0) = 0.5;
uniform float hp_pct : hint_range(0.0, 1.0) = 0.75;
uniform int ap_current = 2;
uniform int ap_max = 5;

uniform vec4 primary_color : source_color = vec4(0.0, 0.85, 1.0, 1.0);
uniform vec4 bg_panel_color : source_color = vec4(0.0, 0.1, 0.15, 0.6);
uniform float line_thickness = 0.004;
uniform float glow_strength = 2.0;
uniform float aspect_ratio = 3.0;

// SDF 數學函式庫
float sdCircle(vec2 p, float r) { return length(p) - r; }
float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}
float sdEqTriangle(vec2 p, float r) {
    const float k = sqrt(3.0);
    p.x = abs(p.x) - r;
    p.y = p.y + r / k;
    if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
    p.x -= clamp(p.x, -2.0 * r, 0.0);
    return -length(p) * sign(p.y);
}

void fragment() {
    vec2 uv = UV;
    
    // 鏡像翻轉
    if (is_mirrored) {
        uv.x = 1.0 - uv.x;
    }
    
    // 故障撕裂 (Glitch)
    if (glitch_intensity > 0.0) {
        uv.x += sin(uv.y * 50.0 + TIME * 10.0) * glitch_intensity * 0.05;
    }
    
    uv.x *= aspect_ratio;
    
    vec3 final_color = vec3(0.0);
    float final_alpha = 0.0;
    float dist_elements = 999.0;
    
    // 1. 左側(或反轉後右側)大圓環
    vec2 circle_pos = vec2(0.5, 0.5);
    float d_circle_outer = abs(sdCircle(uv - circle_pos, 0.4)) - line_thickness;
    
    float angle = atan(uv.y - circle_pos.y, uv.x - circle_pos.x);
    float normalized_angle = (angle + 3.14159) / (2.0 * 3.14159);
    float ring_progress = (normalized_angle <= purity_pct) ? 1.0 : 0.2;
    
    dist_elements = min(dist_elements, d_circle_outer);
    
    // 2. 斜角外框
    vec2 p1 = circle_pos + vec2(0.38, -0.3);
    vec2 p2 = p1 + vec2(1.2, 0.0);
    vec2 p3 = p2 + vec2(0.3, 0.3);
    vec2 p4 = p3 + vec2(0.4, 0.0);
    vec2 p5 = p4 + vec2(0.0, 0.6);
    vec2 p6 = p1 + vec2(0.0, 0.6);
    
    float d_border = sdSegment(uv, p1, p2);
    d_border = min(d_border, sdSegment(uv, p2, p3));
    d_border = min(d_border, sdSegment(uv, p3, p4));
    d_border = min(d_border, sdSegment(uv, p4, p5));
    d_border = min(d_border, sdSegment(uv, p5, p6));
    d_border = min(d_border, sdSegment(uv, p6, p1 + vec2(0.0, 0.6))); 
    d_border -= line_thickness;
    dist_elements = min(dist_elements, d_border);
    
    // 3. 水平條 (Player HP / Crisis HP)
    // 我們畫 3 條軌道，但根據 hp_pct 決定總體填充
    // 為了將 1.0 拆分成 3 段：
    vec2 hp_start_1 = p1 + vec2(0.1, 0.15);
    vec2 hp_end_1 = hp_start_1 + vec2(1.4, 0.0);
    vec2 hp_start_2 = hp_start_1 + vec2(0.0, 0.15);
    vec2 hp_end_2 = hp_start_2 + vec2(1.2, 0.0);
    vec2 hp_start_3 = hp_start_2 + vec2(0.0, 0.15);
    vec2 hp_end_3 = hp_start_3 + vec2(1.0, 0.0);
    
    float d_hp_track = sdSegment(uv, hp_start_1, hp_end_1) - 0.015;
    d_hp_track = min(d_hp_track, sdSegment(uv, hp_start_2, hp_end_2) - 0.015);
    d_hp_track = min(d_hp_track, sdSegment(uv, hp_start_3, hp_end_3) - 0.015);
    
    // 根據 hp_pct 填充 (0.0~0.33, 0.33~0.66, 0.66~1.0)
    float fill_1 = clamp(hp_pct * 3.0, 0.0, 1.0);
    float fill_2 = clamp(hp_pct * 3.0 - 1.0, 0.0, 1.0);
    float fill_3 = clamp(hp_pct * 3.0 - 2.0, 0.0, 1.0);
    
    float d_hp_fill = 999.0;
    if (fill_1 > 0.0) d_hp_fill = min(d_hp_fill, sdSegment(uv, hp_start_1, mix(hp_start_1, hp_end_1, fill_1)) - 0.015);
    if (fill_2 > 0.0) d_hp_fill = min(d_hp_fill, sdSegment(uv, hp_start_2, mix(hp_start_2, hp_end_2, fill_2)) - 0.015);
    if (fill_3 > 0.0) d_hp_fill = min(d_hp_fill, sdSegment(uv, hp_start_3, mix(hp_start_3, hp_end_3, fill_3)) - 0.015);
    
    // 4. AP 點數三角形 (或 SLA 倒數)
    vec2 ap_start = p6 + vec2(0.1, -0.15);
    float tri_spacing = 0.2;
    float d_ap_filled = 999.0;
    float d_ap_empty = 999.0;
    for(int i = 0; i < 10; i++) {
        if (i >= ap_max) break;
        vec2 pos = ap_start + vec2(float(i) * tri_spacing, 0.0);
        float d_tri = sdEqTriangle(uv - pos, 0.06);
        d_ap_empty = min(d_ap_empty, abs(d_tri) - (line_thickness * 1.5));
        if (i < ap_current) d_ap_filled = min(d_ap_filled, d_tri);
    }
    
    float aa = 0.005;
    float alpha_elements = 1.0 - smoothstep(0.0, aa, dist_elements);
    float alpha_hp_track = (1.0 - smoothstep(0.0, aa, d_hp_track)) * 0.3;
    float alpha_hp_fill = 1.0 - smoothstep(0.0, aa, d_hp_fill);
    float alpha_ap_empty = (1.0 - smoothstep(0.0, aa, d_ap_empty)) * 0.5;
    float alpha_ap_filled = 1.0 - smoothstep(0.0, aa, d_ap_filled);
    
    // Glitch Chromatic Aberration for fill
    vec3 base_col = primary_color.rgb;
    if (glitch_intensity > 0.0 && alpha_hp_fill > 0.0) {
        float r_offset = sin(TIME * 20.0) * 0.1 * glitch_intensity;
        float b_offset = cos(TIME * 25.0) * 0.1 * glitch_intensity;
        // Simulating chromatic aberration slightly
        base_col.r += r_offset;
        base_col.b += b_offset;
    }
    
    float glow = exp(-dist_elements * 30.0) * 0.5;
    glow += exp(-d_hp_fill * 25.0) * 0.4;
    glow += exp(-d_ap_filled * 40.0) * 0.6;
    
    float total_intensity = alpha_elements + alpha_hp_track + alpha_hp_fill + alpha_ap_empty + alpha_ap_filled;
    final_color = base_col * total_intensity + base_col * glow * glow_strength;
    final_alpha = clamp(total_intensity + glow, 0.0, 1.0) * primary_color.a;
    
    if (uv.x > circle_pos.x && uv.x < p4.x && uv.y > p1.y && uv.y < p5.y) {
        final_color = mix(bg_panel_color.rgb, final_color, final_alpha);
        final_alpha = max(final_alpha, bg_panel_color.a);
    }
    COLOR = vec4(final_color, final_alpha);
}
"""
write_file(os.path.join(SHADERS_DIR, "SciFiHUD.gdshader"), scifi_shader_content)

# Delete old shader if exists
old_shader = os.path.join(SHADERS_DIR, "PlayerStatusHUD.gdshader")
if os.path.exists(old_shader):
    os.remove(old_shader)

# 2. PlayerStatusHUD.tscn
player_hud_content = """[gd_scene load_steps=5 format=3]

[ext_resource type="Shader" path="res://src/views/shaders/SciFiHUD.gdshader" id="1_shader"]

[sub_resource type="ShaderMaterial" id="ShaderMaterial_player"]
shader = ExtResource("1_shader")
shader_parameter/is_mirrored = false
shader_parameter/glitch_intensity = 0.0
shader_parameter/purity_pct = 1.0
shader_parameter/hp_pct = 1.0
shader_parameter/ap_current = 10
shader_parameter/ap_max = 10
shader_parameter/primary_color = Color(0, 0.85, 1, 1)
shader_parameter/bg_panel_color = Color(0, 0.1, 0.15, 0.6)
shader_parameter/line_thickness = 0.004
shader_parameter/glow_strength = 2.0
shader_parameter/aspect_ratio = 3.0

[sub_resource type="SystemFont" id="SystemFont_ui"]
font_names = PackedStringArray("Monospace")
font_weight = 700

[node name="PlayerStatusHUD" type="Control"]
custom_minimum_size = Vector2(300, 100)
layout_mode = 3
anchors_preset = 0
offset_right = 300.0
offset_bottom = 100.0

[node name="ShaderRect" type="ColorRect" parent="."]
material = SubResource("ShaderMaterial_player")
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2

[node name="PurityLabel" type="Label" parent="."]
layout_mode = 0
offset_left = 13.0
offset_top = 31.0
offset_right = 87.0
offset_bottom = 69.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 24
text = "100%"
horizontal_alignment = 1
vertical_alignment = 1

[node name="RankLabel" type="Label" parent="."]
layout_mode = 0
offset_left = 138.0
offset_top = -2.0
offset_right = 288.0
offset_bottom = 21.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 14
text = "L3 ARCHITECT"
horizontal_alignment = 2
vertical_alignment = 1

[node name="APLabel" type="Label" parent="."]
layout_mode = 0
offset_left = 142.0
offset_top = 79.0
offset_right = 265.0
offset_bottom = 102.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 12
text = "10 / 10"
vertical_alignment = 1
"""
write_file(os.path.join(COMPONENTS_DIR, "PlayerStatusHUD.tscn"), player_hud_content)

# 3. EnemyThreatHUD.tscn
enemy_hud_content = """[gd_scene load_steps=5 format=3]

[ext_resource type="Shader" path="res://src/views/shaders/SciFiHUD.gdshader" id="1_shader"]

[sub_resource type="ShaderMaterial" id="ShaderMaterial_enemy"]
shader = ExtResource("1_shader")
shader_parameter/is_mirrored = true
shader_parameter/glitch_intensity = 0.0
shader_parameter/purity_pct = 0.0
shader_parameter/hp_pct = 1.0
shader_parameter/ap_current = 5
shader_parameter/ap_max = 5
shader_parameter/primary_color = Color(1, 0.0, 0.2, 1)
shader_parameter/bg_panel_color = Color(0.15, 0.0, 0.05, 0.6)
shader_parameter/line_thickness = 0.004
shader_parameter/glow_strength = 2.0
shader_parameter/aspect_ratio = 3.0

[sub_resource type="SystemFont" id="SystemFont_ui"]
font_names = PackedStringArray("Monospace")
font_weight = 700

[node name="EnemyThreatHUD" type="Control"]
custom_minimum_size = Vector2(300, 100)
layout_mode = 3
anchors_preset = 0
offset_right = 300.0
offset_bottom = 100.0

[node name="ShaderRect" type="ColorRect" parent="."]
material = SubResource("ShaderMaterial_enemy")
layout_mode = 1
anchors_preset = 15
anchor_right = 1.0
anchor_bottom = 1.0
grow_horizontal = 2
grow_vertical = 2

[node name="PoisonLabel" type="Label" parent="."]
layout_mode = 0
offset_left = 213.0
offset_top = 31.0
offset_right = 287.0
offset_bottom = 69.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 24
text = "0%"
horizontal_alignment = 1
vertical_alignment = 1

[node name="RateLimitLabel" type="Label" parent="."]
layout_mode = 0
offset_left = 12.0
offset_top = -2.0
offset_right = 162.0
offset_bottom = 21.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 14
text = "[ SYSTEM STABLE ]"
vertical_alignment = 1

[node name="SLALabel" type="Label" parent="."]
layout_mode = 0
offset_left = 30.0
offset_top = 79.0
offset_right = 153.0
offset_bottom = 102.0
theme_override_fonts/font = SubResource("SystemFont_ui")
theme_override_font_sizes/font_size = 12
text = "[SLA] 05:00"
horizontal_alignment = 2
vertical_alignment = 1
"""
write_file(os.path.join(COMPONENTS_DIR, "EnemyThreatHUD.tscn"), enemy_hud_content)

print("HUD scenes and shaders generated successfully.")
