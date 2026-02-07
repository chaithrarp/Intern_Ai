import React, { useEffect, useRef } from 'react';

function MiniAIOrb({ state = 'idle' }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const animationFrameRef = useRef(null);

  const particleCount = 40;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = 150;
    canvas.height = 150;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    // Initialize particles
    particlesRef.current = Array.from({ length: particleCount }, () => ({
      angle: Math.random() * Math.PI * 2,
      radius: Math.random() * 40 + 20,
      orbitSpeed: (Math.random() - 0.5) * 0.02,
      size: Math.random() * 2 + 0.5,
      opacity: Math.random() * 0.6 + 0.4,
    }));

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const time = Date.now() * 0.001;

      // State-based colors
      let color, glowColor;
      switch (state) {
        case 'listening':
          color = '#10b981'; // Green
          glowColor = 'rgba(16, 185, 129, 0.8)';
          break;
        case 'thinking':
          color = '#f59e0b'; // Amber
          glowColor = 'rgba(245, 158, 11, 0.8)';
          break;
        case 'speaking':
          color = '#6366f1'; // Purple
          glowColor = 'rgba(99, 102, 241, 0.8)';
          break;
        default: // idle/waiting
          color = '#00f0ff'; // Cyan
          glowColor = 'rgba(0, 240, 255, 0.8)';
      }

      // Draw particles
      particlesRef.current.forEach((particle, index) => {
        particle.angle += particle.orbitSpeed;

        const pulse = Math.sin(time * 2 + index * 0.1) * 5;
        const currentRadius = particle.radius + pulse;

        const x = centerX + Math.cos(particle.angle) * currentRadius;
        const y = centerY + Math.sin(particle.angle) * currentRadius;

        const sizePulse = Math.sin(time * 3 + index * 0.2) * 0.3 + 1;

        ctx.shadowBlur = 15;
        ctx.shadowColor = glowColor;

        ctx.beginPath();
        ctx.arc(x, y, particle.size * sizePulse, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.globalAlpha = particle.opacity;
        ctx.fill();
        ctx.globalAlpha = 1;
      });

      // Draw center glow
      const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 30);
      gradient.addColorStop(0, `${color}40`);
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

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
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
      }}
    />
  );
}

export default MiniAIOrb;