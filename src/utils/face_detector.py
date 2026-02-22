"""人脸检测工具模块。

使用 OpenCV Haar 级联分类器检测图片中的人脸。
"""

import cv2
import numpy as np
from loguru import logger


class FaceDetector:
    """人脸检测器，用于识别头像图片。"""

    def __init__(self) -> None:
        """初始化人脸检测器，加载 Haar 级联分类器。"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def detect_faces(self, image_bytes: bytes) -> list[tuple[int, int, int, int]]:
        """检测图片中的人脸位置。

        Args:
            image_bytes: 图片字节数据

        Returns:
            list[tuple]: 人脸位置列表 [(x, y, w, h), ...]
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return []

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
            )
            return [tuple(face) for face in faces]
        except Exception as e:
            logger.warning(f"人脸检测失败: {e}")
            return []

    def get_face_score(self, image_bytes: bytes) -> float:
        """计算图片的人脸相似度得分。

        得分基于：
        - 检测到的人脸数量
        - 人脸区域大小占比

        Args:
            image_bytes: 图片字节数据

        Returns:
            float: 人脸相似度得分（0-100）
        """
        faces = self.detect_faces(image_bytes)
        if not faces:
            return 0.0

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return 0.0

        img_area = img.shape[0] * img.shape[1]
        max_face_area = max(w * h for (_, _, w, h) in faces)
        face_ratio = max_face_area / img_area if img_area > 0 else 0

        score = min(len(faces) * 20, 40) + min(face_ratio * 80, 60)
        return score

    def select_best_avatar(self, images: list[bytes]) -> int:
        """从多张图片中选择最像头像的那一张。

        Args:
            images: 图片字节列表

        Returns:
            int: 最佳图片的索引，如果没有检测到人脸则返回得分最高或第一张
        """
        if not images:
            return 0

        scores = [self.get_face_score(img) for img in images]
        best_idx = max(range(len(scores)), key=lambda i: scores[i])

        logger.info(
            f"人脸检测得分: {scores}, 最佳索引: {best_idx}, 得分: {scores[best_idx]}"
        )
        return best_idx


def filter_avatar_images(images: list[bytes]) -> list[bytes]:
    """过滤图片，保留最可能是头像的那一张。

    逻辑：
    1. 如果图片数量 <= 1，直接返回
    2. 如果图片数量 > 1，使用人脸检测选择最佳的一张

    Args:
        images: 图片字节列表（已通过大小过滤）

    Returns:
        list[bytes]: 过滤后的图片列表（最多 1 张）
    """
    if len(images) <= 1:
        return images

    detector = FaceDetector()
    best_idx = detector.select_best_avatar(images)

    logger.info(f"人脸检测过滤: 从 {len(images)} 张图片中保留 1 张头像")
    return [images[best_idx]]


__all__ = ["FaceDetector", "filter_avatar_images"]
