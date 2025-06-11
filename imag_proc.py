from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import os

def difference_of_gaussian(image, sigma1=1, sigma2=2):
    """
    Apply Difference of Gaussian (DoG) to an image.
    This function applies two Gaussian blurs with different standard deviations
    and subtracts the second from the first to enhance edges.
    The result is clipped to ensure pixel values remain in the valid range [0, 255].
    Args:
        image (PIL.Image): Input image.
        sigma1 (float): Standard deviation for the first Gaussian.
        sigma2 (float): Standard deviation for the second Gaussian.
    Returns:
        PIL.Image: Image after applying DoG.
    """
    img_blur1 = image.filter(ImageFilter.GaussianBlur(radius=sigma1))
    img_blur2 = image.filter(ImageFilter.GaussianBlur(radius=sigma2))
    dog_image = Image.fromarray(
        np.clip(np.array(img_blur1, dtype=np.int16) - np.array(img_blur2, dtype=np.int16) + 128, 0, 255).astype(np.uint8)
    )
    return dog_image

def  sobel_edge_detection(image, border_size=1):
    """
    Apply Sobel edge detection to an image.
    Returns both angle and magnitude images.
    """
    sobel_x = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, 0, 1,
                -2, 0, 2,
                -1, 0, 1],
        scale=1
    )
    sobel_y = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, -2, -1,
                0,  0,  0,
                1,  2,  1],
        scale=1
    )
    img_x = image.filter(sobel_x)
    img_y = image.filter(sobel_y)
    arr_x = np.array(img_x, dtype=np.float32)[border_size:-border_size, border_size:-border_size]
    arr_y = np.array(img_y, dtype=np.float32)[border_size:-border_size, border_size:-border_size]

    # Compute magnitude and angle
    magnitude = np.sqrt(arr_x ** 2 + arr_y ** 2)
    angle = np.arctan2(arr_y, arr_x)  # range [-pi, pi]
    # Normalize for image output
    angle_normalized = ((angle + np.pi) / (2 * np.pi)) * 255  # map to [0, 255]
    angle_img = Image.fromarray(angle_normalized.astype(np.uint8), mode="L")
    mag_img = Image.fromarray(np.clip(magnitude, 0, 255).astype(np.uint8), mode="L")
    return angle_img, mag_img

def sobel_edge_rgb(image, border_size=1):
    """
    Apply Sobel edge detection to an image.
    Returns an RGB image where:
      - Red channel is the normalized X component
      - Green channel is the normalized Y component
      - Blue channel is the normalized magnitude
    """
    sobel_x = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, 0, 1,
                -2, 0, 2,
                -1, 0, 1],
        scale=1
    )
    sobel_y = ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, -2, -1,
                0,  0,  0,
                1,  2,  1],
        scale=1
    )
    img_x = image.filter(sobel_x)
    img_y = image.filter(sobel_y)
    arr_x = np.array(img_x, dtype=np.float32)[border_size:-border_size, border_size:-border_size]
    arr_y = np.array(img_y, dtype=np.float32)[border_size:-border_size, border_size:-border_size]

    # Normalize X and Y to [0, 255]
    arr_x_norm = ((arr_x - arr_x.min()) / (np.ptp(arr_x) + 1e-8) * 255).astype(np.uint8)
    arr_y_norm = ((arr_y - arr_y.min()) / (np.ptp(arr_y) + 1e-8) * 255).astype(np.uint8)
    magnitude = np.sqrt(arr_x ** 2 + arr_y ** 2)
    mag_norm = (np.clip(magnitude / (magnitude.max() + 1e-8), 0, 1) * 255).astype(np.uint8)

    rgb = np.stack([arr_x_norm, arr_y_norm, mag_norm], axis=-1)
    rgb_img = Image.fromarray(rgb, mode="RGB")
    return rgb_img

