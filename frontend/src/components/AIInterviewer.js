import React, { useEffect, useRef } from 'react';

function AIInterviewer({ state = 'idle' }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const waveBarCountRef = useRef(60);
  const waveHeightsRef = useRef([]);
  const animationFrameRef = useRef(null);

  const particleCount = 150;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = 500;
    canvas.height = 300;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Initialize particles
    particlesRef.current = Array.from({ length: particleCount }, () => ({
      angle: Math.random() * Math.PI * 2,
      radius: Math.random() * 180 + 60,
      orbitSpeed: (Math.random() - 0.5) * 0.015,
      size: Math.random() * 3 + 1,
      opacity: Math.random() * 0.7 + 0.3,
      colorOffset: Math.random() * 80,
    }));

    // Initialize wave bars
    waveHeightsRef.current = Array.from({ length: waveBarCountRef.current }, () => Math.random());

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // === DRAW SOUND WAVE BARS (BACKGROUND) ===
      const barWidth = canvas.width / waveBarCountRef.current;
      const time = Date.now() * 0.001;

      for (let i = 0; i < waveBarCountRef.current; i++) {
        // Animate wave heights with sine wave
        const targetHeight = (Math.sin(time * 2 + i * 0.2) * 0.5 + 0.5) * 0.8 + 0.2;
        waveHeightsRef.current[i] += (targetHeight - waveHeightsRef.current[i]) * 0.1;

        const barHeight = waveHeightsRef.current[i] * (canvas.height * 0.6);
        const x = i * barWidth;
        const y = (canvas.height - barHeight) / 2;

        // Gradient color for bars
        const gradient = ctx.createLinearGradient(x, y, x, y + barHeight);
        gradient.addColorStop(0, 'rgba(0, 240, 255, 0.1)');
        gradient.addColorStop(0.5, 'rgba(99, 102, 241, 0.15)');
        gradient.addColorStop(1, 'rgba(0, 240, 255, 0.1)');

        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth - 2, barHeight);

        // Glow effect on bars
        ctx.shadowBlur = 15;
        ctx.shadowColor = 'rgba(0, 240, 255, 0.3)';
      }

      ctx.shadowBlur = 0;

      // === DRAW PARTICLES (FOREGROUND) ===
      particlesRef.current.forEach((particle, index) => {
        // Orbit animation
        particle.angle += particle.orbitSpeed;

        // Dynamic radius based on time (pulsing effect)
        const pulse = Math.sin(time * 1.5 + index * 0.1) * 10;
        const currentRadius = particle.radius + pulse;

        const x = centerX + Math.cos(particle.angle) * currentRadius;
        const y = centerY + Math.sin(particle.angle) * currentRadius;

        // Dynamic size
        const sizePulse = Math.sin(time * 2 + index * 0.15) * 0.5 + 1;

        // Color - cyan to purple gradient
        const hue = 180 + particle.colorOffset + (Math.sin(time + index) * 20);

        // Draw particle glow
        ctx.shadowBlur = 20;
        ctx.shadowColor = `hsla(${hue}, 100%, 60%, 0.9)`;

        ctx.beginPath();
        ctx.arc(x, y, particle.size * sizePulse, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${hue}, 100%, 70%, ${particle.opacity})`;
        ctx.fill();

        // Draw connections between nearby particles
        particlesRef.current.forEach((other, otherIndex) => {
          if (otherIndex <= index) return;

          const otherPulse = Math.sin(time * 1.5 + otherIndex * 0.1) * 10;
          const otherRadius = other.radius + otherPulse;
          const otherX = centerX + Math.cos(other.angle) * otherRadius;
          const otherY = centerY + Math.sin(other.angle) * otherRadius;
          const distance = Math.sqrt((x - otherX) ** 2 + (y - otherY) ** 2);

          if (distance < 100) {
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(otherX, otherY);
            ctx.strokeStyle = `hsla(${hue}, 100%, 60%, ${0.2 * (1 - distance / 100)})`;
            ctx.lineWidth = 1;
            ctx.shadowBlur = 5;
            ctx.stroke();
          }
        });
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [state]);

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        position: 'relative',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          maxWidth: '100%',
          height: 'auto',
          filter: 'blur(0.3px)',
        }}
      />
    </div>
  );
}

export default AIInterviewer;