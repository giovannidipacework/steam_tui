from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
import numpy as np
import os
from rich.text import Text

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

def sobel_edge(image, edge_threshold=0.3):
    """
    Apply Sobel edge detection to an image.
    """
    Gx = np.array([[1.0, 0.0, -1.0], [2.0, 0.0, -2.0], [1.0, 0.0, -1.0]])
    Gy = np.array([[1.0, 2.0, 1.0], [0.0, 0.0, 0.0], [-1.0, -2.0, -1.0]])
    [rows, columns] = np.shape(image)

    arr_img = np.array(image)

    mags = np.zeros(shape=(rows, columns))
    angles = np.zeros(shape=(rows, columns))
    arrx = np.zeros(shape=(rows, columns))
    arry = np.zeros(shape=(rows, columns))

    for i in range(rows - 2):
        for j in range(columns - 2):
            gx = np.sum(np.multiply(Gx, arr_img[i:i + 3, j:j + 3]))  # x direction
            gy = np.sum(np.multiply(Gy, arr_img[i:i + 3, j:j + 3]))  # y direction
            arrx[i + 1, j + 1] = gx
            arry[i + 1, j + 1] = gy
            mags[i + 1, j + 1] = np.sqrt(gx ** 2 + gy ** 2)
            angles[i + 1, j + 1] = np.atan2(gy, gx)

    mask = (mags/(mags.max()+ 1e-8)) > edge_threshold
    angles_masked = np.where(mask, angles, 0)
    
    # DEBUG -------------------------------------------------------------------------------------------------------
    DEBUG = False
    if(DEBUG == True):
        h, w = arr_img.shape
        rgb_img = np.zeros((h, w, 3), dtype=np.uint8)
        for x in range(h):
            for y in range(w):
                if mask[x,y] > 0:
                    theta = angles[x,y]
                    absTheta = abs(theta) / np.pi
                    if ((0.0 <= absTheta) and (absTheta < 0.05)):
                        rgb_img[x, y] = (255,0,0)
                    elif ((0.9 < absTheta) and (absTheta <= 1.0)):
                        rgb_img[x, y] = (255,0,0)
                    elif ((0.45 < absTheta) and (absTheta < 0.55)):
                        rgb_img[x, y] =  (0,255,0)
                    elif (0.05 < absTheta and absTheta < 0.45):
                        rgb_img[x, y] = (0,0,255) if np.sign(theta) > 0 else (255,255,0)
                    elif (0.55 < absTheta and absTheta < 0.9):
                        rgb_img[x, y] = (255,255,0) if np.sign(theta) > 0 else (0,0,255)
                else:
                    rgb_img[x, y] = (0, 0, 0)

        images = [arr_img, arrx, arry, mags, angles_masked,rgb_img]
        titles = ['arr_img', 'arrx', 'arry',  'mags', 'angles_masked', 'rgb_img']
        fig, axs = plt.subplots(1, images.__len__(), figsize=(12, 4))  # 1 riga, 3 colonne
        for i, ax in enumerate(axs):
            ax.imshow(images[i])
            ax.set_title(titles[i])
            ax.axis('off')  # nasconde assi
        plt.tight_layout()
        plt.show()
    # DEBUG -------------------------------------------------------------------------------------------------------

    return angles_masked

def image_to_ascii(image_path, in_width=40):
    # ... codice simile a image_to_ascii_pillow ...

    ASCII_CHARS = " .:-=+*#%@░▒▓█"
    EDGE_THRESHOLD = 0.5

    # Get terminal size and set max width/height
    try:
        term_size = os.get_terminal_size()
        max_width = min(term_size.lines, in_width)
        max_height = max_width
    except Exception:
        max_width = 10
        max_height = 10

    # Check for transparent background
    img = Image.open(image_path)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (0, 0, 0, 255))
        img = Image.alpha_composite(background, img).convert("RGB")
    else:
        img = img.convert("RGB")

    img_colors = img
    img = img.convert("L")

    # Calculate width and height to fit terminal and maintain aspect ratio
    # ASCII characters are taller than wide, so adjust aspect ratio
    aspect_ratio = img.height / img.width
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

    img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

    img_dog = difference_of_gaussian(img_resized, sigma1=1, sigma2=2)

    border_size = 1
    img_dog_bordered = Image.new("L", (img_dog.width + 2 * border_size, img_dog.height + 2 * border_size), 128)
    img_dog_bordered.paste(img_dog, (border_size, border_size))

    # Use the new sobel_edge_rgb function
    arr_angle = sobel_edge(img_dog_bordered, EDGE_THRESHOLD)

    # Resize the original image to match the output size for ASCII background
    arr_gray = np.array(img_resized)
    
    img_colors = img_colors.resize((width, height), Image.Resampling.LANCZOS)
    arr_colors = np.array(img_colors)

    ascii_text = Text()
    for y in range(height-1):
        for x in range(width-1):
            char = ""
            theta = arr_angle[y,x]
            if theta != 0:
                absTheta = abs(theta) / np.pi
                if ((0.0 <= absTheta) and (absTheta < 0.05)):
                    char = '|'
                elif ((0.9 < absTheta) and (absTheta <= 1.0)):
                    char = '|'
                elif ((0.45 < absTheta) and (absTheta < 0.55)):
                    char =  '-'
                elif (0.05 < absTheta and absTheta < 0.45):
                    char = '/' if np.sign(theta) > 0 else '\\'
                elif (0.55 < absTheta and absTheta < 0.9):
                    char = '\\' if np.sign(theta) > 0 else '/'
                ascii_text.append(char, style=f"rgb({arr_colors[y, x][0]},{arr_colors[y, x][1]},{arr_colors[y, x][2]})")
            else:
                idx = int(arr_gray[y, x] / 255 * (len(ASCII_CHARS) - 1))
                idx = max(0, min(idx, len(ASCII_CHARS) - 1))
                char = ASCII_CHARS[idx]
                # char = " "
                ascii_text.append(char, style=f"rgb({arr_colors[y, x][0]},{arr_colors[y, x][1]},{arr_colors[y, x][2]})")
        if y < height-1:
            ascii_text.append("\n")

    return ascii_text

# def main():
#     path = "C:/Program Files (x86)/Steam/userdata/66186145/config/grid/2447872262_icon.png"
#     img = image_to_ascii_colored(path, 80)
#     print(f"{img}")

# if __name__ == "__main__":
#     main()