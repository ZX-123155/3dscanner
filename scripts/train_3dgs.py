"""
3D Gaussian Splatting 训练（基于 gsplat 1.5.x + pycolmap 加载）
用法: python scripts/train_3dgs.py --colmap <COLMAP工作目录> --out <输出目录>

核心流程：
1. pycolmap 加载 COLMAP 模型（新格式 OK，无需转换）
2. 从稀疏点云初始化高斯
3. gsplat rasterization 训练（Adam + densify）
4. 渲染环绕视频 + 保存模型
"""

import argparse
import math
import time
from pathlib import Path

import imageio
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch.optim import Adam

import gsplat
from gsplat import DefaultStrategy, rasterization
from loguru import logger


def ssim_loss(img1: torch.Tensor, img2: torch.Tensor, window_size: int = 11) -> torch.Tensor:
    """结构相似性损失（返回 1 - SSIM，值越大越差）"""
    if img1.dim() == 4:  # (1,H,W,3) -> (1,3,H,W)
        img1 = img1.permute(0, 3, 1, 2)
        img2 = img2.permute(0, 3, 1, 2)
    c1, c2 = 0.01**2, 0.03**2
    # 高斯窗口
    gauss = torch.arange(-window_size // 2 + 1, window_size // 2 + 1, dtype=img1.dtype, device=img1.device)
    gauss = torch.exp(-(gauss**2) / (2 * 1.5**2))
    gauss = gauss / gauss.sum()
    kernel = gauss[:, None] * gauss[None, :]
    kernel = kernel.expand(3, 1, window_size, window_size).contiguous()

    pad = window_size // 2
    mu1 = F.conv2d(F.pad(img1, (pad, pad, pad, pad), mode="replicate"), kernel, groups=3)
    mu2 = F.conv2d(F.pad(img2, (pad, pad, pad, pad), mode="replicate"), kernel, groups=3)
    mu1_sq, mu2_sq, mu1_mu2 = mu1**2, mu2**2, mu1 * mu2
    sigma1_sq = F.conv2d(F.pad(img1**2, (pad, pad, pad, pad), mode="replicate"), kernel, groups=3) - mu1_sq
    sigma2_sq = F.conv2d(F.pad(img2**2, (pad, pad, pad, pad), mode="replicate"), kernel, groups=3) - mu2_sq
    sigma12 = F.conv2d(F.pad(img1 * img2, (pad, pad, pad, pad), mode="replicate"), kernel, groups=3) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / ((mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2))
    return (1 - ssim_map.mean()) / 2  # 归一化到 [0,1]


def load_colmap_data(colmap_dir: Path, images_dir: Path, max_size: int = 1600):
    """用 pycolmap 加载模型，返回训练数据"""
    import pycolmap

    recon = pycolmap.Reconstruction(colmap_dir)
    logger.info(f"COLMAP 模型: {len(recon.images)} 图, {len(recon.points3D)} 点, {len(recon.cameras)} 相机")

    # 取注册图片（有序）
    image_list = sorted(recon.images.values(), key=lambda im: im.name)

    # 位姿与内参
    c2ws, Ks, image_names = [], [], []
    for img in image_list:
        pose = img.cam_from_world()  # world -> cam
        R = np.array(pose.rotation.matrix())
        t = np.array(pose.translation)
        w2c = np.eye(4)
        w2c[:3, :3] = R
        w2c[:3, 3] = t
        c2w = np.linalg.inv(w2c)
        c2ws.append(c2w)

        cam = recon.cameras[img.camera_id]
        if cam.model_name == "SIMPLE_RADIAL":
            fx = fy = cam.params[0]
            cx, cy = cam.params[1], cam.params[2]
        elif cam.model_name in ("PINHOLE", "SIMPLE_PINHOLE"):
            if cam.model_name == "SIMPLE_PINHOLE":
                fx = fy = cam.params[0]
                cx, cy = cam.params[1], cam.params[2]
            else:
                fx, fy = cam.params[0], cam.params[1]
                cx, cy = cam.params[2], cam.params[3]
        else:
            # OPENCV 等：取前 4 个参数
            fx, fy = cam.params[0], cam.params[1]
            cx, cy = cam.params[2], cam.params[3]
        K = np.array([[fx, 0, cx], [0, fy, cy], [0, 0, 1]], dtype=np.float32)
        Ks.append(K)
        image_names.append(img.name)

    # 加载图片并缩放到 max_size
    images, scales = [], []
    for name in image_names:
        with Image.open(images_dir / name) as im:
            img = np.array(im.convert("RGB"), dtype=np.float32) / 255.0
        h, w = img.shape[:2]
        s = min(max_size / max(h, w), 1.0)
        if s < 1.0:
            img = np.array(Image.fromarray((img * 255).astype(np.uint8)).resize(
                (int(w * s), int(h * s)), Image.BILINEAR), dtype=np.float32) / 255.0
        images.append(img)
        scales.append(s)

    # 稀疏点云 -> 高斯初始化
    points = np.array([p.xyz for p in recon.points3D.values()], dtype=np.float32)
    colors = np.array([p.color for p in recon.points3D.values()], dtype=np.float32) / 255.0

    return {
        "images": images,
        "c2ws": np.array(c2ws, dtype=np.float32),
        "Ks": np.array(Ks, dtype=np.float32),
        "scales": np.array(scales, dtype=np.float32),
        "names": image_names,
        "init_points": points,
        "init_colors": colors,
    }


def get_camera_rays(c2w, K, width, height):
    """从 c2w 和 K 构造 viewmat 和 K（gsplat 格式）"""
    viewmat = torch.linalg.inv(torch.tensor(c2w, dtype=torch.float32))
    K_t = torch.tensor(K, dtype=torch.float32)
    return viewmat, K_t


def render_360(data, params, num_frames: int = 60, out_path: Path = None, device="cuda"):
    """环绕视角渲染"""
    # 取第一个相机作为参考
    c2w0 = torch.tensor(data["c2ws"][0], dtype=torch.float32)
    center = c2w0[:3, 3].clone()
    # 平均相机位置做旋转中心
    all_c2w = torch.tensor(data["c2ws"], dtype=torch.float32)
    center = all_c2w[:, :3, 3].mean(dim=0)

    up = torch.tensor([0.0, 1.0, 0.0])
    radius = (all_c2w[0, :3, 3] - center).norm().item()

    h = data["images"][0].shape[0]
    w = data["images"][0].shape[1]

    frames = []
    for i in range(num_frames):
        theta = 2 * math.pi * i / num_frames
        cam_pos = center + torch.tensor([radius * math.cos(theta), 0.0, radius * math.sin(theta)])
        forward = (center - cam_pos) / torch.norm(center - cam_pos)
        right = torch.cross(forward, up)
        right = right / torch.norm(right)
        new_up = torch.cross(right, forward)
        rot = torch.stack([right, new_up, -forward], dim=1)
        c2w = torch.eye(4)
        c2w[:3, :3] = rot
        c2w[:3, 3] = cam_pos

        viewmat = torch.linalg.inv(c2w).to(device).unsqueeze(0)
        K = torch.tensor(data["Ks"][0], dtype=torch.float32).to(device).unsqueeze(0)

        with torch.no_grad():
            colors, alphas, _ = rasterization(
                params["means"],
                params["quats"],
                params["scales"],
                params["opacities"],
                params["sh0"] if "sh0" in params else params["colors"],
                viewmats=viewmat,
                Ks=K,
                width=w,
                height=h,
                sh_degree=0,
                backgrounds=torch.zeros(3, device=device),
            )
        img = colors[0].clamp(0, 1).cpu().numpy()
        frames.append((img * 255).astype(np.uint8))

    if out_path is not None:
        imageio.mimsave(out_path, frames, fps=24)
        logger.info(f"环绕视频已保存: {out_path}")
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(description="3DGS 训练")
    parser.add_argument("--colmap", type=Path, required=True, help="COLMAP 工作目录（含 images/ 和 sparse/0）")
    parser.add_argument("--out", type=Path, required=True, help="输出目录")
    parser.add_argument("--max-steps", type=int, default=30000)
    parser.add_argument("--max-size", type=int, default=1024, help="训练图片最大边")
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device(args.device)
    args.out.mkdir(parents=True, exist_ok=True)

    # 1. 加载数据
    sparse_model = args.colmap / "sparse" / "0"
    images_dir = args.colmap / "images"
    data = load_colmap_data(sparse_model, images_dir, max_size=args.max_size)
    N_imgs = len(data["images"])
    logger.info(f"加载完成: {N_imgs} 张图, 分辨率 {data['images'][0].shape}")

    # 2. 初始化高斯
    n_init = min(len(data["init_points"]), 100_000)
    idx = np.random.choice(len(data["init_points"]), n_init, replace=False)
    means = torch.tensor(data["init_points"][idx], dtype=torch.float32, device=device)
    init_colors = torch.tensor(data["init_colors"][idx], dtype=torch.float32, device=device)

    params = {
        "means": means.clone().requires_grad_(True),
        "scales": torch.log(torch.full((n_init, 3), 0.01, device=device)).requires_grad_(True),
        "quats": torch.tensor([1.0, 0.0, 0.0, 0.0], device=device).repeat(n_init, 1).requires_grad_(True),
        "opacities": torch.logit(torch.full((n_init,), 0.1, device=device)).requires_grad_(True),
        "sh0": init_colors.unsqueeze(1).clone().requires_grad_(True),  # (N,1,3) K=1
    }
    logger.info(f"初始化 {n_init} 个高斯")

    # 3. 优化器与 densify 策略
    # gsplat 要求：每个参数一个独立优化器（字典形式），便于 densify 时重置
    optimizer = {
        "means": Adam([params["means"]], lr=1.6e-4),
        "scales": Adam([params["scales"]], lr=5e-3),
        "quats": Adam([params["quats"]], lr=1e-3),
        "opacities": Adam([params["opacities"]], lr=5e-2),
        "sh0": Adam([params["sh0"]], lr=2.5e-3),
    }
    strategy = DefaultStrategy(verbose=True)
    strategy.check_sanity(params, optimizer)

    # 预计算每个相机的 viewmat/K
    viewmats, Ks = [], []
    for i in range(N_imgs):
        v, k = get_camera_rays(data["c2ws"][i], data["Ks"][i],
                               data["images"][i].shape[1], data["images"][i].shape[0])
        viewmats.append(v.to(device))
        Ks.append(k.to(device))

    # 4. 训练循环
    step = 0
    t0 = time.time()
    while step < args.max_steps:
        step += 1
        i = np.random.randint(N_imgs)
        img = torch.tensor(data["images"][i], dtype=torch.float32, device=device)
        gt = img.unsqueeze(0)  # (1,H,W,3)
        K = Ks[i].unsqueeze(0)
        vm = viewmats[i].unsqueeze(0)
        h, w = gt.shape[1], gt.shape[2]

        colors, alphas, info = rasterization(
            params["means"],
            params["quats"],
            params["scales"],
            params["opacities"],
            params["sh0"],
            viewmats=vm,
            Ks=K,
            width=w,
            height=h,
            sh_degree=0,
            backgrounds=torch.zeros(3, device=device),
        )

        # L1 + SSIM 损失
        l1 = F.l1_loss(colors, gt)
        ssim = ssim_loss(colors, gt)
        loss = 0.8 * l1 + 0.2 * ssim

        loss.backward()
        for opt in optimizer.values():
            opt.step()
            opt.zero_grad(set_to_none=True)

        # densify / prune
        strategy.step(step, params, optimizer, loss=loss.detach(), info=info)

        if step % 1000 == 0:
            elapsed = time.time() - t0
            logger.info(
                f"step {step}/{args.max_steps} | loss={loss.item():.4f} l1={l1.item():.4f} "
                f"ssim={ssim.item():.4f} | {elapsed:.0f}s | gaussians={params['means'].shape[0]}"
            )

    logger.info(f"训练完成，用时 {(time.time()-t0)/60:.1f} 分钟，最终高斯数 {params['means'].shape[0]}")

    # 5. 保存模型
    torch.save(params, args.out / "model.pt")
    logger.info(f"模型已保存: {args.out / 'model.pt'}")

    # 6. 渲染环绕视频
    render_360(data, params, num_frames=60, out_path=args.out / "orbit.mp4", device=device)

    # 7. 导出 PLY（兼容 3DGS 查看器）
    from gsplat.exporter import export_splats
    export_splats(
        means=params["means"],
        scales=torch.exp(params["scales"]),
        quats=params["quats"],
        opacities=torch.sigmoid(params["opacities"]),
        sh0=params["sh0"],
        shN=None,
        format="ply",
        save_to=str(args.out / "model.ply"),
    )
    logger.info(f"PLY 已导出: {args.out / 'model.ply'}")


if __name__ == "__main__":
    main()
