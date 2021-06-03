# Example usage
#  blender --background [blend file] --python [script location]/batch_render_camera.py -- -c 1,2,4 -s 1 -e 120
# '--' causes blender to ignore all following arguments so python can use them.
#
# Python options
#  -c is a comma-separated list of camera indices to render. If the order gets messed up the output directory will use the camera's name from the blend file so it will be clear. If not set, all cameras are rendered.
#  -s is frame start for each camera. If not set the value from the blend file will be used.
#  -e is frame end for each camera. If not set the value from the blend file will be used.
#  -p is persistent data to improve time between frames at the cost of memory usage (requires blender 2.93)
# Overwrite options are mutually exclusive. If neither is set, the value from the Blend file will be used.
#  -o is overwrite. If set Blender will be overwrite existing frames.
#  -n is no overwrite. If set Blender will be set to skip existing frames.
#
# See blender --help for details.
#
# CHANGELOG
# Mishka#6218 2021-5-31: 
#   Initial creation of script with -c -s and -e options to batch render
# Mishka#6218 2021-6-2: 
#   Added -o and -n options to specify overwrite and changed options to be a static class instead of global variables
# Mishka#6218 2021-6-2:
#   Fixed bug that caused script not to work when given a single camera
# Mishka#6218 2021-6-3:
#   Added -p for persistent data function (new in blender 2.93)

import bpy
from operator import itemgetter

class Options(object):
    FrameStart = None
    FrameEnd = None
    AllFrames = True
    OverwriteSet = False
    Overwrite = True
    PersistentData = False

def render_with_camera(camera):
    print("Rendering with camera " + camera.name)
    
    scene = bpy.context.scene
    scene.camera = camera
    if not Options.AllFrames:
        if Options.FrameStart:
            scene.frame_start = Options.FrameStart
        if Options.FrameEnd:
            scene.frame_end = Options.FrameEnd

    render = scene.render
    
    # set overwrite option if specified by the user, otherwise use the value in the blend file
    if Options.OverwriteSet:
        render.use_overwrite = Options.Overwrite
        
    # If -p is used set persistent data, otherwise leave the default blend file value
    if Options.PersistentData:
        render.use_persistent_data = True

    filepath = render.filepath
    render_filename = filepath.split("\\")[-1]
    render_folder = "//" + get_blend_name_base() + '_' + camera.name + "\\" + render_filename

    render.use_file_extension = True
    render.filepath = render_folder
    
    bpy.ops.render.render(animation=True)

def get_cameras():
    bpy.ops.object.select_by_type(type="CAMERA")
    cam_objs = bpy.context.selected_objects
    print("Got all cameras: " + ', '.join([c.name for c in cam_objs]))

    return cam_objs

def do_render(camera_index_list):
    cams = get_cameras()
    active_cams = [cams[i] for i in camera_index_list]
    active_cam_names = [cam.name for cam in active_cams]
    print("Rendering with cameras: " + ", ".join(active_cam_names))
    for cam in active_cams:
        render_with_camera(cam)
        
def get_blend_name_base():
    blend_file_name = bpy.path.basename(bpy.data.filepath)
    return blend_file_name.split('.')[0]
    
def is_blender_293():
    bv = bpy.app.version
    return bv[0] >= 2 and bv[1] >= 3

def main():
    import sys       # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
        "Run blender in background mode with this script:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    # Example utility, add some text and renders or saves it (with options)
    # Possible types are: string, int, long, choice, float and complex.
    parser.add_argument(
        "-c", "--camera-list", dest="camera_list_1", type=str,
        help="Comma-separated list of 1-indexed integers for each camera view to be rendered",
    )
    parser.add_argument(
        "-s", "--frame-start", dest="frame_start", type=int,
        help="First frame to render for each camera",
    )
    parser.add_argument(
        "-e", "--frame-end", dest="frame_end", type=int,
        help="Last frame to render for each camera",
    )
    overwrite_args = parser.add_mutually_exclusive_group()
    overwrite_args.add_argument(
        "-o", "--overwrite", dest="overwrite", action="store_true", default=argparse.SUPPRESS,
        help="Set option to overwrite existing frames during rendering",
    )
    overwrite_args.add_argument(
        "-n", "--no-overwrite", dest="no_overwrite", action="store_false", default=argparse.SUPPRESS,
        help="Set option to skip existing frames during rendering",
    )
    parser.add_argument(
        "-p", "--persistent-data", dest="persistent_data", action="store_true",
        help="Set option to use persistent data between frames (only available in 2.93+ and will use more memory)",
    )

    args = parser.parse_args(argv)  # In this example we won't use the args

    camera_list_0 = []
    
    if not argv:
        parser.print_help()
        return
    
    # Persistent data is only available in blender 2.93 or later
    if args.persistent_data and is_blender_293():
        Options.persistent_data = args.persistent_data
    
    if args.frame_start or args.frame_end:
        Options.AllFrames = False
        if args.frame_start:
            Options.FrameStart = args.frame_start
        if args.frame_end:
            Options.FrameEnd = args.frame_end           
    
    # if the user doesn't specify to overwrite or not, use the value from the blend file
    if "no_overwrite" not in args and "overwrite" not in args:
        Options.OverwriteSet = False
    else:
        Options.OverwriteSet = True
        Options.Overwrite = "overwrite" in args     # we know at least one is set, so just check for overwrite existing in args
        
    if not args.camera_list_1:
        print("Error: --camera-list=\"1,2,5\" argument not given, aborting.")
        parser.print_help()
        return
    else:
        cl = []
        if ',' in args.camera_list_1:
            cl = args.camera_list_1.split(',')
        # case of only one camera passed in, make it a list
        else:
            cl = [args.camera_list_1]
        try:
            # camera list needs to be converted to int from string
            cl = [int(val) for val in cl]
        except ValueError:
            print("Error: --camera-list requires a comma-separated list of integers (no spaces)")
            parser.print_help()
            return
        # camera list needs to be zero-indexed internally
        camera_list_0 = [val-1 if val > 0 else 0 for val in cl]
        camera_list_0 = list(set(camera_list_0)) # remove duplicates

    # Run the renders for the selected cameras
    do_render(camera_list_0)

    print("batch job finished, exiting")


if __name__ == "__main__":
    main()