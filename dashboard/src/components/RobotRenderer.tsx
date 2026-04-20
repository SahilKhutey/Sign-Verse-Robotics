"use client";

import React, { useRef, useEffect } from 'react';

interface RobotRendererProps {
  jointAngles: Record<string, number>;
  width?: number;
  height?: number;
}

/**
 * High-performance Canvas Renderer for Robotic Armatures.
 * Visualizes output joint states (Degrees) as a kinematic model.
 */
export default function RobotRenderer({ jointAngles, width = 640, height = 480 }: RobotRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    // Draw Robot Body / Links
    const centerX = width / 2;
    const centerY = height / 3;
    const linkLen = 80;

    // Helper to convert deg to rad
    const rad = (deg: number) => (deg * Math.PI) / 180;

    ctx.strokeStyle = '#ff9100'; // Robot Primary Orange
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';

    // 1. Draw Torso
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(centerX, centerY + 120);
    ctx.stroke();

    // 2. Draw Shoulders Link
    ctx.beginPath();
    ctx.moveTo(centerX - 40, centerY);
    ctx.lineTo(centerX + 40, centerY);
    ctx.stroke();

    // 3. Draw Left Arm
    const l_sh_pitch = jointAngles["l_shoulder_pitch"] || 0;
    const l_el_pitch = jointAngles["l_elbow_pitch"] || 0;

    const lx1 = centerX - 40;
    const ly1 = centerY;
    const lx2 = lx1 - linkLen * Math.cos(rad(l_sh_pitch - 90));
    const ly2 = ly1 + linkLen * Math.sin(rad(l_sh_pitch - 90));
    const lx3 = lx2 - linkLen * Math.cos(rad(l_sh_pitch + l_el_pitch - 90));
    const ly3 = ly2 + linkLen * Math.sin(rad(l_sh_pitch + l_el_pitch - 90));

    ctx.strokeStyle = '#ff9100';
    ctx.beginPath();
    ctx.moveTo(lx1, ly1);
    ctx.lineTo(lx2, ly2);
    ctx.lineTo(lx3, ly3);
    ctx.stroke();

    // 4. Draw Right Arm
    const r_sh_pitch = jointAngles["r_shoulder_pitch"] || 0;
    const r_el_pitch = jointAngles["r_elbow_pitch"] || 0;

    const rx1 = centerX + 40;
    const ry1 = centerY;
    const rx2 = rx1 + linkLen * Math.cos(rad(r_sh_pitch - 90));
    const ry2 = ry1 + linkLen * Math.sin(rad(r_sh_pitch - 90));
    const rx3 = rx2 + linkLen * Math.cos(rad(r_sh_pitch + r_el_pitch - 90));
    const ry3 = ry2 + linkLen * Math.sin(rad(r_sh_pitch + r_el_pitch - 90));

    ctx.beginPath();
    ctx.moveTo(rx1, ry1);
    ctx.lineTo(rx2, ry2);
    ctx.lineTo(rx3, ry3);
    ctx.stroke();

    // Draw Joints
    ctx.fillStyle = '#ffffff';
    [[lx1, ly1], [lx2, ly2], [lx3, ly3], [rx1, ry1], [rx2, ry2], [rx3, ry3], [centerX, centerY + 120]].forEach(([px, py]) => {
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fill();
    });

  }, [jointAngles, width, height]);

  return (
    <canvas 
      ref={canvasRef} 
      width={width} 
      height={height} 
      className="w-full h-full object-contain bg-neutral-950/40 rounded-2xl"
    />
  );
}
