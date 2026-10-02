import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useRef } from 'react'
import type { Mesh } from 'three'

/**
 * Toolchain check ONLY: a placeholder wireframe body that proves react-three-fiber + drei build
 * and render, and that the WebGL path works in the demo browser. The real asset view (machine
 * geometry, hotspots, component highlighting) is a product-page concern for a later milestone.
 */
function PlaceholderBody() {
  const mesh = useRef<Mesh>(null)

  useFrame((_, delta) => {
    if (!mesh.current) return
    mesh.current.rotation.y += delta * 0.35
    mesh.current.rotation.x += delta * 0.08
  })

  return (
    <mesh ref={mesh}>
      <boxGeometry args={[1.4, 1.4, 1.4]} />
      <meshStandardMaterial color="#38bdf8" wireframe />
    </mesh>
  )
}

export default function TwinPreview3D() {
  return (
    <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">3D twin toolchain</h2>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">
            @react-three/fiber + @react-three/drei
          </p>
        </div>
        <span className="rounded-full border border-slate-600/60 bg-slate-500/10 px-3 py-1 text-xs font-medium text-slate-300">
          placeholder geometry
        </span>
      </div>

      <div className="mt-3 h-48 w-full overflow-hidden rounded-lg border border-slate-800 bg-slate-950/60">
        <Canvas camera={{ position: [2.6, 2, 3.2], fov: 45 }} dpr={[1, 2]}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[4, 6, 3]} intensity={1.1} />
          <PlaceholderBody />
          <gridHelper args={[8, 16, '#1e293b', '#0f172a']} />
          <OrbitControls enablePan={false} minDistance={2.5} maxDistance={8} />
        </Canvas>
      </div>

      <p className="mt-2 text-[11px] text-slate-500">
        Drag to orbit. This is not a machine model — it is here so a WebGL regression shows up in M1, not
        on stage during the demo.
      </p>
    </section>
  )
}
