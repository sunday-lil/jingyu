/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        // 治愈系色彩系统（延续原项目视觉语言）
        mist: {
          50: '#FAF8F4',
          100: '#F9F6F0',
          200: '#F0EDE5',
          300: '#E5E0D5',
        },
        ink: {
          900: '#3D3327',
          700: '#5C4F3E',
          500: '#8B7B5E',
          400: '#A89B82',
          300: '#C5BCA8',
        },
        // 五音色（古琴音疗）
        gong: '#E8B8A8',   // 宫 - 土 - 脾
        shang: '#E8C5A8',  // 商 - 金 - 肺
        jue: '#A8C5A0',    // 角 - 木 - 肝
        zhi: '#E8A8B8',    // 徵 - 火 - 心
        yu: '#A8B8C5',     // 羽 - 水 - 肾
        // 强调色
        accent: '#B8A590',
        accentDark: '#8B7B5E',
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Source Han Serif SC"', '"STSong"', 'serif'],
        sans: ['"Noto Sans SC"', '"PingFang SC"', '"Microsoft YaHei"', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        '4xl': '32px',
      },
      animation: {
        'breathe': 'breathe 6s ease-in-out infinite',
        'float': 'float 4s ease-in-out infinite',
        'fade-up': 'fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        breathe: {
          '0%, 100%': { transform: 'scale(1)', opacity: '1' },
          '50%': { transform: 'scale(1.04)', opacity: '0.9' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
