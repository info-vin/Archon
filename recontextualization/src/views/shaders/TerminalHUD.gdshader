shader_type canvas_item;

uniform vec4 bg_color : source_color = vec4(0.04, 0.08, 0.12, 0.9);
uniform vec4 border_color : source_color = vec4(0.0, 0.7, 1.0, 1.0);
uniform vec4 grid_color : source_color = vec4(0.0, 0.4, 0.6, 0.15);

void fragment() {
    vec2 uv = UV;
    vec4 col = bg_color;
    
    // Grid
    vec2 grid_uv = fract(uv * 20.0);
    float grid = smoothstep(0.03, 0.0, grid_uv.x) + smoothstep(0.97, 1.0, grid_uv.x) +
                 smoothstep(0.03, 0.0, grid_uv.y) + smoothstep(0.97, 1.0, grid_uv.y);
    col.rgb = mix(col.rgb, grid_color.rgb, clamp(grid, 0.0, 1.0) * grid_color.a);
    
    float elements = 0.0;
    float glow = 0.0;
    
    // Border logic with chamfered corners
    float border_w = 0.003; // Extremely thin to match PlayAreaHUD
    float cut_tl = 0.05; // Much smaller
    float cut_br = 0.12; // Smaller
    
    // Edges
    if (uv.y < border_w && uv.x > cut_tl && uv.x < 1.0) elements = 1.0; // Top
    if (uv.y > 1.0 - border_w && uv.x > 0.0 && uv.x < 1.0 - cut_br) elements = 1.0; // Bottom
    if (uv.x < border_w && uv.y > cut_tl && uv.y < 1.0) elements = 1.0; // Left
    if (uv.x > 1.0 - border_w && uv.y > 0.0 && uv.y < 1.0 - cut_br) elements = 1.0; // Right
    
    // Diagonal cuts
    float d_tl = abs(uv.x + uv.y - cut_tl);
    if (d_tl < border_w * 1.5 && uv.x < cut_tl && uv.y < cut_tl) elements = 1.0;
    
    float d_br = abs((1.0 - uv.x) + (1.0 - uv.y) - cut_br);
    if (d_br < border_w * 1.5 && uv.x > 1.0 - cut_br && uv.y > 1.0 - cut_br) elements = 1.0;
    
    // Bottom-right inner decoration block
    if ((1.0 - uv.x) + (1.0 - uv.y) < cut_br - 0.015 && uv.x > 1.0 - cut_br && uv.y > 1.0 - cut_br) {
        elements = max(elements, 0.4); // Semi-transparent blue block
    }
    // Add another parallel diagonal line at bottom right
    float d_br2 = abs((1.0 - uv.x) + (1.0 - uv.y) - (cut_br + 0.025));
    if (d_br2 < border_w * 1.0 && uv.x > 1.0 - cut_br - 0.025 && uv.y > 1.0 - cut_br - 0.025) elements = 1.0;
    
    // Top horizontal bars (Match reference: two bars, one long, one short, etc)
    if (uv.y > 0.05 && uv.y < 0.055 && uv.x > 0.25 && uv.x < 0.85) elements = 1.0; // Thinner bar
    if (uv.y > 0.08 && uv.y < 0.085 && uv.x > 0.6 && uv.x < 0.95) elements = 1.0; // Thinner bar
    if (uv.y > 0.11 && uv.y < 0.115 && uv.x > 0.65 && uv.x < 0.95) elements = 1.0; // Thinner bar
    
    // Bottom right vertical bars (Shorter and thinner)
    if (uv.y > 0.9 && uv.y < 0.95 && uv.x > 0.55 && uv.x < 0.75) {
        float bars = fract(uv.x * 100.0); // More bars, thinner
        if (bars < 0.2) elements = 1.0;
    }
    
    // Left vertical thin accent line (like in reference)
    if (uv.x > 0.04 && uv.x < 0.043 && uv.y > 0.15 && uv.y < 0.85) elements = 1.0; // Thinner line
    if (abs(uv.x - 0.0415) < 0.005 && uv.y > 0.3 && uv.y < 0.35) elements = 1.0; // Thinner blip
    
    // High brightness / bloom for Terminal
    vec3 glow_color = border_color.rgb * 3.0;
    col.rgb += glow_color * (elements * 0.5); // Stronger bloom
    
    col.rgb = mix(col.rgb, mix(glow_color, vec3(1.0), 0.5), clamp(elements, 0.0, 1.0));
    col.a = max(col.a, clamp(elements, 0.0, 1.0) * border_color.a);
    
    COLOR = col;
}
