/**
 * J.A.R.V.I.S. 3D Golden Holographic Neural Core
 * Marvel Stark Lab Specification — Golden / Amber Holographic Sphere
 * Features:
 *  - 3D projected particle lattice (spherical distribution) with neural connection filaments
 *  - Concentric rotating orbital rings (equatorial, oblique, polar) with mechanical tick marks
 *  - Central golden singularity with radial multi-stop luminescence
 *  - Audio / Voice reactive pulse wave ripples
 *  - Interactive touch & mouse 3D rotation
 *  - High-performance 60fps Canvas 2D engine with zero external dependencies
 */
(function (global) {
  'use strict';

  class JarvisHoloCore {
    constructor(canvas, options = {}) {
      this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
      if (!this.canvas) return;
      if (this.canvas._jarvisHoloInstance) {
        return this.canvas._jarvisHoloInstance;
      }
      this.canvas._jarvisHoloInstance = this;
      this.ctx = this.canvas.getContext('2d');
      this.options = Object.assign({
        particleCount: 160,
        baseRadius: 100,
        colorGold: '#ffb300',
        colorAmber: '#ff8c00',
        colorBright: '#fff4cc',
        autoRotate: true,
        interactive: true,
        soundReactive: true,
      }, options);

      this.rotX = 0.25;
      this.rotY = 0.0;
      this.rotZ = 0.0;
      this.targetRotX = 0.25;
      this.targetRotY = 0.0;
      this.speedY = 0.008;
      this.pulseEnergy = 0.0;
      this.audioLevel = 0.0;
      this.shockwaves = [];
      this.particles = [];
      this.isDragging = false;
      this.lastMouseX = 0;
      this.lastMouseY = 0;
      this.rafId = null;

      this.initParticles();
      this.bindEvents();
      this.resize();
      this.start();
    }

    initParticles() {
      this.particles = [];
      const count = this.options.particleCount;
      for (let i = 0; i < count; i++) {
        // Uniform spherical surface distribution (Fibonacci sphere / spherical coordinates)
        const phi = Math.acos(1 - 2 * (i + 0.5) / count);
        const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
        const rVariation = 0.88 + Math.random() * 0.24;
        this.particles.push({
          x: Math.sin(phi) * Math.cos(theta) * rVariation,
          y: Math.cos(phi) * rVariation,
          z: Math.sin(phi) * Math.sin(theta) * rVariation,
          size: 1.2 + Math.random() * 2.0,
          brightness: 0.5 + Math.random() * 0.5,
          pulseSpeed: 1.5 + Math.random() * 2.5,
          pulseOffset: Math.random() * Math.PI * 2,
        });
      }
    }

    bindEvents() {
      if (!this.options.interactive) return;

      this.canvas.style.touchAction = 'none';
      this.canvas.style.userSelect = 'none';
      this.canvas.style.webkitUserSelect = 'none';

      const onStart = (clientX, clientY) => {
        this.isDragging = true;
        this.lastMouseX = clientX;
        this.lastMouseY = clientY;
      };

      const onMove = (clientX, clientY) => {
        if (!this.isDragging) return;
        const dx = clientX - this.lastMouseX;
        const dy = clientY - this.lastMouseY;
        this.targetRotY += dx * 0.008;
        this.targetRotX += dy * 0.008;
        this.lastMouseX = clientX;
        this.lastMouseY = clientY;
      };

      const onEnd = () => {
        this.isDragging = false;
      };

      this.canvas.addEventListener('mousedown', (e) => onStart(e.clientX, e.clientY));
      window.addEventListener('mousemove', (e) => onMove(e.clientX, e.clientY));
      window.addEventListener('mouseup', onEnd);

      this.canvas.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
          if (e.cancelable) e.preventDefault();
          onStart(e.touches[0].clientX, e.touches[0].clientY);
        }
      }, { passive: false });

      this.canvas.addEventListener('touchmove', (e) => {
        if (this.isDragging && e.touches.length === 1) {
          if (e.cancelable) e.preventDefault();
          onMove(e.touches[0].clientX, e.touches[0].clientY);
        }
      }, { passive: false });

      window.addEventListener('touchmove', (e) => {
        if (this.isDragging && e.touches.length === 1) {
          if (e.cancelable) e.preventDefault();
          onMove(e.touches[0].clientX, e.touches[0].clientY);
        }
      }, { passive: false });

      this.canvas.addEventListener('touchend', () => {
        if (this.isDragging) onEnd();
      });

      window.addEventListener('touchend', onEnd);

      this.canvas.addEventListener('click', () => {
        this.pulse(1.0);
      });

      window.addEventListener('resize', () => this.resize());
      if (typeof ResizeObserver === 'function') {
        try {
          this._ro = new ResizeObserver(() => this.resize());
          this._ro.observe(this.canvas);
        } catch (_) {}
      }
    }

    resize() {
      const rect = this.canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
      const w = rect.width || this.canvas.clientWidth || 280;
      const h = rect.height || this.canvas.clientHeight || 180;
      const targetW = Math.max(1, Math.round(w * dpr));
      const targetH = Math.max(1, Math.round(h * dpr));
      if (this.canvas.width !== targetW || this.canvas.height !== targetH) {
        this.canvas.width = targetW;
        this.canvas.height = targetH;
      }
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      this.width = w;
      this.height = h;
      this.radius = Math.min(w, h) * 0.38;
    }

    pulse(amount = 0.8) {
      this.pulseEnergy = Math.min(this.pulseEnergy + amount, 2.0);
      this.shockwaves.push({
        radius: 0.1,
        maxRadius: this.radius * 1.5,
        opacity: 0.9,
        speed: 3.5 + amount * 2.0,
      });
      if (this.shockwaves.length > 5) this.shockwaves.shift();
    }

    setAudioLevel(level) {
      this.audioLevel = Math.max(0, Math.min(1, level));
      if (this.audioLevel > 0.4) {
        this.pulse(this.audioLevel * 0.3);
      }
    }

    project(x, y, z, r, cx, cy) {
      // Rotate around X
      let y1 = y * Math.cos(this.rotX) - z * Math.sin(this.rotX);
      let z1 = y * Math.sin(this.rotX) + z * Math.cos(this.rotX);
      // Rotate around Y
      let x2 = x * Math.cos(this.rotY) + z1 * Math.sin(this.rotY);
      let z2 = -x * Math.sin(this.rotY) + z1 * Math.cos(this.rotY);

      // Perspective projection
      const fov = 380;
      const scale = fov / (fov + z2 * r);
      return {
        x: cx + x2 * r * scale,
        y: cy + y1 * r * scale,
        z: z2,
        scale: scale,
      };
    }

    drawRing(cx, cy, r, pitch, yaw, segments = 36, dashed = false) {
      const ctx = this.ctx;
      ctx.save();
      const points = [];
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        let x = Math.cos(theta);
        let y = Math.sin(theta) * Math.sin(pitch);
        let z = Math.sin(theta) * Math.cos(pitch);

        // Apply yaw
        const x_yaw = x * Math.cos(yaw) + z * Math.sin(yaw);
        const z_yaw = -x * Math.sin(yaw) + z * Math.cos(yaw);

        const proj = this.project(x_yaw, y, z_yaw, r, cx, cy);
        points.push(proj);
      }

      ctx.beginPath();
      for (let i = 0; i < points.length; i++) {
        const pt = points[i];
        if (i === 0) ctx.moveTo(pt.x, pt.y);
        else ctx.lineTo(pt.x, pt.y);
      }

      if (dashed) {
        ctx.setLineDash([4, 6]);
      }
      ctx.stroke();
      ctx.restore();
    }

    render(time) {
      const ctx = this.ctx;
      const w = this.width;
      const h = this.height;
      const cx = w / 2;
      const cy = h / 2;
      const r = this.radius * (1 + this.pulseEnergy * 0.08 + this.audioLevel * 0.05);

      ctx.clearRect(0, 0, w, h);

      // Smooth rotation damping
      this.rotX += (this.targetRotX - this.rotX) * 0.08;
      this.rotY += (this.targetRotY - this.rotY) * 0.08;
      if (this.options.autoRotate && !this.isDragging) {
        this.targetRotY += this.speedY + this.pulseEnergy * 0.005;
      }
      this.pulseEnergy *= 0.94;

      // 1. Central Golden Singularity Glow (Marvel Lab Core)
      const corePulse = 1 + Math.sin(time * 0.004) * 0.12 + this.pulseEnergy * 0.4 + this.audioLevel * 0.3;
      const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, r * 0.85);
      grad.addColorStop(0.0, 'rgba(255, 255, 230, 0.95)');
      grad.addColorStop(0.12, 'rgba(255, 200, 50, 0.75)');
      grad.addColorStop(0.35, 'rgba(255, 140, 0, 0.35)');
      grad.addColorStop(0.70, 'rgba(255, 100, 0, 0.08)');
      grad.addColorStop(1.0, 'rgba(255, 80, 0, 0.0)');

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, r * 0.85 * corePulse, 0, Math.PI * 2);
      ctx.fill();

      // 2. Shockwave Rings
      for (let i = this.shockwaves.length - 1; i >= 0; i--) {
        const sw = this.shockwaves[i];
        sw.radius += sw.speed;
        sw.opacity *= 0.95;
        ctx.strokeStyle = `rgba(255, 215, 80, ${sw.opacity.toFixed(3)})`;
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.arc(cx, cy, sw.radius, 0, Math.PI * 2);
        ctx.stroke();
        if (sw.opacity < 0.02 || sw.radius > sw.maxRadius) {
          this.shockwaves.splice(i, 1);
        }
      }

      // 3. Concentric Orbital Rings (Equatorial, Oblique, Polar)
      ctx.strokeStyle = 'rgba(255, 185, 30, 0.45)';
      ctx.lineWidth = 1.2;
      this.drawRing(cx, cy, r * 1.05, 0, time * 0.0006, 64);

      ctx.strokeStyle = 'rgba(255, 215, 80, 0.65)';
      ctx.lineWidth = 1.0;
      this.drawRing(cx, cy, r * 0.95, Math.PI / 4, -time * 0.0009, 48, true);

      ctx.strokeStyle = 'rgba(255, 150, 0, 0.35)';
      ctx.lineWidth = 0.8;
      this.drawRing(cx, cy, r * 0.80, -Math.PI / 3, time * 0.0007, 36);

      // Concentric HUD outer reticle ring with degree markers
      ctx.strokeStyle = 'rgba(255, 190, 40, 0.28)';
      ctx.lineWidth = 1.0;
      ctx.beginPath();
      ctx.arc(cx, cy, r * 1.25, 0, Math.PI * 2);
      ctx.stroke();

      // Tick markers at 30-degree increments
      const ticks = 12;
      for (let t = 0; t < ticks; t++) {
        const angle = (t / ticks) * Math.PI * 2 + time * 0.0002;
        const x1 = cx + Math.cos(angle) * (r * 1.22);
        const y1 = cy + Math.sin(angle) * (r * 1.22);
        const x2 = cx + Math.cos(angle) * (r * 1.28);
        const y2 = cy + Math.sin(angle) * (r * 1.28);
        ctx.strokeStyle = t % 3 === 0 ? 'rgba(255, 230, 100, 0.7)' : 'rgba(255, 180, 20, 0.35)';
        ctx.lineWidth = t % 3 === 0 ? 1.5 : 0.8;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }

      // 4. Project and sort particles by depth (Z)
      const projected = [];
      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i];
        const proj = this.project(p.x, p.y, p.z, r, cx, cy);
        projected.push({
          pt: proj,
          orig: p,
          index: i,
        });
      }
      projected.sort((a, b) => a.pt.z - b.pt.z);

      // 5. Neural Filaments (connections between nearby particles)
      ctx.lineWidth = 0.6;
      const maxConnectDist = r * 0.38;
      const maxDistSq = maxConnectDist * maxConnectDist;
      for (let i = 0; i < projected.length; i += 2) {
        const p1 = projected[i].pt;
        for (let j = i + 1; j < Math.min(i + 7, projected.length); j++) {
          const p2 = projected[j].pt;
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const distSq = dx * dx + dy * dy;
          if (distSq < maxDistSq) {
            const alpha = (1 - Math.sqrt(distSq) / maxConnectDist) * 0.28 * Math.min(p1.scale, p2.scale);
            ctx.strokeStyle = `rgba(255, 195, 50, ${alpha.toFixed(3)})`;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      }

      // 6. Draw 3D Golden Particles
      for (let i = 0; i < projected.length; i++) {
        const item = projected[i];
        const pt = item.pt;
        const p = item.orig;
        const depthAlpha = Math.max(0.2, Math.min(1.0, (pt.z + 1.2) / 2.0));
        const pulse = Math.sin(time * 0.003 * p.pulseSpeed + p.pulseOffset) * 0.3 + 0.7;
        const size = p.size * pt.scale * (1 + this.pulseEnergy * 0.3);

        ctx.fillStyle = pt.z > 0.4
          ? `rgba(255, 255, 230, ${(depthAlpha * pulse).toFixed(2)})`
          : `rgba(255, 180, 30, ${(depthAlpha * pulse * 0.85).toFixed(2)})`;

        ctx.beginPath();
        ctx.arc(pt.x, pt.y, Math.max(0.6, size), 0, Math.PI * 2);
        ctx.fill();

        // Extra halo for frontmost bright nodes
        if (pt.z > 0.65 && p.brightness > 0.8) {
          ctx.fillStyle = `rgba(255, 220, 100, ${(depthAlpha * 0.3).toFixed(2)})`;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, size * 2.6, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 7. Core Singularity Center Ring
      ctx.strokeStyle = 'rgba(255, 240, 180, 0.85)';
      ctx.lineWidth = 1.8;
      ctx.beginPath();
      ctx.arc(cx, cy, 14 * corePulse, 0, Math.PI * 2);
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(cx, cy, 4 * corePulse, 0, Math.PI * 2);
      ctx.fill();

      // 8. HUD Telemetry Coordinates (tactical overlay matching Image 3)
      ctx.fillStyle = 'rgba(255, 200, 60, 0.75)';
      ctx.font = '9px "SFMono-Regular", Consolas, monospace';
      ctx.textAlign = 'left';
      const az = Math.floor(((this.rotY % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2) * (180 / Math.PI));
      const el = Math.floor(this.rotX * (180 / Math.PI));
      ctx.fillText(`AZ ${String(az).padStart(3, '0')}° // EL ${el >= 0 ? '+' : ''}${el}°`, 8, h - 10);
      ctx.textAlign = 'right';
      ctx.fillText(`CORE // SOVEREIGN 99.8%`, w - 8, h - 10);
    }

    start() {
      if (this.rafId) return;
      const loop = (time) => {
        this.render(time);
        this.rafId = requestAnimationFrame(loop);
      };
      this.rafId = requestAnimationFrame(loop);
    }

    stop() {
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
    }
  }

  global.JarvisHoloCore = JarvisHoloCore;

  // Auto-mount mobile holographic neural core immediately even if companion script was cached
  if (typeof document !== 'undefined') {
    const mountMobileIfPresent = () => {
      const mobileCanvas = document.getElementById('jarvisMobileHoloCore');
      if (mobileCanvas && !mobileCanvas._jarvisHoloInstance) {
        try {
          new JarvisHoloCore(mobileCanvas, { particleCount: 145, interactive: true });
        } catch (_) {}
      }
      const cockpitCanvas = document.getElementById('jarvisCockpitHoloCore');
      if (cockpitCanvas && !cockpitCanvas._jarvisHoloInstance) {
        try {
          new JarvisHoloCore(cockpitCanvas, { particleCount: 160, baseRadius: 40, colorGold: '#00f2fe', colorAmber: '#0072ff', colorBright: '#ffffff', interactive: true });
        } catch (_) {}
      }
    };
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', mountMobileIfPresent, { once: true });
    } else {
      mountMobileIfPresent();
    }
  }
})(typeof window !== 'undefined' ? window : this);
