import React, { useMemo, useEffect } from 'react';
import { Task } from '../../../types';
import { select, extent, scaleTime, scaleBand, axisTop, timeFormat, timeWeek } from 'd3';

interface GanttViewProps {
  tasks: Task[];
}

export const GanttView: React.FC<GanttViewProps> = React.memo(({ tasks }) => {
  const svgRef = React.useRef<SVGSVGElement>(null);
  // PERFORMANCE: Pre-parse dates to avoid redundant string parsing allocations in the render loop.
  // We apply this only to valid items to avoid computing values for skipped items.
  const validTasks = useMemo(() => tasks
    .filter(d => d.due_date && d.created_at)
    .map(d => ({
        ...d,
        parsedCreatedAt: new Date(d.created_at!),
        parsedDueDate: new Date(d.due_date!)
    })), [tasks]);

  useEffect(() => {
    if (!svgRef.current || validTasks.length === 0) return;

    const margin = { top: 40, right: 30, bottom: 20, left: 150 };
    const width = 800 - margin.left - margin.right;
    const height = (validTasks.length * 40);

    const svg = select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const x = scaleTime()
      .domain(extent([...validTasks.map(d => d.parsedCreatedAt), ...validTasks.map(d => d.parsedDueDate)]) as [Date, Date])
      .range([0, width]);

    const y = scaleBand()
      .domain(validTasks.map(d => d.title))
      .range([0, height])
      .padding(0.2);

    g.append("g").attr("class", "x-axis").call(axisTop(x).ticks(timeWeek).tickFormat(timeFormat("%b %d") as any));

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? "#cbd5e1" : "#475569";

    g.append("g")
        .attr("class", "y-axis")
        .call(axis => axis.selectAll("text").remove()) // Hide default axis line
        .selectAll("text")
        .data(validTasks)
        .enter()
        .append("text")
        .text(d => d.title)
        .attr("x", -10)
        .attr("y", d => y(d.title)! + y.bandwidth() / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", "end")
        .style("font-size", "12px")
        .attr("fill", textColor);

    g.selectAll(".bar")
      .data(validTasks)
      .enter()
      .append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.parsedCreatedAt))
      .attr("y", d => y(d.title)!)
      .attr("width", d => x(d.parsedDueDate) - x(d.parsedCreatedAt))
      .attr("height", y.bandwidth())
      .attr("rx", 4)
      .attr("fill", "#6366f1")
      .attr("opacity", 0.8);

  }, [validTasks]);

  return (
    <div className="bg-white/50 backdrop-blur-sm rounded-2xl p-6 border border-white/50 shadow-sm overflow-x-auto custom-scrollbar">
      {validTasks.length > 0 ? (
        <svg ref={svgRef} width={800} height={(validTasks.length * 40) + 60} className="mx-auto" />
      ) : (
        <p className="text-gray-500 italic text-center py-10">No tasks with start and end dates to display in Gantt chart.</p>
      )}
    </div>
  );
});
