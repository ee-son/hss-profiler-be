import tensorflow as tf
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

from services.preprocess import custom_standardization

model = tf.keras.models.load_model(
    "models/best_general_model.keras",
    custom_objects={
        "custom_standardization": custom_standardization
    }
)

print("SUCCESS")
model.summary(expand_nested=True)