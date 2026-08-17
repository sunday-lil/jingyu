// 一次性脚本：从 @iconify-json/twemoji 的 icons.json 提取项目用到的图标，
// 生成 frontend/src/assets/twemoji-icons.js（离线注册用，0 运行时 HTTP）。
// 用法：node scripts/extract_twemoji.mjs
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const src = JSON.parse(
  readFileSync(join(root, 'frontend/node_modules/@iconify-json/twemoji/icons.json'), 'utf8'),
)

// 与 EmojiIcon.vue 的 EMOJI_MAP 保持一致
const NEEDED = [
  'water-wave', 'herb', 'seedling', 'cherry-blossom', 'wilted-flower',
  'fallen-leaf', 'leaf-fluttering-in-wind', 'droplet', 'bell',
  'musical-note', 'violin', 'open-book', 'crescent-moon', 'yellow-heart',
  'wrapped-gift', 'sparkles', 'musical-notes', 'deciduous-tree', 'evergreen-tree',
  'spiral-shell', 'clinking-glasses', 'bottle-with-popping-cork',
  'left-pointing-magnifying-glass', 'gear', 'door', 'memo', 'amphora',
  'bust-in-silhouette',
]

function resolve(name, depth = 0) {
  if (depth > 5) return null
  if (src.icons[name]) return src.icons[name]
  const alias = src.aliases?.[name]
  if (alias) return resolve(alias.parent, depth + 1)
  return null
}

const out = {}
const missing = []
for (const name of NEEDED) {
  const data = resolve(name)
  if (data) out[name] = data
  else missing.push(name)
}

const body = `/**
 * twemoji-icons.js — 项目用到的 twemoji 图标离线数据（脚本生成，勿手改）
 * 生成方式：node scripts/extract_twemoji.mjs
 * 用途：EmojiIcon.vue 通过 addIcon 注册，实现 0 运行时 HTTP 请求。
 * 许可：Twemoji CC-BY 4.0（Twitter/X 设计）
 */
export default ${JSON.stringify(out)}
`

writeFileSync(join(root, 'frontend/src/assets/twemoji-icons.js'), body, 'utf8')
console.log(`OK: ${Object.keys(out).length}/${NEEDED.length} icons written`)
if (missing.length) {
  console.log('MISSING:', missing.join(', '))
  process.exit(1)
}
