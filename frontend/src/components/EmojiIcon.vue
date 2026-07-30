<script setup>
/**
 * EmojiIcon.vue — 跨浏览器一致的 emoji 图标（v2.3.3 加）
 *
 * 解决问题：
 * - Safari 用 Apple Color Emoji，Chrome 用 Segoe UI Emoji / Noto，样式差异大
 * - 🥀 等 emoji 跨平台视觉差异极大（Apple 是枯玫瑰，Google 是带叶玫瑰）
 * - @font-face 加 emoji 字体在 Safari 上有字距 bug
 *
 * 方案：Iconify + @iconify-json/twemoji（离线 SVG，0 运行时 HTTP）
 * - SVG 矢量，与系统 emoji 字体无关，所有浏览器渲染一致
 * - Vite 构建时按需 tree-shake，只打包用到的图标
 * - Twemoji CC-BY 4.0 许可（Twitter/X 设计）
 *
 * 用法：
 *   <EmojiIcon emoji="🏝️" />
 *   <EmojiIcon emoji="🌸" :size="24" />
 *   <EmojiIcon emoji="💧" size="1.2em" />
 *
 * 注意：
 * - 仅用于「功能性 UI 图标」（导航/按钮/状态指示）
 * - 正文/用户输入的 emoji 保持系统 emoji（更自然）
 */
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  emoji: {
    type: String,
    required: true,
  },
  size: {
    type: [String, Number],
    default: '1em',
  },
})

// 项目用到的功能性 emoji → Twemoji 图标名映射
// 完整列表见 https://icon-sets.iconify.design/twemoji/
const EMOJI_MAP = {
  '🏝️': 'twemoji:desert-island',
  '🌿': 'twemoji:herb',
  '🌱': 'twemoji:seedling',
  '🌸': 'twemoji:cherry-blossom',
  '🥀': 'twemoji:wilted-flower',
  '🍂': 'twemoji:fallen-leaf',
  '🍃': 'twemoji:leaf-fluttering-in-wind',
  '💧': 'twemoji:droplet',
  '🔔': 'twemoji:bell',
  '🎵': 'twemoji:musical-note',
  '🎻': 'twemoji:violin',
  '📖': 'twemoji:open-book',
  '🌙': 'twemoji:crescent-moon',
  '💛': 'twemoji:yellow-heart',
  '🎁': 'twemoji:gift',
  '🌊': 'twemoji:wave',
  '✨': 'twemoji:sparkles',
  '🎵': 'twemoji:musical-note',
  '🎶': 'twemoji:musical-notes',
  '🌙': 'twemoji:crescent-moon',
  '🌳': 'twemoji:deciduous-tree',
  '🌲': 'twemoji:evergreen-tree',
  '🐚': 'twemoji:spiral-shell',
  '🥂': 'twemoji:clinking-glasses',
  '🍾': 'twemoji:bottle-with-popping-cork',
  '🔍': 'twemoji:magnifying-glass-left',
  '⚙️': 'twemoji:gear',
  '🚪': 'twemoji:door',
  '📝': 'twemoji:memo',
  '⚙': 'twemoji:gear',
  '🍶': 'twemoji:sake',
  '👤': 'twemoji:bust-in-silhouette',
}

const iconName = computed(() => EMOJI_MAP[props.emoji] || null)

// 数字尺寸 → px，字符串原样
const sizeStr = computed(() => {
  const s = props.size
  if (typeof s === 'number') return `${s}px`
  return s
})
</script>

<template>
  <Icon
    v-if="iconName"
    :icon="iconName"
    :width="sizeStr"
    :height="sizeStr"
    class="emoji-icon"
  />
  <span v-else class="emoji-icon__fallback">{{ emoji }}</span>
</template>

<style scoped>
.emoji-icon {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
}

.emoji-icon__fallback {
  display: inline-block;
  vertical-align: middle;
  font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif;
}
</style>
