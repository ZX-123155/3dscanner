"""
COLMAP 4.x 新格式 -> 旧版标准 BIN 格式（3DGS 生态兼容）
用法: python scripts/convert_model.py <输入模型目录> <输出目录>
"""

import struct
import sys
from pathlib import Path

import pycolmap
import numpy as np

# COLMAP 旧版相机模型 ID（与 3DGS 兼容）
CAMERA_MODEL_IDS = {
    "SIMPLE_PINHOLE": 0,
    "PINHOLE": 1,
    "SIMPLE_RADIAL": 2,
    "RADIAL": 3,
    "OPENCV": 4,
    "OPENCV_FISHEYE": 5,
    "FULL_OPENCV": 6,
    "FOV": 7,
    "SIMPLE_RADIAL_FISHEYE": 8,
    "RADIAL_FISHEYE": 9,
    "THIN_PRISM_FISHEYE": 10,
}


def write_cameras_bin(cameras: dict, path: Path) -> None:
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(cameras)))
        for cam in cameras.values():
            model_id = CAMERA_MODEL_IDS.get(cam.model_name, 0)
            f.write(struct.pack("<ii", cam.camera_id, model_id))
            f.write(struct.pack("<ii", cam.width, cam.height))
            params = cam.params.astype(np.float64)
            f.write(struct.pack("<d", len(params)))
            f.write(params.tobytes())


def write_images_bin(images: dict, path: Path) -> None:
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(images)))
        for img in images.values():
            # 4x4 位姿矩阵 -> 四元数+平移 (COLMAP convention)
            pose = img.cam_from_world()
            qvec = np.array(pose.rotation.quat)  # [x,y,z,w]
            qw, qx, qy, qz = qvec[3], qvec[0], qvec[1], qvec[2]
            t = np.array(pose.translation)
            f.write(struct.pack("<Q", img.image_id))
            f.write(struct.pack("<dddd", qw, qx, qy, qz))
            f.write(struct.pack("<ddd", t[0], t[1], t[2]))
            f.write(struct.pack("<i", img.camera_id))
            name = img.name.encode("utf-8")
            f.write(struct.pack("<I", len(name)))
            f.write(name)
            pts = img.points2D
            f.write(struct.pack("<Q", len(pts)))
            if len(pts) > 0:
                # 写入 x,y 坐标（float64）和 3D 点索引
                coords = np.array([p.xy for p in pts], dtype=np.float64)
                f.write(coords.tobytes())
                ids = np.array([p.point3D_id if p.has_point3D() else -1 for p in pts], dtype=np.int64)
                f.write(ids.tobytes())


def write_points3d_bin(points3d: dict, path: Path) -> None:
    with open(path, "wb") as f:
        f.write(struct.pack("<Q", len(points3d)))
        for pid, p3 in points3d.items():
            xyz = np.array(p3.xyz, dtype=np.float64)
            rgb = np.array(p3.color, dtype=np.uint8)
            err = float(p3.error)
            f.write(struct.pack("<Q", pid))
            f.write(xyz.tobytes())
            f.write(rgb.tobytes())
            f.write(struct.pack("<d", err))
            # track: image_id + point2D_idx 对
            track = [(t.image_id, t.point2D_idx) for t in p3.track.elements]
            f.write(struct.pack("<Q", len(track)))
            for image_id, idx in track:
                f.write(struct.pack("<iq", image_id, idx))


def rotmat_to_quat(R: np.ndarray) -> tuple:
    """旋转矩阵 -> (qw, qx, qy, qz)"""
    tr = R[0, 0] + R[1, 1] + R[2, 2]
    if tr > 0:
        s = 2.0 * np.sqrt(tr + 1.0)
        qw = 0.25 * s
        qx = (R[2, 1] - R[1, 2]) / s
        qy = (R[0, 2] - R[2, 0]) / s
        qz = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        qw = (R[2, 1] - R[1, 2]) / s
        qx = 0.25 * s
        qy = (R[0, 1] + R[1, 0]) / s
        qz = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        qw = (R[0, 2] - R[2, 0]) / s
        qx = (R[0, 1] + R[1, 0]) / s
        qy = 0.25 * s
        qz = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        qw = (R[1, 0] - R[0, 1]) / s
        qx = (R[0, 2] + R[2, 0]) / s
        qy = (R[1, 2] + R[2, 1]) / s
        qz = 0.25 * s
    return qw, qx, qy, qz


def convert(input_dir: Path, output_dir: Path) -> None:
    recon = pycolmap.Reconstruction(input_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_cameras_bin(recon.cameras, output_dir / "cameras.bin")
    write_images_bin(recon.images, output_dir / "images.bin")
    write_points3d_bin(recon.points3D, output_dir / "points3D.bin")

    print(f"转换完成: {input_dir} -> {output_dir}")
    print(f"  相机数: {len(recon.cameras)}, 图片数: {len(recon.images)}, 点云数: {len(recon.points3D)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python convert_model.py <输入模型目录> <输出目录>")
        sys.exit(1)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
