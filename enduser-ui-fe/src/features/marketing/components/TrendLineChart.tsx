import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface TrendData {
    date: string;
    [key: string]: string | number;
}

interface TrendLineChartProps {
    data: TrendData[];
}

export const TrendLineChart: React.FC<TrendLineChartProps> = ({ data }) => {
    // Dynamically extract keys that are not 'date'
    const keys = data.length > 0 ? Object.keys(data[0]).filter(k => k !== 'date') : [];
    const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300'];

    return (
        <ResponsiveContainer width="100%" height={300}>
            <LineChart
                data={data}
                margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                }}
            >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }}
                    itemStyle={{ color: '#d1d5db' }}
                />
                <Legend />
                {keys.map((key, index) => (
                    <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={colors[index % colors.length]}
                        activeDot={{ r: 8 }}
                        strokeWidth={2}
                    />
                ))}
            </LineChart>
        </ResponsiveContainer>
    );
};