def image_to_ascii_pillow(image_path, width=40):
    """
    Convert an image to ASCII art using Pillow.
    Args:
        image_path (str): Path to the image file.
        width (int): Desired width of ASCII output.
    Returns:
        str: ASCII art string.
    """
    ASCII_CHARS = " .:-=+*#%@░▒▓█"
    EDGE_THRESHOLD = 0.3

    # Get terminal size and set max width/height
    try:
        term_size = os.get_terminal_size()
        max_width = term_size.columns - 4 if term_size.columns > 10 else 30
        max_height = term_size.lines - 18 if term_size.lines > 20 else 10
    except Exception:
        max_width = 30
        max_height = 10

    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(background, img).convert("RGB")
    else:
        img = img.convert("RGB")
    # Open image to get aspect ratio
    img = img.convert("L")

    aspect_ratio = img.height / img.width

    # Calculate width and height to fit terminal and maintain aspect ratio
    # ASCII characters are taller than wide, so adjust aspect ratio
    char_aspect = 0.5  # typical ASCII char height/width ratio
    # First, try to fit width
    fit_height = int(max_width * aspect_ratio * char_aspect)
    if fit_height <= max_height:
        width = max_width
        height = fit_height
    else:
        height = max_height
        width = int(max_height / (aspect_ratio * char_aspect))
    width = max(1, width)
    height = max(1, height)

    try:
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        img_dog = difference_of_gaussian(img, sigma1=1, sigma2=2)
        border_size = 1
        img_dog_bordered = Image.new("L", (img_dog.width + 2 * border_size, img_dog.height + 2 * border_size), 128)
        img_dog_bordered.paste(img_dog, (border_size, border_size))
        img_dog_bordered.save("1_dog_bordered.png")

        # Use the new sobel_edge_rgb function
        sobel_rgb_img = sobel_edge_rgb(img_dog_bordered, border_size=border_size)
        sobel_rgb_img.save("2_sobel_rgb.png")
        # resize by majority color
        sobel_rgb_img = sobel_rgb_img.resize((width, height), Image.Resampling.LANCZOS)
        sobel_rgb_img.save("3_sobel_rgb_resize.png")

        # Resize the original image to match the output size for ASCII background
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
        arr_gray = np.array(img_resized)
        arr_angle = np.array(sobel_rgb_img)
        
        arr_x = arr_angle[:, :, 0].astype(np.float32)  # Red channel
        arr_y = arr_angle[:, :, 1].astype(np.float32)  # Green channel
        magnitude = arr_angle[:, :, 2].astype(np.float32)  # Blue channel

        ascii_str = ""
        for y in range(height):
            for x in range(width):
                mag = magnitude[y, x] / (magnitude.max() + 1e-8)
                angle = np.arctan2(arr_y[y, x], arr_x[y, x])
                if mag > EDGE_THRESHOLD:
                    if (-np.pi/8 <= angle < np.pi/8):
                        edge_char = '|'
                    elif (np.pi/8 <= angle < 3*np.pi/8):
                        edge_char = '\\'
                    elif (3*np.pi/8 <= angle < 5*np.pi/8) or (-5*np.pi/8 <= angle < -3*np.pi/8):
                        edge_char = '-'
                    elif (-3*np.pi/8 <= angle < -np.pi/8):
                        edge_char = '/'
                    else:
                        edge_char = ' '
                    ascii_str += edge_char
                else:
                    idx = int(arr_gray[y, x] / 255 * (len(ASCII_CHARS) - 1))
                    idx = max(0, min(idx, len(ASCII_CHARS) - 1))
                    ascii_str += ASCII_CHARS[idx]
            ascii_str += "\n"
        return ascii_str
    except Exception as e:
        return f"[ASCII conversion error: {e}]"

from rich.text import Text

