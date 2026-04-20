import { create } from 'zustand';
import type { HealthReport, TelemetryMetrics, TrainingMetrics } from '@/types/telemetry';

function hasMetrics(data: HealthReport | TelemetryMetrics): data is HealthReport {
  return typeof data === 'object' && data !== null && 'metrics' in data;
}

interface StoreState {
  intent: string;
  confidence: number;
  stabilityHealth: number;
  rlLatency: number;
  controlLatency: number;
  reward: number;
  fps: number;
  skeletonVersion: string;
  jointAngles: Record<string, number>;
  contactForces: number[];
  cpuUsage: number;
  robotVelocity: number[];
  totalPowerDrain: number;
  handEmbedding: number[];
  handJoints: number[][];
  bridgeStatus: { blender: boolean; isaac: boolean };
  trainingHistory: TrainingMetrics[];
  trainingMetrics: TrainingMetrics;
  isRecording: boolean;
  isSimulationRunning: boolean;
  isConnected: boolean;
  isConnecting: boolean;
  updateTelemetry: (data: HealthReport | TelemetryMetrics) => void;
  setConnectionStatus: (status: boolean) => void;
  setRecording: (status: boolean) => void;
  setSimRunning: (status: boolean) => void;
}

export const useStore = create<StoreState>((set) => ({
  // Telemetry State
  intent: 'OFFLINE',
  confidence: 0,
  stabilityHealth: 1.0,
  rlLatency: 0,
  controlLatency: 0,
  reward: 0,
  fps: 0,
  skeletonVersion: "v.2.4 (Full)", // Default fallback
  jointAngles: {},
  contactForces: [0, 0, 0],
  
  // New Stitch Telemetry Fields
  cpuUsage: 0.0,
  robotVelocity: [0.0, 0.0, 0.0],
  totalPowerDrain: 120.0,
  handEmbedding: [],
  handJoints: [],
  bridgeStatus: { blender: false, isaac: false },
  trainingHistory: [],
  trainingMetrics: {
    epoch: 0,
    loss: 0.0,
    accuracy: 0.0,
    val_loss: 0.0,
    dataset_size: 0,
    is_training: false
  },
  
  // System Controls
  isRecording: false,
  isSimulationRunning: true,
  isConnected: false,
  isConnecting: true,
  
  // Setters
  updateTelemetry: (data) => {
    let metrics: TelemetryMetrics = {};
    if (hasMetrics(data) && data.metrics && data.metrics.global) {
        metrics = data.metrics.global;
    } else if (hasMetrics(data) && data.metrics && Object.keys(data.metrics).length > 0) {
        metrics = Object.values(data.metrics)[0] as TelemetryMetrics;
    } else {
        metrics = data as TelemetryMetrics;
    }
    
    // High-Frequency Update: 3D Visualization layer
    set({
      isConnected: true,
      isConnecting: false,
      jointAngles: metrics.robot_payload || {},
      handEmbedding: metrics.hand_embedding || [],
      handJoints: metrics.hand_joints || [],
    });

    // Lazy Update: UI Metrics layer
    set({
      intent: metrics.current_intent || 'IDLE',
      confidence: metrics.intent_confidence || 0,
      stabilityHealth: metrics.stability_health !== undefined ? metrics.stability_health : 1.0,
      rlLatency: metrics.rl_latency_ms || 0,
      controlLatency: metrics.control_latency_ms || 0,
      reward: metrics.reward || 0,
      fps: metrics.fps || 0.0,
      skeletonVersion: metrics.skeleton_version || "v.3.2 (Full)",
      contactForces: metrics.contact_forces || [0, 0, 0],
      cpuUsage: metrics.cpu_usage || 0.0,
      robotVelocity: metrics.robot_velocity || [0.0, 0.0, 0.0],
      totalPowerDrain: metrics.total_power_drain || 120.0,
      bridgeStatus: metrics.bridge_status || { blender: false, isaac: false },
      isRecording: hasMetrics(data) ? (data.is_recording ?? false) : false
    });

    // Update Training History (maintain last 50 epochs)
    if (metrics.training) {
        set((state) => {
            const training = metrics.training as TrainingMetrics;
            const lastEpoch = state.trainingHistory[state.trainingHistory.length - 1]?.epoch || -1;
            const newEpoch = training.epoch;
            
            let updatedHistory = state.trainingHistory;
            if (newEpoch > lastEpoch && training.is_training) {
                updatedHistory = [...state.trainingHistory, { ...training }].slice(-50);
            }
            
            return {
                trainingMetrics: training,
                trainingHistory: updatedHistory
            };
        });
    }
  },
  
  setConnectionStatus: (status: boolean) => set({ isConnected: status, isConnecting: false }),
  setRecording: (status: boolean) => set({ isRecording: status }),
  setSimRunning: (status: boolean) => set({ isSimulationRunning: status })
}));
