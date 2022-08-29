import os
from videoprops import get_video_properties
from math import sqrt

convertedFolder = '/home/neutron/Pictures/converted'
downscaledFolder = '/home/neutron/Pictures/downscaled'
sourceFolder = '/home/neutron/Pictures/source/'


def split(filename):
    return '.'.join(filename.split('.')[:-1]), filename.split('.')[-1].lower()

def is_image(filename):
    return split(filename)[-1] in ['arw', 'cr2', 'dng', 'gpr', 'nef', 'jpg', 'jpeg', 'png', 'heic']

def is_video(filename):
    return split(filename)[-1] in ['avi', 'mov', 'mpg', 'mp4']

def is_raw(filename):
    return split(filename)[-1] in ['arw', 'cr2', 'dng', 'gpr', 'nef']

def is_jpg(filename):
    return split(filename)[-1] in ['jpg', 'jpeg']

def is_png(filename):
    return split(filename)[-1] == 'png'
    
def is_heif(filename):
    return split(filename)[-1] == 'heic'

def new_filename(foldername, filename, number, extension):
    date = foldername[:10].replace(' ', '')
    prefix = ''
    if is_image(filename):
        prefix = 'IMG'
    elif is_video(filename):
        prefix = 'VID'
    return prefix + date + "_" + str(number).zfill(6) + '.' + extension

sourced = lambda foldername, filename: os.path.join(sourceFolder, foldername, filename)
converted = lambda foldername, filename: os.path.join(convertedFolder, foldername, filename)
downscaled = lambda foldername, filename: os.path.join(downscaledFolder, foldername, filename)

def copy(source, destination):
    os.system('cp "' + source + '" "' + destination + '"')

def delete(path):
    os.system('rm "' + path + '"')

def convert_raw_to_dng(source, destination):
    if split(source)[-1] == 'dng':
        copy(source, destination)
    else:
        os.system('dnglab convert "' + source + '" "' + destination + '"')

def convert_heif_to_png(source, destination):
    os.system('heif-convert -q 100 "' + source + '" "' + destination + '"')

def convert_video(source, destination):
    os.system('ffmpeg -n -hwaccel auto -i "{}" -c:v hevc_nvenc -rc constqp -qp 24 -b:v 0K -c:a aac -b:a 384k -vf yadif "{}"'.format(
        source, destination
    ))

def convert(foldername, filename, number):
    if is_video(filename):
        convert_video(sourced(foldername, filename), converted(foldername, new_filename(foldername, filename, number, 'mp4')))
    elif is_raw(filename):
        convert_raw_to_dng(sourced(foldername, filename), converted(foldername, new_filename(foldername, filename, number, 'dng')))
    elif is_jpg(filename):
        copy(sourced(foldername, filename), converted(foldername, new_filename(foldername, filename, number, 'jpg')))
    elif is_png(filename):
        copy(sourced(foldername, filename), converted(foldername, new_filename(foldername, filename, number, 'png')))
    elif is_heif(filename):
        convert_heif_to_png(sourced(foldername, filename), converted(foldername, new_filename(foldername, filename, number, 'png')))

def downscale_dng(source, destination):
    os.system('dcraw -c -w "' + source + '" | convert - -resize "2073600@>" "' + destination + '"')

def downscale_jpg_png(source, destination):
    os.system('convert -quality 88 -resize "2073600@>" "' + source + '" "' + destination + '"')

def downscale_video(source, destination):
    props = get_video_properties(os.path.join(sourceFolder, foldername, filename))
    width = int(props['width'])
    height = int(props['height'])
    scaling = sqrt(2073600 / (width * height))
    if scaling < 1:
        width *= scaling
        height *= scaling
    if 'tags' in props.keys():
        if 'rotate' in props['tags'].keys():
            if props['tags']['rotate'] == '90':
                width, height = height, width
    framerate = min(30, int(props['nb_frames']) / float(props['duration']))   
    os.system('ffmpeg -n -hwaccel auto -i "{}" -c:v hevc_nvenc -rc constqp -qp 30 -b:v 0K -c:a aac -b:a 384k -vf yadif=1,scale={}:{} -r {} "{}"'.format(
        source,
        width,
        height,
        framerate,
        destination
    ))

def downscale(foldername, filename, number):
    if is_video(filename):
        downscale_video(sourced(foldername, filename), downscaled(foldername, new_filename(foldername, filename, number, 'mp4')))
    elif is_raw(filename):
        downscale_dng(converted(foldername, new_filename(foldername, filename, number, 'dng')), downscaled(foldername, new_filename(foldername, filename, number, 'jpg')))
    elif is_jpg(filename):
        downscale_jpg_png(sourced(foldername, filename), downscaled(foldername, new_filename(foldername, filename, number, 'jpg')))
    elif is_png(filename):
        downscale_jpg_png(sourced(foldername, filename), downscaled(foldername, new_filename(foldername, filename, number, 'jpg')))
    elif is_heif(filename):
        downscale_jpg_png(converted(foldername, new_filename(foldername, filename, number, 'png')), downscaled(foldername, new_filename(foldername, filename, number, 'jpg')))

if not os.path.exists(os.path.join(downscaledFolder)):
    os.mkdir(os.path.join(downscaledFolder))

if not os.path.exists(os.path.join(convertedFolder)):
    os.mkdir(os.path.join(convertedFolder))

for foldername in os.listdir(os.path.join(sourceFolder)):
    if not os.path.exists(os.path.join(convertedFolder, foldername)):
        os.mkdir(os.path.join(convertedFolder, foldername))
    if not os.path.exists(os.path.join(downscaledFolder, foldername)):
        os.mkdir(os.path.join(downscaledFolder, foldername))
    img = 1
    vid = 1
    images_done = dict()
    for filename in os.listdir(os.path.join(sourceFolder, foldername)):
        if is_image(filename):
            if (data := images_done.get(split(filename)[0])):
                if is_raw(data.get('ext')):
                    delete(downscaled(foldername, new_filename(foldername, filename, data.get('number'), 'jpg')))
                    downscale(foldername, filename, data.get('number'))
                elif is_raw(split(filename)[-1]):
                    delete(converted(foldername, new_filename(foldername, filename, data.get('number'), 'jpg')))
                    convert(foldername, filename, data.get('number'))
            else:
                convert(foldername, filename, img)
                downscale(foldername, filename, img)
                images_done[split(filename)[0]] = {'number': img, 'ext': split(filename)[-1]}
                img += 1
        elif is_video(filename):
            convert(foldername, filename, vid)
            downscale(foldername, filename, vid)
            vid += 1
