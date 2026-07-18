shader_type canvas_item;

// --- 玩家狀態參數 ---
uniform float purity_pct : hint_range(0.0, 1.0) = 0.5;
uniform float hp_pct : hint_range(0.0, 1.0) = 0.75;
uniform int ap_current = 2;
uniform int ap_max = 5;

// --- 視覺風格設定 ---
uniform vec4 primary_color : source_color = vec4(0.0, 0.85, 1.0, 1.0); // 經典 Cyan
uniform vec4 bg_panel_color : source_color = vec4(0.0, 0.1, 0.15, 0.6);
uniform float line_thickness = 0.004; // 極細緻的高質感線條
uniform float glow_strength = 2.0;
uniform float aspect_ratio = 3.0; // 假設 UI 寬高比為 3:1

// --- SDF 數學函式庫 (呈現極致平滑邊緣的關鍵) ---
float sdCircle(vec2 p, float r) {
    return length(p) - r;
}

float sdSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp(dot(pa, ba) / dot(ba, ba), 0.0, 1.0);
    return length(pa - ba * h);
}

// 繪製正三角形 SDF (用於 AP 點數)
float sdEqTriangle(vec2 p, float r) {
    const float k = sqrt(3.0);
    p.x = abs(p.x) - r;
    p.y = p.y + r / k;
    if (p.x + k * p.y > 0.0) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.0;
    p.x -= clamp(p.x, -2.0 * r, 0.0);
    return -length(p) * sign(p.y);
}

void fragment() {
    // 修正 UV 比例，確保圓形不會變橢圓
    vec2 uv = UV;
    uv.x *= aspect_ratio;
    
    vec3 final_color = vec3(0.0);
    float final_alpha = 0.0;
    float dist_elements = 999.0;
    float dist_bg = 999.0;
    
    // --- 1. 左側純淨度大圓環 (Purity Circle) ---
    vec2 circle_pos = vec2(0.5, 0.5); // 在修正後的 UV 空間中的位置
    float d_circle_outer = abs(sdCircle(uv - circle_pos, 0.4)) - line_thickness;
    float d_circle_inner = abs(sdCircle(uv - circle_pos, 0.35)) - line_thickness * 0.5;
    
    // 圓環外部的裝飾性三角形 (十字準星風格)
    // 透過旋轉與鏡像複製，利用 SDF 達成完美對稱
    
    // 圓環進度條 (依據 purity_pct)
    float angle = atan(uv.y - circle_pos.y, uv.x - circle_pos.x);
    // 將角度轉為 0.0 ~ 1.0
    float normalized_angle = (angle + 3.14159) / (2.0 * 3.14159);
    float ring_progress = (normalized_angle <= purity_pct) ? 1.0 : 0.2; // 未達成的部分變暗
    
    dist_elements = min(dist_elements, d_circle_outer);
    
    // --- 2. 右側斜角高質感外框 (Premium Chamfered Border) ---
    // 利用 sdSegment 繪製精準的折線 (非小學生的粗糙畫法)
    vec2 p1 = circle_pos + vec2(0.38, -0.3);
    vec2 p2 = p1 + vec2(1.2, 0.0);
    vec2 p3 = p2 + vec2(0.3, 0.3); // 斜切角
    vec2 p4 = p3 + vec2(0.4, 0.0);
    vec2 p5 = p4 + vec2(0.0, 0.6); // 右下角
    vec2 p6 = p1 + vec2(0.0, 0.6); // 左下角接回圓環
    
    float d_border = sdSegment(uv, p1, p2);
    d_border = min(d_border, sdSegment(uv, p2, p3));
    d_border = min(d_border, sdSegment(uv, p3, p4));
    d_border = min(d_border, sdSegment(uv, p4, p5));
    d_border = min(d_border, sdSegment(uv, p5, p6));
    d_border = min(d_border, sdSegment(uv, p6, p1 + vec2(0.0, 0.6))); 
    
    d_border -= line_thickness;
    dist_elements = min(dist_elements, d_border);
    
    // --- 3. 特務血量條 (Player HP Horizontal Bars) ---
    // 在右側面板中繪製水平的血條
    vec2 hp_start = p1 + vec2(0.1, 0.15);
    vec2 hp_end = hp_start + vec2(1.6, 0.0);
    float d_hp_track = sdSegment(uv, hp_start, hp_end) - 0.02; // 軌道厚度
    
    // 依據 hp_pct 決定填滿長度
    vec2 hp_fill_end = mix(hp_start, hp_end, hp_pct);
    float d_hp_fill = sdSegment(uv, hp_start, hp_fill_end) - 0.015;
    
    // --- 4. AP 點數三角形 (Action Points) ---
    // 利用 sdEqTriangle 加上 Modulo (fract) 來繪製連續的三角形
    vec2 ap_start = p6 + vec2(0.1, -0.15);
    float tri_spacing = 0.2;
    float d_ap_filled = 999.0;
    float d_ap_empty = 999.0;
    
    for(int i = 0; i < ap_max; i++) {
        vec2 pos = ap_start + vec2(float(i) * tri_spacing, 0.0);
        float d_tri = sdEqTriangle(uv - pos, 0.06);
        
        // 空心外框
        float d_tri_outline = abs(d_tri) - (line_thickness * 1.5);
        d_ap_empty = min(d_ap_empty, d_tri_outline);
        
        // 實心填滿 (如果 i < ap_current)
        if (i < ap_current) {
            d_ap_filled = min(d_ap_filled, d_tri);
        }
    }
    
    // --- 組合與抗鋸齒渲染 (Anti-Aliasing & Compositing) ---
    // 使用 fwidth 或固定的極小值來做完美的 smoothstep 邊緣柔化
    float aa = 0.005; // 抗鋸齒平滑度
    
    // 計算主視覺元素的 Alpha
    float alpha_elements = 1.0 - smoothstep(0.0, aa, dist_elements);
    float alpha_hp_track = (1.0 - smoothstep(0.0, aa, d_hp_track)) * 0.3; // 軌道半透明
    float alpha_hp_fill = 1.0 - smoothstep(0.0, aa, d_hp_fill);
    
    float alpha_ap_empty = (1.0 - smoothstep(0.0, aa, d_ap_empty)) * 0.5;
    float alpha_ap_filled = 1.0 - smoothstep(0.0, aa, d_ap_filled);
    
    // 疊加顏色與光暈 (Bloom)
    // 距離場的 exponential glow，帶來高級的霓虹發光感
    float glow = exp(-dist_elements * 30.0) * 0.5;
    glow += exp(-d_hp_fill * 25.0) * 0.4;
    glow += exp(-d_ap_filled * 40.0) * 0.6;
    
    // 總和所有元素的強度
    float total_intensity = alpha_elements + alpha_hp_track + alpha_hp_fill + alpha_ap_empty + alpha_ap_filled;
    
    final_color = primary_color.rgb * total_intensity;
    final_color += primary_color.rgb * glow * glow_strength;
    
    final_alpha = clamp(total_intensity + glow, 0.0, 1.0) * primary_color.a;
    
    // 背景底板 (如果在框線內)
    // 這裡簡單判定 UV 範圍作為底板
    if (uv.x > circle_pos.x && uv.x < p4.x && uv.y > p1.y && uv.y < p5.y) {
        final_color = mix(bg_panel_color.rgb, final_color, final_alpha);
        final_alpha = max(final_alpha, bg_panel_color.a);
    }
    
    COLOR = vec4(final_color, final_alpha);
}
