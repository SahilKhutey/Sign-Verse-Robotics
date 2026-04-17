import { create } from 'zustand';

export const useStore = create((set) => ({
  // Telemetry State
  intent: 'IDLE',
  confidence: 0,
  stabilityHealth: 1.0,
  reward: 0,
  jointAngles: {},
  contactForces: [0, 0, 0],
  
  // System Controls
  isRecording: false,
  isSimulationRunning: true,
  
  // Setters
  updateTelemetry: (data) => set({
    intent: data.intent || 'IDLE',
    confidence: data.confidence || 0,
    stabilityHealth: data.stability_health !== undefined ? data.stability_health : 1.0,
    reward: data.reward || 0,
    jointAngles: data.robot_payload || {},
    contactForces: data.contact_forces || [0, 0, 0]
  }),
  
  setRecording: (status) => set({ isRecording: status }),
  setSimRunning: (status) => set({ isSimulationRunning: status })
}));
