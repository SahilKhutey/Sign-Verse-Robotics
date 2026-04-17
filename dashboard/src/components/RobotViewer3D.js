import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera, Grid, Stars } from '@react-three/drei';
import { useStore } from '../store/useStore';

function HumanoidRig() {
  const jointAngles = useStore((state) => state.jointAngles);
  const robotRef = useRef();

  useFrame(() => {
    if (robotRef.current) {
      // Update rotations for visible elements based on 30Hz telemetry
      // This maps the 'robot_payload' dictionary to 3D bones
      // robotRef.current.rotation.y += 0.01; // Example animation
    }
  });

  return (
    <group ref={robotRef}>
      {/* Dynamic Skeletal visualization of the humanoid */}
      <mesh position={[0, 0.9, 0]}>
        <boxGeometry args={[0.3, 0.6, 0.2]} />
        <meshStandardMaterial color="#00ff00" wireframe />
      </mesh>
      {/* Legs simulation based on contact forces */}
      <mesh position={[-0.1, 0.3, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 0.6]} />
        <meshStandardMaterial color="#00ffff" />
      </mesh>
      <mesh position={[0.1, 0.3, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 0.6]} />
        <meshStandardMaterial color="#00ffff" />
      </mesh>
    </group>
  );
}

export default function RobotViewer3D() {
  return (
    <div className="w-full h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
      <Canvas>
        <PerspectiveCamera makeDefault position={[3, 2, 5]} />
        <OrbitControls />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        <Grid infiniteGrid cellSize={1} sectionSize={5} fadeDistance={30} />
        <HumanoidRig />
      </Canvas>
    </div>
  );
}
