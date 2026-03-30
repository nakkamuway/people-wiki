<template>
  <NuxtLayout name="default">
    <div class="space-y-6">
      <div class="flex items-center justify-between flex-wrap gap-4">
        <h1 class="font-serif text-3xl text-text-primary">Relationship Map</h1>
        <div class="flex items-center gap-3">
          <label class="text-sm text-text-secondary">Center:</label>
          <select
            v-model="centerId"
            class="bg-bg-card border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
          >
            <option :value="null">All (均等配置)</option>
            <option v-for="p in data?.people" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
      </div>

      <div v-if="!data" class="text-center py-20">
        <p class="text-text-muted">Loading...</p>
      </div>

      <div v-else class="bg-bg-secondary border border-border rounded-xl overflow-hidden relative" ref="containerRef">
        <svg
          ref="svgRef"
          :viewBox="viewBox"
          class="w-full"
          style="min-height: 500px; max-height: 80vh;"
          @mousedown="onSvgMouseDown"
          @mousemove="onSvgMouseMove"
          @mouseup="onSvgMouseUp"
          @mouseleave="onSvgMouseUp"
          @wheel.prevent="onWheel"
          @touchstart="onTouchStart"
          @touchmove.prevent="onTouchMove"
          @touchend="onTouchEnd"
        >
          <!-- Edges -->
          <line
            v-for="edge in edges"
            :key="edge.key"
            :x1="nodePositions[edge.from]?.x ?? 0"
            :y1="nodePositions[edge.from]?.y ?? 0"
            :x2="nodePositions[edge.to]?.x ?? 0"
            :y2="nodePositions[edge.to]?.y ?? 0"
            :stroke="edge.color"
            stroke-width="2"
            stroke-opacity="0.6"
          />

          <!-- Edge labels -->
          <text
            v-for="edge in edges"
            :key="'label-' + edge.key"
            :x="((nodePositions[edge.from]?.x ?? 0) + (nodePositions[edge.to]?.x ?? 0)) / 2"
            :y="((nodePositions[edge.from]?.y ?? 0) + (nodePositions[edge.to]?.y ?? 0)) / 2 - 6"
            text-anchor="middle"
            class="fill-text-muted pointer-events-none"
            style="font-size: 9px;"
          >{{ edge.label }}</text>

          <!-- Nodes -->
          <g
            v-for="node in nodes"
            :key="node.id"
            :transform="`translate(${nodePositions[node.id]?.x ?? 0}, ${nodePositions[node.id]?.y ?? 0})`"
            class="cursor-pointer"
            @mousedown.stop="onNodeMouseDown($event, node.id)"
            @touchstart.stop="onNodeTouchStart($event, node.id)"
            @click="onNodeClick(node.id)"
          >
            <circle
              :r="node.radius"
              class="fill-bg-card"
              :stroke="node.id === centerId ? '#c9a96e' : 'var(--color-border)'"
              :stroke-width="node.id === centerId ? 2.5 : 1.5"
            />
            <circle
              :r="node.radius - 2"
              :fill="node.id === centerId ? '#c9a96e' : '#b0a090'"
              :opacity="node.id === centerId ? 0.2 : 0.08"
            />
            <text
              y="-4"
              text-anchor="middle"
              dominant-baseline="middle"
              class="fill-text-primary pointer-events-none"
              :style="{ fontSize: node.fontSize + 'px', fontWeight: 500 }"
            >{{ truncName(node.name) }}</text>
            <text
              v-if="node.organization"
              y="10"
              text-anchor="middle"
              class="fill-text-muted pointer-events-none"
              style="font-size: 8px;"
            >{{ truncName(node.organization, 8) }}</text>
          </g>
        </svg>

        <!-- Legend -->
        <div class="absolute bottom-3 left-3 bg-bg-primary/80 backdrop-blur-sm border border-border rounded-lg p-3 text-xs space-y-1">
          <div class="flex items-center gap-2"><span class="w-4 h-0.5 inline-block" style="background: #e8917a;"></span><span class="text-text-muted">配偶者</span></div>
          <div class="flex items-center gap-2"><span class="w-4 h-0.5 inline-block" style="background: #e8c97a;"></span><span class="text-text-muted">親子</span></div>
          <div class="flex items-center gap-2"><span class="w-4 h-0.5 inline-block" style="background: #7ae8a3;"></span><span class="text-text-muted">兄弟姉妹</span></div>
          <div class="flex items-center gap-2"><span class="w-4 h-0.5 inline-block" style="background: #b0a090;"></span><span class="text-text-muted">その他</span></div>
        </div>
      </div>
    </div>
  </NuxtLayout>
