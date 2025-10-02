# ----------------------------
# Libraries Used:
# ----------------------------
# - streamlit → UI
# - sqlite3 → Database storage
# - hashlib → Generate Unique IDs
# - PIL → Image processing
# - imagehash → Exact duplicate detection
# - torch + transformers (CLIP) → Similarity embeddings
# ----------------------------

import streamlit as st
import sqlite3
import hashlib
import imagehash
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

# ----------------------------
# Initialize CLIP Model
# ----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# ----------------------------
# Database Setup
# ----------------------------
conn = sqlite3.connect("claims.db", check_same_thread=False)
c = conn.cursor()

# Store everything in one table
c.execute("""
CREATE TABLE IF NOT EXISTS records (
    image_id TEXT,
    customer_id TEXT,
    order_id TEXT,
    marketplace TEXT,
    description TEXT,
    image_hash TEXT,
    embedding BLOB
)
""")
conn.commit()

# ----------------------------
# Utility Functions
# ----------------------------
def generate_image_id(customer_id, order_id):
    """Generate unique image ID from Customer + Order ID"""
    raw = f"{customer_id}_{order_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]

def get_image_hash(image):
    """Compute perceptual hash (for exact duplicates)"""
    return str(imagehash.phash(image))

def get_embedding(image, description):
    """Compute joint embedding of image + description"""
    inputs = processor(text=[description], images=image, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        image_embeds = model.get_image_features(inputs["pixel_values"])
        text_embeds = model.get_text_features(inputs["input_ids"])
    # Weighted sum (more weight on text for narrative matching)
    combined = (0.4 * image_embeds + 0.6 * text_embeds).cpu().numpy()
    return combined.tobytes()  # store as BLOB

def cosine_similarity(a, b):
    """Compute cosine similarity between two embeddings"""
    import numpy as np
    a, b = np.frombuffer(a, dtype=np.float32), np.frombuffer(b, dtype=np.float32)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def check_duplicates(image, description):
    """Check DB for duplicates"""
    image_hash = get_image_hash(image)
    new_embedding = get_embedding(image, description)

    c.execute("SELECT * FROM records")
    all_records = c.fetchall()

    for rec in all_records:
        img_id, cust_id, ord_id, market, desc, stored_hash, stored_emb = rec

        # 1. Exact duplicate (hash match)
        if stored_hash == image_hash:
            return ("Exact Duplicate", img_id, cust_id, ord_id)

        # 2. Similar image (high cosine similarity on images)
        sim = cosine_similarity(new_embedding, stored_emb)
        if sim > 0.85:
            return ("Similar Image", img_id, cust_id, ord_id)

        # 3. Same narrative (moderate similarity with description+image combined)
        if sim > 0.65:
            return ("Same Narrative", img_id, cust_id, ord_id)

    return ("No Duplicate", None, None, None)

def save_to_db(image_id, customer_id, order_id, marketplace, description, image):
    """Save record to DB"""
    image_hash = get_image_hash(image)
    embedding = get_embedding(image, description)
    c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",
              (image_id, customer_id, order_id, marketplace, description, image_hash, embedding))
    conn.commit()

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🖼️ Duplicate & Narrative Detection Tool")

customer_id = st.text_input("Customer ID")
order_id = st.text_input("Order ID")
marketplace = st.text_input("Marketplace")
description = st.text_area("Image Description")
uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file and st.button("Check for Duplicates"):
    image = Image.open(uploaded_file).convert("RGB")

    # Generate Unique Image ID
    new_image_id = generate_image_id(customer_id, order_id)

    # Check for duplicates
    status, existing_img_id, cust, ordid = check_duplicates(image, description)

    if status == "No Duplicate":
        save_to_db(new_image_id, customer_id, order_id, marketplace, description, image)
        st.success(f"✅ No duplicate found. Stored under Image ID: {new_image_id}")

    else:
        st.warning(f"⚠️ {status} found! Existing Claim → ImageID: {existing_img_id}, "
                   f"CustomerID: {cust}, OrderID: {ordid}")
        st.info(f"New claim is now linked to existing Image ID: {existing_img_id}")