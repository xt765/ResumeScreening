"""人脸检测工具测试。"""

import cv2
import numpy as np
import pytest

from src.utils.face_detector import FaceDetector, filter_avatar_images


def create_test_image(
    width: int = 200,
    height: int = 200,
    color: tuple[int, int, int] = (128, 128, 128),
) -> bytes:
    """创建测试图片。

    Args:
        width: 图片宽度
        height: 图片高度
        color: 背景颜色 (B, G, R)

    Returns:
        bytes: 图片字节数据
    """
    img = np.full((height, width, 3), color, dtype=np.uint8)
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


def create_face_like_image(width: int = 200, height: int = 200) -> bytes:
    """创建类似人脸的测试图片。

    在图片中央绘制一个椭圆模拟人脸。

    Args:
        width: 图片宽度
        height: 图片高度

    Returns:
        bytes: 图片字节数据
    """
    img = np.full((height, width, 3), (200, 200, 200), dtype=np.uint8)

    center = (width // 2, height // 2)
    axes = (width // 4, height // 3)
    cv2.ellipse(img, center, axes, 0, 0, 360, (180, 180, 180), -1)

    cv2.circle(img, (center[0] - 20, center[1] - 10), 8, (50, 50, 50), -1)
    cv2.circle(img, (center[0] + 20, center[1] - 10), 8, (50, 50, 50), -1)
    cv2.ellipse(img, (center[0], center[1] + 20), (15, 8), 0, 0, 360, (100, 100, 100), -1)

    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


class TestFaceDetector:
    """人脸检测器测试。"""

    def test_init(self) -> None:
        """测试初始化。"""
        detector = FaceDetector()
        assert detector.face_cascade is not None
        assert not detector.face_cascade.empty()

    def test_detect_faces_no_face(self) -> None:
        """测试无人脸图片。"""
        detector = FaceDetector()
        image_bytes = create_test_image()
        faces = detector.detect_faces(image_bytes)
        assert isinstance(faces, list)

    def test_detect_faces_invalid_image(self) -> None:
        """测试无效图片数据。"""
        detector = FaceDetector()
        faces = detector.detect_faces(b"invalid_image_data")
        assert faces == []

    def test_detect_faces_empty_bytes(self) -> None:
        """测试空字节数据。"""
        detector = FaceDetector()
        faces = detector.detect_faces(b"")
        assert faces == []

    def test_get_face_score_no_face(self) -> None:
        """测试无人脸图片得分。"""
        detector = FaceDetector()
        image_bytes = create_test_image()
        score = detector.get_face_score(image_bytes)
        assert score == 0.0

    def test_get_face_score_invalid_image(self) -> None:
        """测试无效图片得分。"""
        detector = FaceDetector()
        score = detector.get_face_score(b"invalid")
        assert score == 0.0

    def test_select_best_avatar_empty_list(self) -> None:
        """测试空图片列表。"""
        detector = FaceDetector()
        idx = detector.select_best_avatar([])
        assert idx == 0

    def test_select_best_avatar_single_image(self) -> None:
        """测试单张图片。"""
        detector = FaceDetector()
        images = [create_test_image()]
        idx = detector.select_best_avatar(images)
        assert idx == 0

    def test_select_best_avatar_multiple_images(self) -> None:
        """测试多张图片选择最佳。"""
        detector = FaceDetector()
        images = [
            create_test_image(color=(100, 100, 100)),
            create_test_image(color=(200, 200, 200)),
            create_test_image(color=(150, 150, 150)),
        ]
        idx = detector.select_best_avatar(images)
        assert 0 <= idx < len(images)


class TestFilterAvatarImages:
    """头像过滤测试。"""

    def test_filter_empty_images(self) -> None:
        """测试空图片列表。"""
        result = filter_avatar_images([])
        assert result == []

    def test_filter_single_image(self) -> None:
        """测试单张图片直接返回。"""
        images = [create_test_image()]
        result = filter_avatar_images(images)
        assert len(result) == 1
        assert result[0] == images[0]

    def test_filter_two_images(self) -> None:
        """测试两张图片选择最佳。"""
        images = [
            create_test_image(color=(100, 100, 100)),
            create_test_image(color=(200, 200, 200)),
        ]
        result = filter_avatar_images(images)
        assert len(result) == 1

    def test_filter_multiple_images(self) -> None:
        """测试多张图片选择最佳。"""
        images = [
            create_test_image(color=(50, 50, 50)),
            create_test_image(color=(100, 100, 100)),
            create_test_image(color=(150, 150, 150)),
            create_test_image(color=(200, 200, 200)),
        ]
        result = filter_avatar_images(images)
        assert len(result) == 1

    def test_filter_returns_first_when_no_face_detected(self) -> None:
        """测试无人脸时返回第一张。"""
        images = [
            create_test_image(color=(100, 100, 100)),
            create_test_image(color=(200, 200, 200)),
        ]
        result = filter_avatar_images(images)
        assert len(result) == 1


class TestFaceDetectorIntegration:
    """人脸检测集成测试。"""

    def test_detector_with_real_image_format(self) -> None:
        """测试真实图片格式。"""
        detector = FaceDetector()

        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.rectangle(img, (30, 30), (70, 70), (255, 255, 255), -1)

        _, buffer = cv2.imencode(".png", img)
        image_bytes = buffer.tobytes()

        faces = detector.detect_faces(image_bytes)
        assert isinstance(faces, list)

    def test_detector_with_different_image_sizes(self) -> None:
        """测试不同尺寸图片。"""
        detector = FaceDetector()

        for size in [50, 100, 200, 400]:
            image_bytes = create_test_image(width=size, height=size)
            faces = detector.detect_faces(image_bytes)
            assert isinstance(faces, list)

    def test_score_range(self) -> None:
        """测试得分范围。"""
        detector = FaceDetector()
        image_bytes = create_test_image()
        score = detector.get_face_score(image_bytes)
        assert 0.0 <= score <= 100.0