</template>

<script setup lang="ts">
interface PersonNode {
  id: number
  name: string
  organization: string | null
  radius: number
  fontSize: number
  edgeCount: number
}

interface Edge {
  key: string
  from: number
  to: number
  label: string
  color: string
}

interface NodePosition {
  x: number
  y: number
  vx: number
  vy: number
  pinned: boolean
}

const { data } = useFetch<{
  people: { id: number; name: string; organization: string | null }[]
  relationships: { id: number; personId: number; name: string; relationship: string; linkedPersonId: number }[]
}>('/api/relationships')

const centerId = ref<number | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)
const containerRef = ref<HTMLElement | null>(null)

// Zoom / pan state
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)

// Simulation area
const SIM_W = 800
const SIM_H = 600
const NODE_MIN_R = 20
const NODE_MAX_R = 40

// Derived: edges (deduplicated)
const edges = computed<Edge[]>(() => {
  if (!data.value) return []
  const seen = new Set<string>()
  const result: Edge[] = []
  for (const rel of data.value.relationships) {
    if (!rel.linkedPersonId || rel.linkedPersonId === 0) continue
    const a = Math.min(rel.personId, rel.linkedPersonId)
    const b = Math.max(rel.personId, rel.linkedPersonId)
    const key = `${a}-${b}`
    if (seen.has(key)) continue
    seen.add(key)
    result.push({
      key,
      from: rel.personId,
      to: rel.linkedPersonId,
      label: rel.relationship,
      color: edgeColor(rel.relationship),
    })
  }
  return result
})

// Count edges per person
const edgeCountMap = computed<Record<number, number>>(() => {
  const map: Record<number, number> = {}
  for (const e of edges.value) {
    map[e.from] = (map[e.from] || 0) + 1
    map[e.to] = (map[e.to] || 0) + 1
  }
  return map
})

const maxEdgeCount = computed(() => Math.max(1, ...Object.values(edgeCountMap.value)))

// Derived: nodes
const nodes = computed<PersonNode[]>(() => {
  if (!data.value) return []
  return data.value.people.map(p => {
    const ec = edgeCountMap.value[p.id] || 0
    const ratio = ec / maxEdgeCount.value
    const radius = NODE_MIN_R + (NODE_MAX_R - NODE_MIN_R) * ratio
    const fontSize = 10 + 3 * ratio
    return { ...p, radius, fontSize, edgeCount: ec }
  })
})

// Force simulation positions
const nodePositions = reactive<Record<number, NodePosition>>({})
let animFrameId = 0
let draggingNodeId: number | null = null
let isPanning = false
let panStartX = 0
let panStartY = 0
let panStartPanX = 0
let panStartPanY = 0

const viewBox = computed(() => {
  const cx = SIM_W / 2 - panX.value
  const cy = SIM_H / 2 - panY.value
  const w = SIM_W / zoom.value
  const h = SIM_H / zoom.value
  return `${cx - w / 2} ${cy - h / 2} ${w} ${h}`
})

function edgeColor(rel: string): string {
  if (rel === '配偶者') return '#e8917a'
  if (['子供', '父親', '母親', '親'].includes(rel)) return '#e8c97a'
  if (rel === '兄弟姉妹') return '#7ae8a3'
  return '#b0a090'
}

function truncName(name: string, max = 5): string {
  return name.length > max ? name.slice(0, max - 1) + '…' : name
}

