<template>
  <div class="w-full overflow-x-auto">
    <svg :viewBox="viewBox" class="w-full" style="min-height: 320px; max-height: 480px;">
      <!-- 接続線 -->
      <line
        v-for="(fm, i) in nodes"
        :key="'line-' + i"
        :x1="center.x"
        :y1="center.y"
        :x2="fm.x"
        :y2="fm.y"
        :stroke-width="fm.lineWidth"
        stroke="var(--color-border)"
        stroke-opacity="0.6"
      />

      <!-- 関係ラベル（線の中間） -->
      <text
        v-for="(fm, i) in nodes"
        :key="'label-' + i"
        :x="(center.x + fm.x) / 2"
        :y="(center.y + fm.y) / 2 - 6"
        text-anchor="middle"
        class="fill-text-muted"
        style="font-size: 10px;"
      >{{ fm.relationship }}</text>

      <!-- 家族ノード -->
      <g
        v-for="(fm, i) in nodes"
        :key="'node-' + i"
        :transform="`translate(${fm.x}, ${fm.y})`"
        class="cursor-pointer"
        @click="onNodeClick(fm)"
      >
        <circle
          :r="fm.radius"
          class="fill-bg-card stroke-border"
          :stroke-width="1.5"
        />
        <circle
          :r="fm.radius - 2"
          :fill="relationshipColor(fm.relationship)"
          opacity="0.15"
        />
        <text
          y="1"
          text-anchor="middle"
          dominant-baseline="middle"
          class="fill-text-primary"
          :style="{ fontSize: fm.fontSize + 'px', fontWeight: 500 }"
        >{{ truncName(fm.name) }}</text>
        <!-- イベント数バッジ -->
        <g v-if="fm.eventCount > 0" :transform="`translate(${fm.radius * 0.7}, ${-fm.radius * 0.7})`">
          <circle r="8" fill="var(--color-accent)" />
          <text y="1" text-anchor="middle" dominant-baseline="middle" fill="var(--color-bg-primary)" style="font-size: 9px; font-weight: 700;">{{ fm.eventCount }}</text>
        </g>
      </g>

      <!-- 中心ノード（本人） -->
      <g :transform="`translate(${center.x}, ${center.y})`">
        <circle r="40" class="fill-bg-card" stroke="var(--color-accent)" stroke-width="2.5" />
        <circle r="37" fill="var(--color-accent)" opacity="0.12" />
        <text y="-4" text-anchor="middle" dominant-baseline="middle" class="fill-text-primary" style="font-size: 14px; font-weight: 600;">{{ truncName(personName) }}</text>
        <text y="12" text-anchor="middle" class="fill-accent" style="font-size: 9px;">本人</text>
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
interface FamilyMember {
  id: number
  name: string
  relationship: string
  linkedPersonId?: number | null
  eventCount?: number
}

const props = defineProps<{
  personName: string
  family: FamilyMember[]
}>()

const emit = defineEmits<{
  navigate: [personId: number]
}>()

const CENTER_X = 250
const CENTER_Y = 200
const RADIUS_BASE = 130
const NODE_MIN = 24
const NODE_MAX = 42

const center = { x: CENTER_X, y: CENTER_Y }

const maxEventCount = computed(() =>
  Math.max(1, ...props.family.map(f => f.eventCount || 0))
)

const nodes = computed(() => {
  const count = props.family.length
  if (count === 0) return []

  return props.family.map((fm, i) => {
    const angle = (2 * Math.PI * i) / count - Math.PI / 2
    const ec = fm.eventCount || 0
    const ratio = ec / maxEventCount.value

    // ノードサイズ: イベント数に応じて拡大
    const radius = NODE_MIN + (NODE_MAX - NODE_MIN) * ratio
    // 線の太さ
    const lineWidth = 1.5 + 3.5 * ratio
    // フォントサイズ
    const fontSize = 10 + 3 * ratio
    // 距離（大きいノードは少し遠く）
    const dist = RADIUS_BASE + radius * 0.3

    return {
      ...fm,
      x: CENTER_X + Math.cos(angle) * dist,
      y: CENTER_Y + Math.sin(angle) * dist,
      radius,
      lineWidth,
      fontSize,
    }
  })
})

const viewBox = computed(() => {
  if (nodes.value.length === 0) return '100 50 300 300'
  const xs = [center.x, ...nodes.value.map(n => n.x)]
  const ys = [center.y, ...nodes.value.map(n => n.y)]
  const pad = 60
  const minX = Math.min(...xs) - pad
  const minY = Math.min(...ys) - pad
  const maxX = Math.max(...xs) + pad
  const maxY = Math.max(...ys) + pad
  return `${minX} ${minY} ${maxX - minX} ${maxY - minY}`
})

function relationshipColor(rel: string): string {
  const colors: Record<string, string> = {
    '配偶者': '#e8917a',
    '子供': '#7ac4e8',
    '父親': '#e8c97a',
    '母親': '#e8c97a',
    '親': '#e8c97a',
    '兄弟姉妹': '#7ae8a3',
    'その他': '#b0a090',
  }
  return colors[rel] || colors['その他']
}

function truncName(name: string): string {
  return name.length > 5 ? name.slice(0, 4) + '…' : name
}

function onNodeClick(fm: FamilyMember & { x: number; y: number }) {
  if (fm.linkedPersonId) {
    emit('navigate', fm.linkedPersonId)
  }
}
</script>
