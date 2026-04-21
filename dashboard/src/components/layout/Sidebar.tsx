"use client";

import React from 'react';
import { Terminal, Zap, Database, Activity, MonitorPlay, Focus, Cpu, Glasses, Sliders, History } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Dashboard', icon: Activity },
    { href: '/capture', label: 'Capture Studio', icon: MonitorPlay },
    { href: '/dataset', label: 'Dataset Manager', icon: Database },
    { href: '/jobs', label: 'Job History', icon: History },
    { href: '/timeline', label: 'Motion Timeline', icon: Sliders },
    { href: '/pose', label: 'Pose & Gesture Lab', icon: Focus },
    { href: '/retargeting', label: 'Robot Retargeting', icon: Cpu },
    { href: '/simulation', label: 'Simulation', icon: Glasses },
    { href: '/training', label: 'Training Monitor', icon: Activity },
  ];

  return (
    <aside className="bg-neutral-950 font-jetbrains-mono text-xs uppercase h-screen w-64 fixed left-0 top-0 border-r border-neutral-800/30 flex flex-col pt-20 pb-8 z-40">
      <div className="px-6 mb-8">
        <div className="flex items-center gap-3 mb-1">
          <Database className="w-6 h-6 text-primary" />
          <h2 className="font-space-grotesk font-black text-primary tracking-tighter">SYNTHETIC LAB</h2>
        </div>
        <p className="text-[9px] text-neutral-600 tracking-[0.2em]">V.04-ALFA</p>
      </div>
      
      <nav className="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
        {links.map((link) => {
          const isActive = pathname === link.href;
          const Icon = link.icon;
          
          return (
            <Link 
              key={link.href}
              href={link.href}
              className={`py-3 px-6 flex items-center gap-3 transition-all cursor-crosshair ${
                isActive 
                  ? 'bg-neutral-800/80 text-blue-400 border-l-4 border-primary' 
                  : 'text-neutral-600 hover:bg-neutral-900 hover:text-neutral-200'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span>{link.label}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="px-6 mt-6 space-y-4">
        <button className="w-full bg-gradient-to-tr from-primary to-primary-container text-on-primary py-3 rounded-lg font-bold text-[10px] tracking-widest uppercase hover:opacity-90 transition-opacity flex items-center justify-center gap-2">
          <Zap className="w-4 h-4" />
          Deploy Pipeline
        </button>
        <div className="pt-6 border-t border-neutral-800/30 flex flex-col gap-2">
          <a className="text-neutral-600 hover:text-blue-300 transition-all flex items-center gap-3" href="#">
            <span className="material-symbols-outlined text-sm">segment</span>
            Logs
          </a>
          <a className="text-neutral-600 hover:text-blue-300 transition-all flex items-center gap-3" href="#">
            <Terminal className="w-4 h-4" />
            Terminal
          </a>
        </div>
      </div>
    </aside>
  );
}