// Initialize positions in a circle
function initPositions() {
  const count = nodes.value.length
  if (count === 0) return
  const cx = SIM_W / 2
  const cy = SIM_H / 2
  const r = Math.min(SIM_W, SIM_H) * 0.35

  nodes.value.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2
    if (!nodePositions[node.id]) {
      nodePositions[node.id] = {
        x: cx + Math.cos(angle) * r,
        y: cy + Math.sin(angle) * r,
        vx: 0,
        vy: 0,
        pinned: false,
      }
    }
  })
}

// Force simulation step
function simulate() {
  const alpha = 0.3
  const damping = 0.85
  const repulsion = 8000
  const springLength = 150
  const springStrength = 0.02
  const centerStrength = 0.01
  const cx = SIM_W / 2
  const cy = SIM_H / 2

  const ids = nodes.value.map(n => n.id)

  // Repulsion (all pairs)
  for (let i = 0; i < ids.length; i++) {
    for (let j = i + 1; j < ids.length; j++) {
      const a = nodePositions[ids[i]]
      const b = nodePositions[ids[j]]
      if (!a || !b) continue
      let dx = a.x - b.x
      let dy = a.y - b.y
      let dist = Math.sqrt(dx * dx + dy * dy) || 1
      if (dist < 1) dist = 1
      const force = repulsion / (dist * dist)
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force
      if (!a.pinned) { a.vx += fx * alpha; a.vy += fy * alpha }
      if (!b.pinned) { b.vx -= fx * alpha; b.vy -= fy * alpha }
    }
  }

  // Spring (edges)
  for (const edge of edges.value) {
    const a = nodePositions[edge.from]
    const b = nodePositions[edge.to]
    if (!a || !b) continue
    const dx = b.x - a.x
    const dy = b.y - a.y
    const dist = Math.sqrt(dx * dx + dy * dy) || 1
    const displacement = dist - springLength
    const fx = (dx / dist) * displacement * springStrength
    const fy = (dy / dist) * displacement * springStrength
    if (!a.pinned) { a.vx += fx * alpha; a.vy += fy * alpha }
    if (!b.pinned) { b.vx -= fx * alpha; b.vy -= fy * alpha }
  }

  // Center gravity
  for (const id of ids) {
    const pos = nodePositions[id]
    if (!pos || pos.pinned) continue
    pos.vx += (cx - pos.x) * centerStrength * alpha
    pos.vy += (cy - pos.y) * centerStrength * alpha
  }

  // Apply velocity
  for (const id of ids) {
    const pos = nodePositions[id]
    if (!pos || pos.pinned) continue
    pos.vx *= damping
    pos.vy *= damping
    pos.x += pos.vx
    pos.y += pos.vy
  }

  // Pin center person
  if (centerId.value && nodePositions[centerId.value]) {
    nodePositions[centerId.value].x = cx
    nodePositions[centerId.value].y = cy
    nodePositions[centerId.value].vx = 0
    nodePositions[centerId.value].vy = 0
  }

  animFrameId = requestAnimationFrame(simulate)
}

// SVG coordinate conversion
function svgPoint(clientX: number, clientY: number) {
  if (!svgRef.value) return { x: 0, y: 0 }
  const pt = svgRef.value.createSVGPoint()
  pt.x = clientX
  pt.y = clientY
  const ctm = svgRef.value.getScreenCTM()
  if (!ctm) return { x: 0, y: 0 }
  const svgPt = pt.matrixTransform(ctm.inverse())
  return { x: svgPt.x, y: svgPt.y }
}

// Node drag (mouse)
function onNodeMouseDown(e: MouseEvent, id: number) {
  draggingNodeId = id
  const pos = nodePositions[id]
  if (pos) {
    pos.pinned = true
    const pt = svgPoint(e.clientX, e.clientY)
    pos.x = pt.x
    pos.y = pt.y
  }
}

// Node drag (touch)
function onNodeTouchStart(e: TouchEvent, id: number) {
  if (e.touches.length !== 1) return
  draggingNodeId = id
  const pos = nodePositions[id]
  if (pos) {
    pos.pinned = true
    const touch = e.touches[0]
    const pt = svgPoint(touch.clientX, touch.clientY)
    pos.x = pt.x
    pos.y = pt.y
  }
}

