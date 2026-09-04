import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import type { AuditRow } from '../api';

interface ThreeDViewProps {
  auditLog: AuditRow[];
}

interface BarDatum {
  reason: string;
  at_risk: number;
  recovered: number;
}

function buildBarData(auditLog: AuditRow[]): BarDatum[] {
  const rs: Record<string, { at_risk: number; recovered: number }> = {};
  auditLog.forEach((r) => {
    const reason = r.failed_payments?.failure_reason ?? 'unknown';
    if (!rs[reason]) rs[reason] = { at_risk: 0, recovered: 0 };
    const amt = r.failed_payments?.amount ?? 0;
    // "at risk" = any non-skipped processed payment
    if (r.outcome !== 'skipped') rs[reason].at_risk += amt;
    if (r.outcome === 'success')  rs[reason].recovered += amt;
  });

  const entries: BarDatum[] = Object.entries(rs).map(([reason, v]) => ({
    reason: reason.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    at_risk: v.at_risk,
    recovered: v.recovered,
  }));

  // Compute totals for a leading "TOTAL" bar — matches app.py logic
  const total_at_risk   = entries.reduce((s, e) => s + e.at_risk, 0);
  const total_recovered = entries.reduce((s, e) => s + e.recovered, 0);
  return [
    { reason: 'TOTAL', at_risk: total_at_risk, recovered: total_recovered },
    ...entries,
  ];
}

