"use client";

import React, { useRef, useEffect } from 'react';

const BONE_CONNECTIONS: [number, number][] = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24],
  [23, 25], [25, 27], [24, 26], [26, 28],
  [27, 31], [28, 32],
];

interface SkeletonRendererProps {
  joints: number[][];
  width?: number;
  height?: number;
}

function buildProjector(joints: number[][], width: number, height: number) {
  const valid = joints.filter((joint) => Array.isArray(joint) && joint.length >= 2 && Number.isFinite(joint[0]) && Number.isFinite(joint[1]));
  if (valid.length === 0) {
    return () => ({ x: 0, y: 0 });
  }

  const xs = valid.map((joint) => joint[0]);
  const ys = valid.map((joint) => joint[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const spanX = Math.max(maxX - minX, 1e-6);
  const spanY = Math.max(maxY - minY, 1e-6);
  const normalizedInput = minX >= -0.1 && maxX <= 1.1 && minY >= -0.1 && maxY <= 1.1;

  if (normalizedInput) {
    return (joint: number[]) => ({
      x: joint[0] * width,
      y: joint[1] * height,
    });
  }

  const padding = 0.12;
  const usableWidth = width * (1 - padding * 2);
  const usableHeight = height * (1 - padding * 2);
  const scale = Math.min(usableWidth / spanX, usableHeight / spanY);
  const offsetX = (width - (spanX * scale)) / 2;
  const offsetY = (height - (spanY * scale)) / 2;

  return (joint: number[]) => ({
    x: offsetX + ((joint[0] - minX) * scale),
    y: offsetY + ((joint[1] - minY) * scale),
  });
}

export default function SkeletonRenderer({ joints, width = 640, height = 480 }: SkeletonRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);
    if (!joints || joints.length === 0) return;

    const project = buildProjector(joints, width, height);

    ctx.strokeStyle = '#00f2ff';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    BONE_CONNECTIONS.forEach(([i, j]) => {
      const start = joints[i];
      const end = joints[j];
      if (!start || !end) return;

      const p1 = project(start);
      const p2 = project(end);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    });

    ctx.fillStyle = '#ffffff';
    joints.forEach((joint, idx) => {
      if (!joint || idx >= 33) return;
      const point = project(joint);
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, 2 * Math.PI);
      ctx.fill();
    });
  }, [joints, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      className="w-full h-full object-contain bg-neutral-950 rounded-lg shadow-inner ring-1 ring-outline-variant/20"
    />
  );
}
