// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightAutoSidebar from 'starlight-auto-sidebar';

// ============================================
// 遊戲文件設定
// ============================================
// TODO: 修改以下設定以符合您的遊戲

const SITE_CONFIG = {
	// 網站標題（顯示在導航列）
	title: '蠕蟲之王',
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
				{
					tag: 'link',
					attrs: {
						rel: 'icon',
						type: 'image/png',
						href: '/favicon.png',
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
					label: '前言',
					slug: 'front-matter',
				},
				{
					label: '基本規則',
					autogenerate: { directory: 'basics' },
				},
				{
					label: '冒險者',
					autogenerate: { directory: 'adventurer' },
				},
				{
					label: '公會',
					slug: 'guild',
				},
				{
					label: '族裔',
					autogenerate: { directory: 'kith-and-kin' },
				},
				{
					label: '四大道途',
					autogenerate: { directory: 'four-paths' },
				},
				{
					label: '探索階段',
					autogenerate: { directory: 'crawl-phase' },
				},
				{
					label: '挑戰階段',
					autogenerate: { directory: 'challenge-phase' },
				},
				{
					label: '紮營階段',
					slug: 'camp-phase',
				},
				{
					label: '城市階段',
					autogenerate: { directory: 'city-phase' },
				},
				{
					label: '主持人指南',
					autogenerate: { directory: 'gamemastering' },
				},
				{
					label: '法術',
					autogenerate: { directory: 'sorcery' },
				},
				{
					label: '煉金術',
					slug: 'alchemy',
				},
				{
					label: '地城居民',
					autogenerate: { directory: 'dungeon-denizens' },
				},
				{
					label: '城市建構',
					autogenerate: { directory: 'city-creation' },
				},
				{
					label: '地下世界建構',
					autogenerate: { directory: 'underworld-creation' },
				}
			],
			plugins: [starlightAutoSidebar()],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});
