import os
import gc
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet50

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CONFIG_DIR = os.path.join(PROJECT_DIR, "config")

DEVICE = torch.device("cpu")

IMAGE_TRANSFORMS = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


class CNNFromScratch(nn.Module):
    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 28 * 28, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)



# Mantém somente um modelo carregado por vez para economizar RAM.
_loaded_model = None
_loaded_model_key = None

# Reduz o consumo de memória e processamento em servidores pequenos.
torch.set_num_threads(1)

try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass


def load_ecg_model(model_type):
    global _loaded_model, _loaded_model_key

    model_type = (model_type or "resnet50").lower()

    if model_type in ("cnn", "cnn_scratch", "cnn do zero"):
        model_key = "cnn"
        weights_path = os.path.join(
            CONFIG_DIR, "cnn_scratch_weights.pth"
        )
    elif model_type in ("resnet50", "resnet", "resnet50 (transfer learning)"):
        model_key = "resnet50"
        weights_path = os.path.join(
            CONFIG_DIR, "resnet_transfer_weights.pth"
        )
    else:
        raise ValueError("Modelo selecionado não é válido.")

    # Reutiliza o modelo se ele já estiver carregado.
    if _loaded_model is not None and _loaded_model_key == model_key:
        return _loaded_model

    # Libera o modelo anterior antes de carregar outro.
    if _loaded_model is not None:
        del _loaded_model
        _loaded_model = None
        _loaded_model_key = None
        gc.collect()

    if not os.path.exists(weights_path):
        raise FileNotFoundError(
            f"Arquivo de pesos não encontrado: {weights_path}"
        )

    if model_key == "cnn":
        model = CNNFromScratch()
    else:
        model = resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, 2)

    try:
        state_dict = torch.load(
            weights_path,
            map_location=DEVICE,
            weights_only=True,
            mmap=True
        )
    except (TypeError, RuntimeError):
        try:
            state_dict = torch.load(
                weights_path,
                map_location=DEVICE,
                weights_only=True
            )
        except TypeError:
            state_dict = torch.load(
                weights_path,
                map_location=DEVICE
            )

    try:
        model.load_state_dict(state_dict, assign=True)
    except TypeError:
        model.load_state_dict(state_dict)

    del state_dict
    gc.collect()

    model.to(DEVICE)
    model.eval()

    _loaded_model = model
    _loaded_model_key = model_key

    return _loaded_model


def analyze_ecg_image(image_file, model_type="resnet50"):
    image = Image.open(image_file).convert("RGB")
    image_tensor = IMAGE_TRANSFORMS(image).unsqueeze(0).to(DEVICE)

    model = load_ecg_model(model_type)

    with torch.inference_mode():
        outputs = model(image_tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]

    anomaly_probability = probabilities[0].item() * 100
    normal_probability = probabilities[1].item() * 100

    prediction = int(torch.argmax(probabilities).item())

    classification = (
        "Anomalia detectada" if prediction == 0 else "Normal"
    )

    return {
        "classification": classification,
        "probabilities": {
            "Anomalia (M)": round(anomaly_probability, 2),
            "Normal (N)": round(normal_probability, 2)
        },
        "model": model_type
    }