def image_to_ascii_colored(image_path, in_width=40):
    # ... codice simile a image_to_ascii_pillow ...

    ASCII_CHARS = " .:-=+*#%@░▒▓█"
    EDGE_THRESHOLD = 0.25

    # Get terminal size and set max width/height
    try:
        term_size = os.get_terminal_size()
        max_width = term_size.columns - 4 if term_size.columns > 10 else 30
        max_width = min(max_width, in_width)
        max_height = term_size.lines - 18 if term_size.lines > 20 else 10
    except Exception:
        max_width = 30
        max_height = 10

    max_width = min(max_width, in_width)

    # Open image to get aspect ratio
    # img_backup = Image.open(image_path).convert("RGB")

    from PIL import ImageOps

    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(background, img).convert("RGB")
    else:
        img = img.convert("RGB")

    img_backup = img
    img = img.convert("L")
    aspect_ratio = img.height / img.width

    # Calculate width and height to fit terminal and maintain aspect ratio
    # ASCII characters are taller than wide, so adjust aspect ratio
    char_aspect = 0.5  # typical ASCII char height/width ratio
    # First, try to fit width
    fit_height = int(max_width * aspect_ratio * char_aspect)
    if fit_height <= max_height:
        width = max_width
        height = fit_height
    else:
        height = max_height
        width = int(max_height / (aspect_ratio * char_aspect))
    width = max(1, width)
    height = max(1, height)

    try:
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        img_dog = difference_of_gaussian(img, sigma1=1, sigma2=2)
        border_size = 1
        img_dog_bordered = Image.new("L", (img_dog.width + 2 * border_size, img_dog.height + 2 * border_size), 128)
        img_dog_bordered.paste(img_dog, (border_size, border_size))
        img_dog_bordered.save("1_dog_bordered.png")

        # Use the new sobel_edge_rgb function
        sobel_rgb_img = sobel_edge_rgb(img_dog_bordered, border_size=border_size)
        sobel_rgb_img.save("2_sobel_rgb.png")
        # resize by majority color
        sobel_rgb_img = sobel_rgb_img.resize((width, height), Image.Resampling.LANCZOS)
        sobel_rgb_img.save("3_sobel_rgb_resize.png")

        # Resize the original image to match the output size for ASCII background
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
        arr_gray = np.array(img_resized)
        arr_angle = np.array(sobel_rgb_img)

        arr_x = arr_angle[:, :, 0].astype(np.float32)  # Red channel
        arr_y = arr_angle[:, :, 1].astype(np.float32)  # Green channel
        magnitude = arr_angle[:, :, 2].astype(np.float32)  # Blue channel

        img_backup_resized = img_backup.resize((width, height), Image.Resampling.LANCZOS)
        arr_backup = np.array(img_backup_resized)

        ascii_text = Text()
        for y in range(height):
            for x in range(width):
                mag = magnitude[y, x] / (magnitude.max() + 1e-8)
                angle = np.arctan2(arr_y[y, x], arr_x[y, x])
                char = ""
                if mag > EDGE_THRESHOLD:
                    if (-np.pi/8 <= angle < np.pi/8):
                        char = '|'
                    elif (np.pi/8 <= angle < 3*np.pi/8):
                        char = '\\'
                    elif (3*np.pi/8 <= angle < 5*np.pi/8) or (-5*np.pi/8 <= angle < -3*np.pi/8):
                        char = '-'
                    elif (-3*np.pi/8 <= angle < -np.pi/8):
                        char = '/'
                    else:
                        char = ' '
                    ascii_text.append(char, style=f"rgb({arr_backup[y, x][0]},{arr_backup[y, x][1]},{arr_backup[y, x][2]})")
                else:
                    idx = int(arr_gray[y, x] / 255 * (len(ASCII_CHARS) - 1))
                    idx = max(0, min(idx, len(ASCII_CHARS) - 1))
                    char = ASCII_CHARS[idx]
                    ascii_text.append(char, style=f"rgb({arr_backup[y, x][0]},{arr_backup[y, x][1]},{arr_backup[y, x][2]})")
            if y < height-1:
                ascii_text.append("\n")

        return ascii_text
    except Exception as e:
        return f"[ASCII conversion error: {e}]"

