// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// ============================================
// 遊戲文件設定
// ============================================
// TODO: 修改以下設定以符合您的遊戲

const SITE_CONFIG = {
	// 網站標題（顯示在導航列）
	title: 'Cairn',
	// 預設語言
	defaultLocale: 'zh-TW',
	localeLabel: '繁體中文',
	// SEO：設為 true 允許搜尋引擎索引
	allowIndexing: false,
};

// ============================================
// Astro 設定（通常不需修改）
// ============================================

export default defineConfig({
	markdown: {
		smartypants: false,
	},
	integrations: [
		starlight({
			title: SITE_CONFIG.title,
			head: [
				// SEO 設定
				{
					tag: 'meta',
					attrs: {
						name: 'robots',
						content: SITE_CONFIG.allowIndexing ? 'index, follow' : 'noindex, nofollow',
					},
				},
				// Open Graph 圖片（社群分享預覽）
				{
					tag: 'meta',
					attrs: {
						property: 'og:image',
						content: '/og-image.jpg',
					},
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image:width',
						content: '1200',
					},
				},
				{
					tag: 'meta',
					attrs: {
						property: 'og:image:height',
						content: '630',
					},
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:card',
						content: 'summary_large_image',
					},
				},
				{
					tag: 'meta',
					attrs: {
						name: 'twitter:image',
						content: '/og-image.jpg',
					},
				},
			],
			defaultLocale: 'root',
			locales: {
				root: { label: SITE_CONFIG.localeLabel, lang: SITE_CONFIG.defaultLocale },
			},
			// ============================================
			// 側邊欄設定
			// TODO: 根據您的內容結構修改
			// ============================================
			sidebar: [
				{
					label: '簡介',
					autogenerate: { directory: 'bilingual/introduction' },
				},
				{
					label: '玩家角色',
					autogenerate: { directory: 'bilingual/player-characters' },
				},
				{
					label: '技能與專長',
					autogenerate: { directory: 'bilingual/skills' },
				},
				{
					label: '戰鬥與傷害',
					autogenerate: { directory: 'bilingual/combat' },
				},
				{
					label: '魔法',
					autogenerate: { directory: 'bilingual/magic' },
				},
				{
					label: '旅行',
					autogenerate: { directory: 'bilingual/travel' },
				}
			],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});