// SVG pan (mouse)
function onSvgMouseDown(e: MouseEvent) {
  if (draggingNodeId !== null) return
  isPanning = true
  panStartX = e.clientX
  panStartY = e.clientY
  panStartPanX = panX.value
  panStartPanY = panY.value
}

function onSvgMouseMove(e: MouseEvent) {
  if (draggingNodeId !== null) {
    const pos = nodePositions[draggingNodeId]
    if (pos) {
      const pt = svgPoint(e.clientX, e.clientY)
      pos.x = pt.x
      pos.y = pt.y
      pos.vx = 0
      pos.vy = 0
    }
    return
  }
  if (isPanning) {
    const scale = SIM_W / zoom.value
    const rect = svgRef.value?.getBoundingClientRect()
    if (!rect) return
    const factor = scale / rect.width
    panX.value = panStartPanX + (e.clientX - panStartX) * factor
    panY.value = panStartPanY + (e.clientY - panStartY) * factor
  }
}

function onSvgMouseUp() {
  if (draggingNodeId !== null) {
    const pos = nodePositions[draggingNodeId]
    if (pos) pos.pinned = (draggingNodeId === centerId.value)
    draggingNodeId = null
  }
  isPanning = false
}

// Touch pan
let lastTouchX = 0
let lastTouchY = 0

function onTouchStart(e: TouchEvent) {
  if (draggingNodeId !== null || e.touches.length !== 1) return
  isPanning = true
  lastTouchX = e.touches[0].clientX
  lastTouchY = e.touches[0].clientY
  panStartPanX = panX.value
  panStartPanY = panY.value
  panStartX = lastTouchX
  panStartY = lastTouchY
}

function onTouchMove(e: TouchEvent) {
  if (draggingNodeId !== null) {
    const pos = nodePositions[draggingNodeId]
    if (pos && e.touches.length === 1) {
      const touch = e.touches[0]
      const pt = svgPoint(touch.clientX, touch.clientY)
      pos.x = pt.x
      pos.y = pt.y
      pos.vx = 0
      pos.vy = 0
    }
    return
  }
  if (isPanning && e.touches.length === 1) {
    const scale = SIM_W / zoom.value
    const rect = svgRef.value?.getBoundingClientRect()
    if (!rect) return
    const factor = scale / rect.width
    panX.value = panStartPanX + (e.touches[0].clientX - panStartX) * factor
    panY.value = panStartPanY + (e.touches[0].clientY - panStartY) * factor
  }
}

function onTouchEnd() {
  if (draggingNodeId !== null) {
    const pos = nodePositions[draggingNodeId]
    if (pos) pos.pinned = (draggingNodeId === centerId.value)
    draggingNodeId = null
  }
  isPanning = false
}

// Zoom
function onWheel(e: WheelEvent) {
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  zoom.value = Math.max(0.3, Math.min(5, zoom.value * delta))
}

// Node click -> navigate
let mouseDownTime = 0
function onNodeClick(id: number) {
  // Only navigate if it wasn't a drag
  navigateTo(`/people/${id}`)
}

// Watch data and center changes
watch(() => data.value, () => {
  if (data.value) {
    initPositions()
  }
}, { immediate: true })

watch(centerId, (newId) => {
  // Unpin old center
  for (const id of Object.keys(nodePositions)) {
    const pos = nodePositions[Number(id)]
    if (pos) pos.pinned = false
  }
  // Pin new center
  if (newId && nodePositions[newId]) {
    nodePositions[newId].pinned = true
    nodePositions[newId].x = SIM_W / 2
    nodePositions[newId].y = SIM_H / 2
  }
  // Give a small kick to redistribute
  for (const id of Object.keys(nodePositions)) {
    const pos = nodePositions[Number(id)]
    if (pos && !pos.pinned) {
      pos.vx += (Math.random() - 0.5) * 10
      pos.vy += (Math.random() - 0.5) * 10
    }
  }
})

onMounted(() => {
  animFrameId = requestAnimationFrame(simulate)
})

onUnmounted(() => {
  cancelAnimationFrame(animFrameId)
})
</script>
