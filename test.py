import streamlit as st
import sqlite3
import hashlib
import imagehash
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import os
import pandas as pd
import uuid

# ----------------------------
# Device & CLIP Setup
# ----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"

# Folder where you have downloaded CLIP model
clip_model_path = os.path.abspath("./clip_model_offline")

# Load CLIP offline
model = CLIPModel.from_pretrained(clip_model_path, local_files_only=True).to(device)
processor = CLIPProcessor.from_pretrained(clip_model_path, local_files_only=True)

# ----------------------------
# Database Setup
# ----------------------------
conn = sqlite3.connect("claims.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS records (
    unique_image_id TEXT,
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
def generate_unique_image_id():
    """Generate truly unique ID for a new unique image"""
    return str(uuid.uuid4())[:8]

def get_image_hash(image):
    return str(imagehash.phash(image))

def get_embedding(image, description):
    """Compute joint embedding of image + description (offline)"""
    inputs = processor(text=[description], images=image, return_tensors="pt", padding=True)
    pixel_values = inputs["pixel_values"].to(device)
    input_ids = inputs["input_ids"].to(device)

    with torch.no_grad():
        image_embeds = model.get_image_features(pixel_values)
        text_embeds = model.get_text_features(input_ids)

    combined = (0.4 * image_embeds + 0.6 * text_embeds).cpu().numpy().astype(np.float32)
    return combined.tobytes()

def cosine_similarity(a, b):
    a, b = np.frombuffer(a, dtype=np.float32), np.frombuffer(b, dtype=np.float32)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def check_duplicates(image, description):
    """Check if image matches any existing cluster"""
    image_hash = get_image_hash(image)
    new_embedding = get_embedding(image, description)

    c.execute("SELECT * FROM records")
    all_records = c.fetchall()

    for rec in all_records:
        uid, cust_id, ord_id, market, desc, stored_hash, stored_emb = rec

        # Exact duplicate
        if stored_hash == image_hash:
            return ("Exact Duplicate", uid)

        # Similar image
        sim = cosine_similarity(new_embedding, stored_emb)
        if sim > 0.85:
            return ("Similar Image", uid)

        # Same narrative
        if sim > 0.65:
            return ("Same Narrative", uid)

    return ("No Duplicate", None)

def save_to_db(unique_image_id, customer_id, order_id, marketplace, description, image):
    """Save record into database; link to cluster if duplicate"""
    image_hash = get_image_hash(image)
    embedding = get_embedding(image, description)
    c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",
              (unique_image_id, customer_id, order_id, marketplace, description, image_hash, embedding))
    conn.commit()

# ----------------------------
# Streamlit UI
# ----------------------------
st.sidebar.title("📌 Navigation")
menu = st.sidebar.radio("Go to:", ["Submit Claim", "Database Viewer"])

st.title("Duplicate image identification and clustering")

# ----------------------------
# Submit Claim
# ----------------------------
if menu == "Submit Claim":
    customer_id_input = st.text_input("Customer ID")
    order_id_input = st.text_input("Order ID")
    marketplace_input = st.text_input("Marketplace")
    description_input = st.text_area("Image Description")
    uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

    if uploaded_file and st.button("Check for Duplicates"):
        image_input = Image.open(uploaded_file).convert("RGB")

        # Check for duplicates
        status, matched_uid = check_duplicates(image_input, description_input)

        if status == "No Duplicate":
            # Create new unique image ID
            new_uid = generate_unique_image_id()
            save_to_db(new_uid, customer_id_input, order_id_input, marketplace_input,
                       description_input, image_input)
            st.success(f"✅ No duplicate found. Stored under Unique Image ID: {new_uid}")
        else:
            # Link current claim to existing unique image ID
            save_to_db(matched_uid, customer_id_input, order_id_input, marketplace_input,
                       description_input, image_input)
            st.warning(f"⚠️ {status} found! Claim linked to existing Unique Image ID: {matched_uid}")

# ----------------------------
# Database Viewer
# ----------------------------
elif menu == "Database Viewer":
    st.subheader("📂 Stored Claims in Database")

    c.execute("SELECT unique_image_id, customer_id, order_id, marketplace, description FROM records")
    rows = c.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["Unique Image ID", "Customer ID", "Order ID", "Marketplace", "Description"])
        grouped = df.groupby("Unique Image ID")

        for uid, group in grouped:
            st.markdown(f"###  Unique Image ID: {uid}")
            st.table(group[["Customer ID", "Order ID", "Marketplace", "Description"]])
    else:
        st.info("No records found in database.")