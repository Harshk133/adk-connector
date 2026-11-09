"""Build the 3D ADK Connectors logo in Blender.

Traces assets/adk-connector.png into separate named parts so the website can
animate each one, then exports a GLB, a .blend source file and a studio render.

Usage (from the repository root):
    blender -b --factory-startup -P website/model/build_logo.py
"""
import math
import os

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
ASSETS = os.path.join(SITE, "assets")

COLORS = {
    "blue": "4A88EF",
    "green": "3DA357",
    "red": "EB4537",
    "yellow": "FAAF08",
    "white": "F7F8FA",
    "fold": "C8D9E9",
}


def to_scene(x, y):
    """Convert logo pixel coordinates (500px canvas, y down) to scene units."""
    return (x - 250) / 100, (250 - y) / 100


def linear_rgba(hex_color):
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    return tuple(channel(int(hex_color[i : i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def make_material(name, hex_color, roughness=0.3, coat=0.7):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = linear_rgba(hex_color)
    shader.inputs["Metallic"].default_value = 0.0
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Coat Weight"].default_value = coat
    shader.inputs["Coat Roughness"].default_value = 0.12
    return material


def arc(cx, cy, radius, start_deg, end_deg, segments=28):
    return [
        (
            cx + radius * math.cos(math.radians(start_deg + (end_deg - start_deg) * i / segments)),
            cy + radius * math.sin(math.radians(start_deg + (end_deg - start_deg) * i / segments)),
        )
        for i in range(segments + 1)
    ]


def circle(cx, cy, radius, segments=40):
    return [
        (
            cx + radius * math.cos(2 * math.pi * i / segments),
            cy + radius * math.sin(2 * math.pi * i / segments),
        )
        for i in range(segments)
    ]


def stadium(left, right, cy, radius):
    return arc(left, cy, radius, 270, 90) + arc(right, cy, radius, 90, -90)


def round_corners(points, radii, segments=8):
    """Replace each hard corner with a smooth curve of roughly the given radius."""
    rounded = []
    count = len(points)
    for i, point in enumerate(points):
        p = Vector(point)
        before, after = Vector(points[i - 1]), Vector(points[(i + 1) % count])
        to_before, to_after = before - p, after - p
        angle = to_before.angle(to_after)
        distance = min(
            radii[i] / max(math.tan(angle / 2), 1e-3),
            to_before.length * 0.499,
            to_after.length * 0.499,
        )
        start = p + to_before.normalized() * distance
        end = p + to_after.normalized() * distance
        for step in range(segments + 1):
            t = step / segments
            curve_point = (1 - t) ** 2 * start + 2 * (1 - t) * t * p + t**2 * end
            rounded.append((curve_point.x, curve_point.y))
    return rounded


def chevron(start, apex, end, width, outer_radius=15, inner_radius=4):
    """Outline a three-point stroke with rounded caps."""
    a, b, c = Vector(start), Vector(apex), Vector(end)
    half = width / 2
    first, second = (b - a).normalized(), (c - b).normalized()
    normal_1 = Vector((-first.y, first.x))
    normal_2 = Vector((-second.y, second.x))
    miter = (normal_1 + normal_2).normalized()
    miter_length = half / max(miter.dot(normal_1), 1e-3)

    left = [a + normal_1 * half, b + miter * miter_length, c + normal_2 * half]
    right = [c - normal_2 * half, b - miter * miter_length, a - normal_1 * half]
    chord_middle = (a + c) / 2
    left_is_outer = (left[1] - chord_middle).length > (right[1] - chord_middle).length
    left_radius, right_radius = (
        (outer_radius, inner_radius) if left_is_outer else (inner_radius, outer_radius)
    )
    points = [tuple(p) for p in left + right]
    return round_corners(points, [half, left_radius, half, half, right_radius, half])


def build_part(name, outline, material, depth, z, parent, bevel=0.035, bevel_steps=4):
    scene_points = [to_scene(x, y) for x, y in outline]
    xs, ys = zip(*scene_points)
    center_x, center_y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2

    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "2D"
    curve.fill_mode = "BOTH"
    curve.resolution_u = 1
    curve.extrude = max(depth / 2 - bevel, 0)
    curve.bevel_depth = bevel
    curve.bevel_resolution = bevel_steps
    curve.offset = -bevel
    spline = curve.splines.new("POLY")
    spline.points.add(len(scene_points) - 1)
    for spline_point, (x, y) in zip(spline.points, scene_points):
        spline_point.co = (x - center_x, y - center_y, 0, 1)
    spline.use_cyclic_u = True

    curve_object = bpy.data.objects.new(f"{name}_curve", curve)
    bpy.context.collection.objects.link(curve_object)
    bpy.context.view_layer.update()
    evaluated = curve_object.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(evaluated)
    bpy.data.objects.remove(curve_object)
    bpy.data.curves.remove(curve)
    mesh.name = name

    geometry = bmesh.new()
    geometry.from_mesh(mesh)
    bmesh.ops.remove_doubles(geometry, verts=geometry.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(geometry, faces=geometry.faces)
    for face in geometry.faces:
        face.smooth = True
    # Keep flat caps crisp while the bevels and curved walls shade smoothly.
    for edge in geometry.edges:
        linked = edge.link_faces
        is_cap_edge = any(abs(f.normal.z) > 0.9995 for f in linked)
        too_sharp = len(linked) == 2 and linked[0].normal.angle(linked[1].normal, 0) > math.radians(35)
        edge.smooth = not (is_cap_edge or too_sharp)
    geometry.to_mesh(mesh)
    geometry.free()

    mesh.materials.append(material)
    part = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(part)
    part.parent = parent
    part.location = (center_x, center_y, z)
    return part


def ring_half(side):
    """One colored half of the capsule, split on the logo's vertical seam."""
    seam = 236
    outer_top, outer_bottom, inner_top, inner_bottom = 63, 270, 95, 238
    center_y = 166.5
    if side == "left":
        outer = arc(187.5, center_y, 103.5, 270, 90)
        inner = arc(184.5, center_y, 71.5, 90, 270)
    else:
        outer = arc(313.5, center_y, 103.5, 270, 450)
        # Skip arc points beside the seam: an edge shorter than the bevel folds the mesh.
        inner = [point for point in arc(231.5, center_y, 71.5, 90, -90) if point[0] > seam + 9]
    return (
        [(seam, outer_top)]
        + outer
        + [(seam, outer_bottom), (seam, inner_bottom)]
        + inner
        + [(seam, inner_top)]
    )


def build_logo():
    bpy.ops.wm.read_factory_settings(use_empty=True)

    materials = {name: make_material(f"logo_{name}", value) for name, value in COLORS.items()}
    root = bpy.data.objects.new("ADK_Logo", None)
    bpy.context.collection.objects.link(root)

    build_part("ring_blue", ring_half("left"), materials["blue"], 0.34, 0, root, 0.045, 5)
    build_part("ring_green", ring_half("right"), materials["green"], 0.34, 0, root, 0.045, 5)
    build_part("face", stadium(184.5, 231.5, 166.5, 70), materials["white"], 0.26, -0.02, root, 0.035, 4)
    build_part("eye_left", circle(161, 167, 18.5), materials["blue"], 0.11, 0.135, root, 0.05, 6)
    build_part("eye_right", circle(256, 167, 18.5), materials["blue"], 0.11, 0.135, root, 0.05, 6)

    plane_outline = [(401, 126), (384, 217), (345, 186), (385, 144), (332, 179), (304, 167)]
    build_part(
        "plane",
        round_corners(plane_outline, [6, 7, 1, 0.5, 1, 6], 6),
        materials["white"], 0.09, 0.215, root, 0.022, 3,
    )
    fold_outline = [(332, 179), (385, 144), (345, 186), (358, 199), (346, 211), (341, 210)]
    build_part(
        "plane_fold",
        round_corners(fold_outline, [1, 0.5, 1, 2, 4, 3], 6),
        materials["fold"], 0.05, 0.19, root, 0.012, 2,
    )

    bracket_outline = [
        (156, 293), (84, 293), (84, 437), (156, 437),
        (156, 406), (115, 406), (115, 324), (156, 324),
    ]
    build_part(
        "bracket",
        round_corners(bracket_outline, [15, 20, 20, 15, 15, 3, 3, 15], 10),
        materials["yellow"], 0.34, 0, root, 0.045, 5,
    )
    build_part(
        "chevron_left",
        chevron((248, 318), (193, 365), (248, 412), 34),
        materials["red"], 0.34, 0, root, 0.045, 5,
    )
    build_part(
        "chevron_right",
        chevron((347, 318), (402, 365), (347, 412), 34),
        materials["red"], 0.34, 0, root, 0.045, 5,
    )
    return root


def export_glb(path):
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_yup=False,
        export_apply=False,
        export_normals=True,
        export_tangents=False,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )


def add_area_light(name, location, power, size, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = power
    light.size = size
    light.color = color
    light_object = bpy.data.objects.new(name, light)
    bpy.context.collection.objects.link(light_object)
    light_object.location = location
    direction = Vector((0, 0, 0)) - Vector(location)
    light_object.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_studio_shot(root, path):
    scene = bpy.context.scene
    root.rotation_euler = (math.radians(9), math.radians(-24), math.radians(3))

    camera_data = bpy.data.cameras.new("camera")
    camera_data.lens = 85
    camera = bpy.data.objects.new("camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0, 0, 10.5)
    scene.camera = camera

    add_area_light("key", (-4, 5, 7), 900, 6)
    add_area_light("fill", (6, -1, 6), 260, 8, (0.8, 0.88, 1))
    add_area_light("rim", (3, 6, -4), 500, 5, (0.75, 0.85, 1))

    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.32, 0.36, 0.45, 1)
    scene.world = world

    scene.render.engine = "CYCLES"
    scene.cycles.samples = 96
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.film_transparent = True
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 1200
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    root.rotation_euler = (0, 0, 0)


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    logo = build_logo()
    export_glb(os.path.join(ASSETS, "adk-connector-logo.glb"))
    render_studio_shot(logo, os.path.join(ASSETS, "adk-connector-logo-render.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "adk-connector-logo.blend"))
    print("LOGO BUILD COMPLETE")
