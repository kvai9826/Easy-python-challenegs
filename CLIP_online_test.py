from transformers import CLIPProcessor, CLIPModel
import os

save_path = "./clip_model_offline"
os.makedirs(save_path, exist_ok=True)

# Download and save CLIP
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

model.save_pretrained(save_path)
processor.save_pretrained(save_path)

print(f"✅ CLIP saved at {save_path}")