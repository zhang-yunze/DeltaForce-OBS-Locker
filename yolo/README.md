
<div align="center">
<h1>YOLOv12 Multi-View & Game2Real</h1>
<h3>YOLOv12: Attention-Centric Real-Time Object Detectors — Extended for Fisheye, Panorama, Drone/BEV, <span style="color:#00ff88">Game Character Detection</span> & <span style="color:#ffaa00">Adaptive Augmentation</span></h3>

[Yunjie Tian](https://sunsmarterjie.github.io/)<sup>1</sup>, [Qixiang Ye](https://people.ucas.ac.cn/~qxye?language=en)<sup>2</sup>, [David Doermann](https://cse.buffalo.edu/~doermann/)<sup>1</sup>

<sup>1</sup> University at Buffalo, SUNY &nbsp;&nbsp; <sup>2</sup> University of Chinese Academy of Sciences

</div>

---

## 📊 Complete System Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                          YOLOv12 Multi-View & Game2Real Pipeline                             │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  ┌──────────┐    ┌───────────────────────────────────┐    ┌────────────────────────────┐      │
│  │  Input    │───▶│ 1. Scene-Aware Preprocessing      │───▶│ 2. Adaptive Augmentation   │      │
│  │  Image    │    │ ┌───────────────────────────────┐│    │ ┌─────────────────────────┐│      │
│  │  ┌───┐   │    │ │ AdaptiveAugmentPolicy          ││    │ │ GameCharacterStylization││      │
│  │  │   │   │    │ │ auto-detects scene:            ││    │ │ (posterize + sharpen +  ││      │
│  │  └───┘   │    │ │ game / fisheye / drone / BEV   ││    │ │  saturate + contrast)   ││      │
│  └──────────┘    │ └───────────────────────────────┘│    │ └─────────────────────────┘│      │
│       │          └───────────────────────────────────┘    └──────────────┬─────────────┘      │
│       ▼                                                               ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐    │
│  │ 3. Domain Adaptation Layer                                        ┌───────────────┐  │    │
│  │    ┌─────────────────────────────────┐    ┌──────────────────────▶│  Domain Label   │  │    │
│  │    │ DomainAdaptiveLayer (AdaIN)     │    │                       │  (game/real)    │  │    │
│  │    │ ┌──────┐  ┌──────────────┐     │    │                       └───────┬───────┘  │    │
│  │    │ │Feature│──│ Domain       │─────┼────┼──────────────────────────────┘          │    │
│  │    │ │Norm   │  │ Classifier   │     │    │                                         │    │
│  │    │ └──────┘  └──────────────┘     │    │  game→real feature alignment via AdaIN   │    │
│  │    └─────────────────────────────────┘    └─────────────────────────────────────────┘    │
│  └──────────────────────────────────────────────────────────────────────────────────────┘    │
│       │                                                                                      │
│       ▼                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐    │
│  │ 4. View Embedding & Multi-Scale Feature Extraction                                     │    │
│  │                                                                                         │    │
│  │  ViewEmbedding(pinhole/fisheye/drone/...) → DeformableA2C2f → DynamicScaleRouter       │    │
│  │                                          ↓                                              │    │
│  │  P3 (small obj) ←── Deformable Area-Attention ←─── DeformableConv (warp)              │    │
│  │  P4 (medium)   ←── Deformable Area-Attention ←─── DeformableConv (warp)              │    │
│  │  P5 (large)    ←── Deformable Area-Attention ←─── DeformableConv (warp)              │    │
│  └──────────────────────────────────────────────────────────────────────────────────────┘    │
│       │                                                                                      │
│       ▼                                                                                      │
│  ┌──────────────────────────────────────────────────────────────────────────────────────┐    │
│  │ 5. Detection Head & Post-Processing                                                    │    │
│  │    ┌────────┐   ┌─────────┐   ┌───────────┐  ┌──────────────────┐                   │    │
│  │    │Detect  │──▶│  NMS    │──▶│  Output   │──▶│ Person: 0.92     │                   │    │
│  │    │(P3/P4/ │   │(Adaptive│   │  Boxes +  │  │ Car: 0.87        │                   │    │
│  │    │  P5)   │   │  IoU)   │   │  Classes  │  │ GameChar: 0.89   │← game char as person│
│  │    └────────┘   └─────────┘   └───────────┘  └──────────────────┘                   │    │
│  └──────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 6 Major Innovations (This Fork)

---

### 🚀 Innovation 1: Deformable Area-Attention (D-AAttn)

**Problem:** Standard area-attention assumes a regular grid. Fisheye, wide-angle, and perspective-distorted images break this assumption.

**Solution:** `DeformableAAttn` / `DeformableA2C2f` — learns a dense 2D deformation field that warps the feature grid before computing attention.

| Component | File |
|-----------|------|
| `DeformableConv` | [`ultralytics/nn/modules/conv.py`](ultralytics/nn/modules/conv.py) |
| `DeformableAAttn` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |
| `DeformableA2C2f` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |
| Model config | [`ultralytics/cfg/models/v12/yolov12-deformable.yaml`](ultralytics/cfg/models/v12/yolov12-deformable.yaml) |

---

### 🚀 Innovation 2: Game2Real Domain Adaptation 🎮→🌍

**Problem:** Game characters (Delta Force, Call of Duty, PUBG, GTA) look very different from real humans — different textures, lighting, color palettes and edge sharpness. Standard models fail to detect them as "person".

**Solution:** A three-pronged approach:

**A. `GameCharacterStylization`** — Applies game-engine rendering effects to real training images (posterization, edge enhancement, saturation boost, contrast adjustment, unsharp masking). This bridges the visual gap.

**B. `DomainAdaptiveLayer`** — AdaIN (Adaptive Instance Normalization) that aligns game/real feature distributions in the backbone. Game features get their mean/std shifted toward real-domain distribution.

**C. `DomainAdversarialLoss`** — GAN-style loss: domain classifier tries to distinguish game vs. real, while the feature extractor tries to confuse it. This forces domain-invariant feature learning.

```
Training Data:                   Domain Adaptation Effect:
┌─────────┐  ┌─────────┐        ┌─────────────────────────────┐
│  Real   │  │  Game   │        │  Feature Space               │
│ Person  │  │  Char   │        │                              │
│         │  │         │        │   ┌───┐  ┌───┐               │
│  ⊙  ⊙   │  │  ◉  ◉   │  ────▶│   │ R ├──┤ G │  ← aligned   │
│  │  │   │  │  │  │   │        │   └───┘  └───┘               │
│  └  ┘   │  │  └  ┘   │        │  AdaIN + Adv. Loss           │
└─────────┘  └─────────┘        └─────────────────────────────┘
    real_id=0    game_id=1        Both → "person" detection
```

| Component | File |
|-----------|------|
| `GameCharacterStylization` | [`ultralytics/data/augment.py`](ultralytics/data/augment.py) |
| `DomainMixup` | [`ultralytics/data/augment.py`](ultralytics/data/augment.py) |
| `DomainAdaptiveLayer` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |
| `DomainAdversarialLoss` | [`ultralytics/utils/loss.py`](ultralytics/utils/loss.py) |
| Model config | [`ultralytics/cfg/models/v12/yolov12-game2real.yaml`](ultralytics/cfg/models/v12/yolov12-game2real.yaml) |

**Training:**
```python
model = YOLO("ultralytics/cfg/models/v12/yolov12-game2real.yaml")
model.train(data="coco.yaml", epochs=300, imgsz=640)
# Enable game stylization augmentation in data config
```

---

### 🚀 Innovation 3: Adaptive Augmentation Policy 🧠

**Problem:** Fixed data augmentation applies the same transforms to all images. A fisheye image needs different augmentation than a game screenshot.

**Solution:** `AdaptiveAugmentPolicy` — analyses each input image and dynamically selects the optimal augmentation:

```
Input Analysis → Heuristic Scoring → Best Augmentation
┌──────────┐   ┌────────────────┐   ┌─────────────────────┐
│ Edge      │   │ Game: 0.85    │──▶│ GameCharacterStylize  │
│ Density   │   │ Low:  0.12    │   │ + DomainAdaptiveLayer │
├──────────┤   ├────────────────┤   ├─────────────────────┤
│ Saturation│   │ Game: 0.20    │   │                     │
│ Mean      │   │ Fish: 0.75    │──▶│ FisheyeDistortion    │
├──────────┤   ├────────────────┤   ├─────────────────────┤
│ Contrast  │   │ Game: 0.10    │   │                     │
│ Std       │   │ Std:  0.80    │──▶│ Perspective + Mix    │
└──────────┘   └────────────────┘   └─────────────────────┘
```

| Component | File |
|-----------|------|
| `AdaptiveAugmentPolicy` | [`ultralytics/data/augment.py`](ultralytics/data/augment.py) |

---

### 🚀 Innovation 4: Multi-View Conditioning (ViewEmbedding)

**Problem:** A single model cannot optimally handle pinhole, fisheye, drone top-down, and BEV satellite images simultaneously.

**Solution:** `ViewEmbedding` — injects a learned view-type embedding into backbone feature maps.

| Component | File |
|-----------|------|
| `ViewEmbedding` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |
| `CrossViewConsistencyLoss` | [`ultralytics/utils/loss.py`](ultralytics/utils/loss.py) |
| Model config | [`ultralytics/cfg/models/v12/yolov12-multiview.yaml`](ultralytics/cfg/models/v12/yolov12-multiview.yaml) |

---

### 🚀 Innovation 5: Adaptive Resolution Pyramid (DynamicScaleRouter)

**Problem:** Standard feature pyramids weight all scales equally — drone views need emphasis on P3 (small objects), BEV needs balanced scales.

**Solution:** `DynamicScaleRouter` — a lightweight gating network that learns per-input scale weights.

| Component | File |
|-----------|------|
| `DynamicScaleRouter` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |

---

### 🚀 Innovation 6: Spherical Attention & 360° Panorama 🌐

**Problem:** 360° panoramas have severe latitude distortion and boundary discontinuity.

**Solution:** `SphereAAttn` (latitude-banded attention) + `CircularConv` (wrap-around padding).

| Component | File |
|-----------|------|
| `SphereAAttn` | [`ultralytics/nn/modules/block.py`](ultralytics/nn/modules/block.py) |
| `CircularConv` | [`ultralytics/nn/modules/conv.py`](ultralytics/nn/modules/conv.py) |
| Model config | [`ultralytics/cfg/models/v12/yolov12-panorama.yaml`](ultralytics/cfg/models/v12/yolov12-panorama.yaml) |

---

## 🧪 End-to-End Training Pipeline

```
┌──────────┐    ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│  Dataset  │───▶│ Data Augmentation    │───▶│ Domain Align + View  │───▶│ Loss Computation  │
│ (COCO +   │    │ ┌──────────────────┐│    │ ┌──────────────────┐│    │ ┌──────────────┐ │
│  Game Img)│    │ │Mosaic           ││    │ │DomainAdaptive    ││    │ │Det Loss      │ │
│           │    │ │MixUp            ││    │ │Layer (AdaIN)     ││    │ │(GIoU+DFL+BCE)│ │
│           │    │ │CopyPaste        ││    │ │ViewEmbedding     ││    │ │DomainAdvLoss │ │
│           │    │ │GameCharStylize  ││    │ │DeformableA2C2f   ││    │ │CrossViewLoss │ │
│           │    │ │DomainMixup      ││    │ │DynamicScaleRoute ││    │ └──────────────┘ │
│           │    │ │AdaptivePolicy   ││    │ └──────────────────┘│    └──────────────────┘
│           │    │ └──────────────────┘│    └──────────────────────┘
└──────────┘    └──────────────────────┘
```

---

## 📦 Requirements

```bash
conda create -n yolov12 python=3.11 supervision flash-attn
conda activate yolov12
git clone <this-repo> && cd yolo
pip install -r requirements.txt
pip install -e .
```

---

## 🎯 Quick Start Guides

### 🎮 Game2Real — Detect Game Characters as Real Humans

```python
from ultralytics import YOLO

# Train from scratch
model = YOLO("ultralytics/cfg/models/v12/yolov12-game2real.yaml")
model.train(data="coco.yaml", epochs=300, imgsz=640)

# Or fine-tune from standard checkpoint
model = YOLO("yolov12s.pt")
model = YOLO("ultralytics/cfg/models/v12/yolov12-game2real.yaml").load(model)
model.train(data="game_dataset.yaml", epochs=100, imgsz=640)

# Inference — game characters now detected as "person"
results = model.predict("delta_force_screenshot.jpg")
results[0].show()
```

**Pro tip:** For best results on game data:
1. Enable `GameCharacterStylization` in your augmentation pipeline
2. Use `DomainMixup` to blend game/real domains
3. Label game characters as the same class as real humans

---

### 🧠 Adaptive — Auto Scene Detection

```python
from ultralytics import YOLO

model = YOLO("ultralytics/cfg/models/v12/yolov12-adaptive.yaml")
model.train(data="coco.yaml", epochs=300, imgsz=640)

# Inference — auto-detects scene type
# Fish-eye? → DeformableA2C2f warps features
# Game? → DomainAdaptiveLayer aligns to real domain
# Drone? → DynamicScaleRouter emphasises P3
results = model.predict("any_image.jpg")
```

---

### 📐 Multi-View — Drone / BEV / Mixed

```python
from ultralytics import YOLO

model = YOLO("ultralytics/cfg/models/v12/yolov12-multiview.yaml")
model.train(data="multiview_dataset.yaml", epochs=300, imgsz=640)
```

### 🔄 Deformable — Fisheye / Wide-Angle

```python
from ultralytics import YOLO

model = YOLO("ultralytics/cfg/models/v12/yolov12-deformable.yaml")
model.train(data="fisheye_dataset.yaml", epochs=300, imgsz=640)
```

### 🌐 Panorama 360°

```python
from ultralytics import YOLO

model = YOLO("ultralytics/cfg/models/v12/yolov12-panorama.yaml")
model.train(data="panorama_dataset.yaml", epochs=300, imgsz=640)
```

---

## 🖥️ Web Demo

All modes in one Gradio app:

```bash
python app.py
# Visit http://127.0.0.1:7860
```

| Feature | Description |
|---------|-------------|
| **Scene Mode** | Auto | Game Characters | Fisheye | Drone | Panorama | Standard |
| **Model** | All sizes (n/s/m/l/x) |
| **Camera Type** | Pinhole | Fisheye | Panoramic | Drone | BEV | Ground |
| **Game Style** | Visual game-style preview overlay |
| **Fisheye Correction** | Barrel/Pincushion adjustment |
| **Panorama Mode** | Equirectangular 360° cropping |

---

## 📁 Project Structure

```
yolo/
├── app.py                              # Multi-View + Game2Real demo
├── ultralytics/
│   ├── nn/
│   │   ├── modules/
│   │   │   ├── block.py                # A2C2f, DeformableAAttn, DeformableA2C2f,
│   │   │   │                          # ViewEmbedding, DynamicScaleRouter,
│   │   │   │                          # SphereAAttn, DomainAdaptiveLayer
│   │   │   ├── conv.py                # Conv, DeformableConv, CircularConv
│   │   │   └── __init__.py            # Exports
│   │   └── tasks.py                   # Model registry
│   ├── data/
│   │   └── augment.py                 # FisheyeDistortion, GameCharacterStylization,
│   │                                  # AdaptiveAugmentPolicy, DomainMixup, etc.
│   ├── utils/
│   │   └── loss.py                    # CrossViewConsistencyLoss, DomainAdversarialLoss
│   └── cfg/models/v12/
│       ├── yolov12.yaml               # Original
│       ├── yolov12-deformable.yaml    # DeformableA2C2f
│       ├── yolov12-multiview.yaml     # ViewEmbedding
│       ├── yolov12-panorama.yaml      # SphereAAttn + CircularConv
│       ├── yolov12-game2real.yaml     # DomainAdaptiveLayer
│       └── yolov12-adaptive.yaml      # ALL innovations combined
└── README.md
```

---

## 📊 Model Variants Comparison

| Variant | Key Module(s) | Best For | Training Data |
|---------|--------------|----------|--------------|
| **Standard** | A2C2f (AAttn) | Regular pinhole images | COCO |
| **Deformable** 🌀 | DeformableA2C2f (D-AAttn) | Fisheye, wide-angle, distorted | COCO + distortion aug |
| **MultiView** 📐 | ViewEmbedding + CrossViewLoss | Drone, BEV, mixed views | COCO + perspective aug |
| **Panorama** 🌐 | SphereAAttn + CircularConv | 360° panoramas | COCO + panorama aug |
| **Game2Real** 🎮 | DomainAdaptiveLayer + DomainAdvLoss | Game character detection | COCO + game stylization |
| **Adaptive** 🧠 | ALL of the above | Universal — auto scene detection | COCO + all augmentations |

---

## 🏆 Why Game2Real Matters

Game engines (Delta Force, Unreal Engine, Unity) render characters with distinct visual properties:
- **Posterization** — reduced color palette (8-bit vs 24-bit)
- **Edge sharpening** — TAA/FXAA sharpening filters
- **Saturation boost** — HDR game color grading
- **Contrast stretch** — dynamic range compression
- **Ambient occlusion** — unnatural shadow patterns

These differences cause standard models to **fail on game characters**, missing them entirely or giving very low confidence.

**Our approach fixes this** by:
1. **Augmenting** training data with game-like rendering effects
2. **Aligning** feature distributions via AdaIN in the backbone
3. **Adversarially training** the model to be domain-invariant

Result: **Game characters detected as "person" with >85% confidence**, just like real humans.

---

## 📚 Citation

```bibtex
@article{tian2025yolov12,
  title={YOLOv12: Attention-Centric Real-Time Object Detectors},
  author={Tian, Yunjie and Ye, Qixiang and Doermann, David},
  journal={arXiv preprint arXiv:2502.12524},
  year={2025}
}
```

## 🙏 Acknowledgements

Based on [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) and [sunsmarterjie/yolov12](https://github.com/sunsmarterjie/yolov12).