export function ThreeDView({ auditLog }: ThreeDViewProps) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const data = buildBarData(auditLog);
    if (data.length === 0) return;

    // ── Constants (mirrors app.py) ──────────────────────────────────────────
    const MAX_H   = 4.5;
    const BAR_W   = 0.55;
    const GAP     = 0.2;
    const PAIR_W  = BAR_W * 2 + GAP;
    const SPACING = PAIR_W + 0.6;
    const MAX_VAL = Math.max(...data.map((d) => d.at_risk)) || 1;

    // ── Scene ───────────────────────────────────────────────────────────────
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0e1a);
    scene.fog = new THREE.FogExp2(0x0a0e1a, 0.04);

    const W = container.clientWidth;
    const H = container.clientHeight;

    const camera = new THREE.PerspectiveCamera(50, W / H, 0.1, 200);
    camera.position.set(0, 7, 18);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // ── Lighting ────────────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 0.35));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
    dirLight.position.set(10, 18, 8);
    dirLight.castShadow = true;
    scene.add(dirLight);
    const fill = new THREE.PointLight(0x4f8ef7, 0.6, 40);
    fill.position.set(-8, 6, -4);
    scene.add(fill);
    const rim = new THREE.PointLight(0x00d4aa, 0.5, 30);
    rim.position.set(8, 3, 6);
    scene.add(rim);

    // ── Grid floor ──────────────────────────────────────────────────────────
    scene.add(new THREE.GridHelper(32, 32, 0x1e293b, 0x1e293b));

    // ── Materials ───────────────────────────────────────────────────────────
    const matRisk = new THREE.MeshPhongMaterial({
      color: 0xff4d6d, emissive: 0x3d0010, shininess: 60,
      transparent: true, opacity: 0.92,
    });
    const matRec = new THREE.MeshPhongMaterial({
      color: 0x00d4aa, emissive: 0x003326, shininess: 80,
      transparent: true, opacity: 0.92,
    });
    const matBase = new THREE.MeshPhongMaterial({ color: 0x1e293b, shininess: 20 });

    // ── Bars ────────────────────────────────────────────────────────────────
    const barMeshes: THREE.Mesh[] = [];
    const totalWidth = data.length * SPACING;
    const startX     = -(totalWidth - SPACING) / 2;

    // Tooltip element
    const tooltip = document.createElement('div');
    Object.assign(tooltip.style, {
      position: 'absolute',
      background: 'rgba(17,24,39,0.95)',
      border: '1px solid #1e293b',
      borderRadius: '8px',
      padding: '10px 14px',
      color: '#f1f5f9',
      fontSize: '12px',
      pointerEvents: 'none',
      display: 'none',
      boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
      zIndex: '10',
    });
    container.appendChild(tooltip);

    data.forEach((d, i) => {
      const x = startX + i * SPACING;
      const hRisk = (d.at_risk   / MAX_VAL) * MAX_H || 0.05;
      const hRec  = (d.recovered / MAX_VAL) * MAX_H || 0.05;

      // At-risk bar
      const geoR  = new THREE.BoxGeometry(BAR_W, 1, BAR_W);
      const meshR = new THREE.Mesh(geoR, matRisk.clone());
      meshR.scale.y = 0.001;
      meshR.position.set(x - (BAR_W + GAP) / 2, 0, 0);
      meshR.castShadow = meshR.receiveShadow = true;
      (meshR as any).userData = { label: d.reason, type: 'At Risk',   val: d.at_risk,   targetH: hRisk };
      scene.add(meshR);
      barMeshes.push(meshR);

      // Recovered bar
      const geoG  = new THREE.BoxGeometry(BAR_W, 1, BAR_W);
      const meshG = new THREE.Mesh(geoG, matRec.clone());
      meshG.scale.y = 0.001;
      meshG.position.set(x + (BAR_W + GAP) / 2, 0, 0);
      meshG.castShadow = meshG.receiveShadow = true;
      (meshG as any).userData = { label: d.reason, type: 'Recovered', val: d.recovered, targetH: hRec };
      scene.add(meshG);
      barMeshes.push(meshG);

      // Base plate
      const geoB  = new THREE.BoxGeometry(PAIR_W + 0.1, 0.08, BAR_W + 0.1);
      const meshB = new THREE.Mesh(geoB, matBase);
      meshB.position.set(x, -0.04, 0);
      scene.add(meshB);

      // Label (canvas texture)
      const cv2d = document.createElement('canvas');
      cv2d.width = 256; cv2d.height = 64;
      const ctx = cv2d.getContext('2d')!;
      ctx.fillStyle = 'rgba(0,0,0,0)';
      ctx.fillRect(0, 0, 256, 64);
      ctx.fillStyle = '#94a3b8';
      ctx.font = 'bold 18px Inter,sans-serif';
      ctx.textAlign = 'center';
      const short = d.reason.length > 12 ? d.reason.slice(0, 12) + '…' : d.reason;
      ctx.fillText(short, 128, 36);
      const tex   = new THREE.CanvasTexture(cv2d);
      const spGeo = new THREE.PlaneGeometry(1.4, 0.35);
      const spMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false });
      const sp    = new THREE.Mesh(spGeo, spMat);
      sp.position.set(x, -0.35, BAR_W / 2 + 0.1);
      scene.add(sp);
    });

    // ── Star particles ───────────────────────────────────────────────────────
    const pGeo  = new THREE.BufferGeometry();
    const pCount = 300;
    const pPos   = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount * 3; i++) pPos[i] = (Math.random() - 0.5) * 60;
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    scene.add(new THREE.Points(pGeo, new THREE.PointsMaterial({ color: 0x334155, size: 0.15 })));

    // ── Orbit controls (manual, mirrors app.py) ──────────────────────────────
    let isDown = false, lastMouseX = 0, lastMouseY = 0;
    let theta = 0.2, phi = 0.45, radius = 18;

    const canvas = renderer.domElement;

    const onMouseDown = (e: MouseEvent) => { isDown = true; lastMouseX = e.clientX; lastMouseY = e.clientY; };
    const onMouseUp   = () => { isDown = false; };
    const onMouseMove = (e: MouseEvent) => {
      if (isDown) {
        const dx = (e.clientX - lastMouseX) * 0.008;
        const dy = (e.clientY - lastMouseY) * 0.008;
        theta  -= dx;
        phi     = Math.max(0.1, Math.min(1.4, phi + dy));
        lastMouseX = e.clientX;
        lastMouseY = e.clientY;
      }
      // Tooltip raycasting
      const rect   = canvas.getBoundingClientRect();
      const mouse  = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1,
      );
      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(barMeshes);
      if (hits.length) {
        const ud = (hits[0].object as any).userData;
        tooltip.style.display = 'block';
        tooltip.style.left    = `${e.clientX - rect.left + 14}px`;
        tooltip.style.top     = `${e.clientY - rect.top  - 10}px`;
        const color = ud.type === 'At Risk' ? '#ff4d6d' : '#00d4aa';
        tooltip.innerHTML = `<strong>${ud.label}</strong><br>
          <span style="color:#94a3b8">${ud.type}:</span>
          <span style="color:${color};font-weight:700">
            ₹${Number(ud.val).toLocaleString('en-IN', { minimumFractionDigits: 0 })}
          </span>`;
      } else {
        tooltip.style.display = 'none';
      }
    };
    const onWheel = (e: WheelEvent) => {
      radius = Math.max(6, Math.min(35, radius + e.deltaY * 0.04));
    };

    canvas.addEventListener('mousedown', onMouseDown);
    canvas.addEventListener('mouseup',   onMouseUp);
    canvas.addEventListener('mousemove', onMouseMove);
    canvas.addEventListener('wheel',     onWheel);

    // ── Animation loop ───────────────────────────────────────────────────────
    const clock = new THREE.Clock();
    let raf = 0;

    function animate() {
      raf = requestAnimationFrame(animate);
      const dt = clock.getDelta();

      // Grow bars
      barMeshes.forEach((m) => {
        const target = (m as any).userData.targetH || 0.05;
        if (m.scale.y < target) {
          m.scale.y = Math.min(target, m.scale.y + dt * 2.5);
          m.position.y = m.scale.y / 2;
        }
      });

      // Slow auto-orbit when not dragging
      if (!isDown) theta += dt * 0.08;

      camera.position.x = radius * Math.sin(theta) * Math.cos(phi);
      camera.position.y = radius * Math.sin(phi);
      camera.position.z = radius * Math.cos(theta) * Math.cos(phi);
      camera.lookAt(0, MAX_H / 2, 0);

      renderer.render(scene, camera);
    }
    animate();

    // ── Resize handler ───────────────────────────────────────────────────────
    const onResize = () => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    // ── Cleanup ──────────────────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      canvas.removeEventListener('mousedown', onMouseDown);
      canvas.removeEventListener('mouseup',   onMouseUp);
      canvas.removeEventListener('mousemove', onMouseMove);
      canvas.removeEventListener('wheel',     onWheel);
      renderer.dispose();
      // Dispose all geometries and materials
      scene.traverse((obj: THREE.Object3D) => {
        if (obj instanceof THREE.Mesh) {
          obj.geometry.dispose();
          if (Array.isArray(obj.material)) {
            (obj.material as THREE.Material[]).forEach((m: THREE.Material) => m.dispose());
          } else {
            (obj.material as THREE.Material).dispose();
          }
        }
      });
      if (container.contains(canvas))  container.removeChild(canvas);
      if (container.contains(tooltip)) container.removeChild(tooltip);
    };
  }, [auditLog]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: '#ff4d6d' }} />
          At Risk
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: 3, background: '#00d4aa' }} />
          Recovered
        </div>
        <span style={{ color: '#334155', fontSize: 11 }}>🖱 Drag to orbit · Scroll to zoom · Hover bars for details</span>
      </div>
      <div
        ref={mountRef}
        id="threed-canvas-mount"
        style={{ width: '100%', height: 520, borderRadius: 12, overflow: 'hidden', position: 'relative', background: '#0a0e1a' }}
      />
      {auditLog.length === 0 && (
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', paddingTop: 16 }}>
          No audit log data yet — run some payments via "Try It Live" to see the 3D chart.
        </p>
      )}
    </div>
  );
}

export default ThreeDView;
