"use client";

import Image from 'next/image';
import React, { useEffect, useRef } from 'react';
import { Terminal, Settings, Bell } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { wsUrl } from '@/lib/api';

export default function Topbar() {
  const { isConnected, updateTelemetry, setConnectionStatus } = useStore();
  const latestMessageRef = useRef<string | null>(null);

  useEffect(() => {
    let socket: WebSocket;
    let reconnectTimeout: NodeJS.Timeout | undefined;
    const flushInterval = setInterval(() => {
      if (!latestMessageRef.current) return;
      try {
        const data = JSON.parse(latestMessageRef.current);
        latestMessageRef.current = null;
        updateTelemetry(data);
      } catch {
        latestMessageRef.current = null;
      }
    }, 100);
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      reconnectTimeout = setTimeout(() => {
        if (disposed) return;
        console.log("[STITCH-HUD] Initiating global telemetry uplink...");
        socket = new WebSocket(wsUrl('/ws/telemetry'));
        
        socket.onopen = () => {
          setConnectionStatus(true);
        };

        socket.onmessage = (event) => {
          latestMessageRef.current = event.data;
        };

        socket.onclose = () => {
          if (disposed) return;
          setConnectionStatus(false);
          connect(); // Retry recursive
        };
      }, 500);
    };

    connect();
    return () => {
      disposed = true;
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (flushInterval) clearInterval(flushInterval);
    };
  }, [updateTelemetry, setConnectionStatus]);

  return (
    <header className="bg-neutral-950/80 backdrop-blur-xl font-space-grotesk uppercase tracking-tighter docked full-width top-0 z-50 shadow-[0_8px_32px_rgba(0,123,255,0.1)] fixed left-0 right-0">
      <div className="flex justify-between items-center w-full px-6 py-3">
        <div className="flex items-center gap-8">
          <div className="text-xl font-bold text-primary tracking-widest">Sign-Verse Control</div>
          <nav className="hidden md:flex items-center gap-6 text-[10px]">
            <a className="text-neutral-500 hover:text-neutral-300 transition-colors" href="#">Systems</a>
            <a className="text-neutral-500 hover:text-neutral-300 transition-colors" href="#">Protocols</a>
            <a className="text-neutral-500 hover:text-neutral-300 transition-colors" href="#">Diagnostics</a>
          </nav>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 px-3 py-1 bg-neutral-900/50 rounded-lg border border-outline-variant/10">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-tertiary glow-green' : 'bg-error'}`}></span>
            <span className={`text-[10px] font-bold ${isConnected ? 'text-blue-400' : 'text-error'}`}>
               {isConnected ? 'Backend Link Active' : 'Backend Offline'}
            </span>
          </div>
          <div className="flex items-center gap-4 text-neutral-500">
            <Terminal className="w-5 h-5 cursor-pointer hover:text-blue-300 transition-colors" />
            <Settings className="w-5 h-5 cursor-pointer hover:text-blue-300 transition-colors" />
            <div className="relative">
              <Bell className="w-5 h-5 cursor-pointer hover:text-blue-300 transition-colors" />
              <span className="absolute top-0 right-0 w-1.5 h-1.5 bg-error rounded-full"></span>
            </div>
            <Image 
              alt="Chief Research Officer" 
              className="w-8 h-8 rounded-lg border border-outline-variant/20 object-cover" 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDQmwoaxyqbzG2zk9HopPXU2j_5de_ReBxFNAQlmv8Mz_zNxSovnV5niRHd_eE2wUxoOsnO2Jyd1pX3Jphywh3Ij8peCijpbA8jSrxliHgZkxC6s6xqGVT0R7Qg-sED76NNFPA7rTf8QS8Ekms6q9O3pmqY69ONHQsIxfvI79z74oM5UFxNyCJ2O04dINd2670FVCpto2zC139kPi6jXdD74QJBvYRy3k2tqE9w6ciqEvscLGQuHxmr0ShRzS5tmYemIF7oLTmR75c"
              width={32}
              height={32}
            />
          </div>
        </div>
      </div>
    </header>
  );
}
