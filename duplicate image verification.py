import cv2
from PIL import Image
import imagehash

# Load images using OpenCV
image_path1 = input("Enter image URL 1: ")
image_path2 = input("Enter image URL 2: ")
img1 = cv2.imread(image_path1)
img2 = cv2.imread(image_path2)

# Convert to PIL format for hashing
img1_pil = Image.fromarray(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
img2_pil = Image.fromarray(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
a
# Generate hash
hash1 = imagehash.average_hash(img1_pil)
hash2 = imagehash.average_hash(img2_pil)

# Compare hashes
if hash1 - hash2 < 5:
    print("Images are duplicates or nearly identical")
else:
    print("Images are different")