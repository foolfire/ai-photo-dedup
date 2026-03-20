"""
深度特征提取模块
使用 MobileNetV2 提取图片语义特征向量
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image


class ImageEmbedder:
    """深度特征向量提取器"""

    def __init__(self, device: str = "auto"):
        if device == "auto":
            self.device = torch.device("mps" if torch.backends.mps.is_available()
                                       else "cuda" if torch.cuda.is_available()
                                       else "cpu")
        else:
            self.device = torch.device(device)

        # 加载预训练 MobileNetV2，去掉分类头
        from torchvision.models import mobilenet_v2
        self.model = mobilenet_v2(weights="IMAGENET1K_V1")
        self.model.classifier = torch.nn.Identity()  # 输出 1280 维特征
        self.model.eval().to(self.device)

        self.transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    @torch.no_grad()
    def embed(self, image_path: Path) -> Optional[np.ndarray]:
        """提取单张图片的特征向量"""
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
                tensor = self.transform(img).unsqueeze(0).to(self.device)
                features = self.model(tensor)
                # L2 归一化
                features = F.normalize(features, p=2, dim=1)
                return features.cpu().numpy().flatten()
        except Exception as e:
            print(f"[WARN] 无法提取特征 {image_path}: {e}")
            return None

    def embed_batch(self, image_paths: List[Path], batch_size: int = 32) -> Dict[Path, np.ndarray]:
        """批量提取特征向量"""
        embeddings: Dict[Path, np.ndarray] = {}
        batch_paths: List[Path] = []
        batch_tensors: List[torch.Tensor] = []

        for path in image_paths:
            try:
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    tensor = self.transform(img)
                    batch_paths.append(path)
                    batch_tensors.append(tensor)
            except Exception as e:
                print(f"[WARN] 跳过 {path}: {e}")
                continue

            if len(batch_tensors) == batch_size:
                self._process_batch(batch_paths, batch_tensors, embeddings)
                batch_paths.clear()
                batch_tensors.clear()

        # 处理剩余
        if batch_tensors:
            self._process_batch(batch_paths, batch_tensors, embeddings)

        return embeddings

    @torch.no_grad()
    def _process_batch(self, paths, tensors, embeddings):
        batch = torch.stack(tensors).to(self.device)
        features = self.model(batch)
        features = F.normalize(features, p=2, dim=1)
        for i, p in enumerate(paths):
            embeddings[p] = features[i].cpu().numpy()


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算余弦相似度（向量已归一化时等同于点积）"""
    return float(np.dot(a, b))


def find_embedding_duplicates(
    embeddings: Dict[Path, np.ndarray],
    threshold: float = 0.95,
) -> List[List[Path]]:
    """
    在特征向量字典中找出所有重复组
    threshold: 余弦相似度阈值（0-1）
    """
    paths = list(embeddings.keys())
    visited = set()
    groups: List[List[Path]] = []

    for i, p1 in enumerate(paths):
        if p1 in visited:
            continue
        group = [p1]
        for j in range(i + 1, len(paths)):
            p2 = paths[j]
            if p2 in visited:
                continue
            sim = cosine_similarity(embeddings[p1], embeddings[p2])
            if sim >= threshold:
                group.append(p2)
                visited.add(p2)
        if len(group) > 1:
            visited.add(p1)
            groups.append(group)

    return groups
