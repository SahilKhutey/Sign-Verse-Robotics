"use client";

import React, { useRef, useEffect } from 'react';

const HAND_CONNECTIONS: [number, number][] = [
  [0, 1], [1, 2], [2, 3], [3, 4],
  [0, 5], [5, 6], [6, 7], [7, 8],
  [5, 9], [9, 10], [10, 11], [11, 12],
  [9, 13], [13, 14], [14, 15], [15, 16],
  [13, 17], [17, 18], [18, 19], [19, 20],
  [0, 17],
];

interface HandRendererProps {
  joints: number[][]; // (21, 3) landmarks
  width?: number;
  height?: number;
  color?: string;
}

/**
 * Specialized Canvas Renderer for fine-motor Hand Skeletons.
 */
export default function HandRenderer({ joints, width = 640, height = 480, color = '#ff00ff' }: HandRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);
    if (!joints || joints.length === 0) return;

    // 1. Draw Bones
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    HAND_CONNECTIONS.forEach(([i, j]) => {
      const start = joints[i];
      const end = joints[j];
      if (start && end) {
        ctx.beginPath();
        ctx.moveTo(start[0] * width, start[1] * height);
        ctx.lineTo(end[0] * width, end[1] * height);
        ctx.stroke();
      }
    });

    // 2. Draw Joints
    ctx.fillStyle = '#ffffff';
    joints.forEach((joint) => {
        ctx.beginPath();
        ctx.arc(joint[0] * width, joint[1] * height, 5, 0, 2 * Math.PI);
        ctx.fill();
    });

  }, [joints, width, height, color]);

  return (
    <canvas 
      ref={canvasRef} 
      width={width} 
      height={height} 
      className="w-full h-full object-contain bg-neutral-950/50 rounded-xl"
    />
  );
}
