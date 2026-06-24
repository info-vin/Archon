@tool
extends SceneTree

func _init():
    print("Building HD-2D MeshLibrary from Isometric Assets...")
    
    var mesh_lib = MeshLibrary.new()
    var asset_dir = "res://Assets/Rooms/isometric/"
    var files = ["floor_tile.png", "wall_corner_SW.png", "desk_SW.png", "chair_SW.png", "server_rack_SW.png", "sofa_SW.png"]
    
    var item_id = 0
    for file in files:
        var tex_path = asset_dir + file
        var tex = load(tex_path)
        if not tex:
            print("Failed to load texture: ", tex_path)
            continue
            
        var mat = StandardMaterial3D.new()
        mat.albedo_texture = tex
        mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
        mat.alpha_scissor_threshold = 0.1
        mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST # Pixel art style
        
        # Billboard mode so the pre-rendered isometric sprites face the camera directly
        mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
        mat.billboard_keep_scale = true
        
        # Create a QuadMesh to hold the texture
        var quad = QuadMesh.new()
        # Scale the quad according to texture size (assuming 1 unit = 64 pixels)
        var size_x = tex.get_width() / 64.0
        var size_y = tex.get_height() / 64.0
        quad.size = Vector2(size_x, size_y)
        quad.material = mat
        
        mesh_lib.create_item(item_id)
        mesh_lib.set_item_mesh(item_id, quad)
        mesh_lib.set_item_name(item_id, file.replace(".png", ""))
        
        print("Added item: ", file, " with ID ", item_id)
        item_id += 1

    # Save the MeshLibrary
    var save_path = "res://Assets/Rooms/isometric/HD2D_MeshLibrary.tres"
    var err = ResourceSaver.save(mesh_lib, save_path)
    if err == OK:
        print("Successfully saved MeshLibrary to ", save_path)
    else:
        print("Failed to save MeshLibrary! Error: ", err)
        
    quit()
