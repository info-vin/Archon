shader_type canvas_item;

// The ratio of the corner to be cut off (0.0 to 0.5)
uniform float chamfer_ratio : hint_range(0.0, 0.5) = 0.18;

void fragment() {
    // Basic texture read
    vec4 color = texture(TEXTURE, UV);
    
    // Discard logic for the 4 corners
    bool cut = false;
    
    // Top-Left corner
    if (UV.x < chamfer_ratio && UV.y < chamfer_ratio) {
        if (UV.x + UV.y < chamfer_ratio) {
            cut = true;
        }
    }
    // Top-Right corner
    else if (UV.x > 1.0 - chamfer_ratio && UV.y < chamfer_ratio) {
        if ((1.0 - UV.x) + UV.y < chamfer_ratio) {
            cut = true;
        }
    }
    // Bottom-Left corner
    else if (UV.x < chamfer_ratio && UV.y > 1.0 - chamfer_ratio) {
        if (UV.x + (1.0 - UV.y) < chamfer_ratio) {
            cut = true;
        }
    }
    // Bottom-Right corner
    else if (UV.x > 1.0 - chamfer_ratio && UV.y > 1.0 - chamfer_ratio) {
        if ((1.0 - UV.x) + (1.0 - UV.y) < chamfer_ratio) {
            cut = true;
        }
    }
    
    // Apply discard or original alpha
    if (cut) {
        COLOR = vec4(0.0);
    } else {
        COLOR = color;
    }
}
