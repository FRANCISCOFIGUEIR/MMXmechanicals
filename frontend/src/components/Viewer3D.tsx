import { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
export default function Viewer3D({ field, simId }) {
  const mountRef = useRef(null); const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!mountRef.current) return;
    const mount = mountRef.current; const width = mount.clientWidth; const height = 400;
    const scene = new THREE.Scene(); scene.background = new THREE.Color(0x07080d);
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000); camera.position.set(80, 60, 80);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); renderer.setSize(width, height); mount.appendChild(renderer.domElement);
    const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true;
    scene.add(new THREE.AmbientLight(0x404060, 0.5));
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8); dirLight.position.set(50, 80, 50); scene.add(dirLight);
    const boxGeo = new THREE.BoxGeometry(64, 64, 64); const edges = new THREE.EdgesGeometry(boxGeo);
    scene.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1e2330 })));
    const gridSize = 64; const planeGeo = new THREE.PlaneGeometry(gridSize, gridSize, gridSize - 1, gridSize - 1);
    const colors = new Float32Array(gridSize * gridSize * 3);
    for (let i = 0; i < gridSize; i++) for (let j = 0; j < gridSize; j++) {
      const x = i / gridSize, y = j / gridSize; let val = field === 'velocity' ? Math.sin(x * Math.PI * 2) * Math.cos(y * Math.PI * 2) * 0.5 + 0.5 : field === 'pressure' ? (1 - x) * (1 - y) : x * 0.8 + y * 0.2;
      const idx = (i * gridSize + j) * 3;
      colors[idx] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 3))); colors[idx + 1] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 2))); colors[idx + 2] = Math.max(0, Math.min(1, 1.5 - Math.abs(4 * val - 1)));
    }
    planeGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const plane = new THREE.Mesh(planeGeo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide, transparent: true, opacity: 0.8 })); plane.rotation.x = -Math.PI / 2; scene.add(plane);
    for (let s = 0; s < 8; s++) { const points = []; let x = 0, y = 32, z = (s - 4) * 8; for (let step = 0; step < 60; step++) { points.push(new THREE.Vector3(x, y + Math.sin(step * 0.1) * 5, z + Math.cos(step * 0.15) * 3)); x += 1.2; } scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), new THREE.LineBasicMaterial({ color: 0x00e5a0, transparent: true, opacity: 0.4 }))); }
    setLoading(false);
    let frameId; const animate = () => { frameId = requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); }; animate();
    return () => { cancelAnimationFrame(frameId); mount.removeChild(renderer.domElement); renderer.dispose(); };
  }, [field, simId]);
  return <div className="relative">{loading && <div className="absolute inset-0 flex items-center justify-center"><div className="w-8 h-8 rounded-full border-2 border-mmx-border border-t-mmx-accent animate-spin" /></div>}<div ref={mountRef} className="w-full rounded-xl overflow-hidden bg-mmx-bg" style={{ height: 400 }} /></div>;
}