"use client";

import React, { useEffect, useState } from 'react';
import type { TrainingMetrics } from '@/types/telemetry';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area 
} from 'recharts';

interface TrainingChartProps {
  data: TrainingMetrics[];
  dataKey: keyof TrainingMetrics;
  color?: string;
  name: string;
  detailMode?: boolean;
}

export default function TrainingChart({ data, dataKey, color = "#00f2ff", name, detailMode = false }: TrainingChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="w-full h-full min-h-[200px] min-w-0">
      {!mounted ? null : (
      <ResponsiveContainer width="100%" height="100%">
        {detailMode ? (
          <AreaChart data={data}>
            <defs>
              <linearGradient id={`color${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={color} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
            <XAxis 
              dataKey="epoch" 
              stroke="#555" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false}
              label={{ value: 'Epoch', position: 'insideBottom', offset: -5, fill: '#555', fontSize: 10 }}
            />
            <YAxis 
              stroke="#555" 
              fontSize={10} 
              tickLine={false} 
              axisLine={false}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px', fontSize: '10px' }}
              itemStyle={{ color: color }}
            />
            <Area 
              type="monotone" 
              dataKey={dataKey} 
              stroke={color} 
              fillOpacity={1} 
              fill={`url(#color${dataKey})`} 
              strokeWidth={2}
              name={name}
              animationDuration={500}
            />
          </AreaChart>
        ) : (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
            <XAxis dataKey="epoch" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Tooltip 
               contentStyle={{ backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px', fontSize: '10px' }}
            />
            <Line 
              type="monotone" 
              dataKey={dataKey} 
              stroke={color} 
              strokeWidth={3} 
              dot={false}
              name={name}
              animationDuration={300}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
      )}
    </div>
  );
}
