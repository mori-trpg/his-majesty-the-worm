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
					label: 'Front Matter',
					slug: 'front-matter',
				},
				{
					label: 'The Basics',
					autogenerate: { directory: 'basics' },
				},
				{
					label: 'The Adventurer',
					autogenerate: { directory: 'adventurer' },
				},
				{
					label: 'The Guild',
					slug: 'guild',
				},
				{
					label: 'Kith and Kin',
					autogenerate: { directory: 'kith-and-kin' },
				},
				{
					label: 'The Four Paths',
					autogenerate: { directory: 'four-paths' },
				},
				{
					label: 'Crawl Phase',
					autogenerate: { directory: 'crawl-phase' },
				},
				{
					label: 'Challenge Phase',
					autogenerate: { directory: 'challenge-phase' },
				},
				{
					label: 'Camp Phase',
					slug: 'camp-phase',
				},
				{
					label: 'City Phase',
					autogenerate: { directory: 'city-phase' },
				},
				{
					label: 'Gamemastering',
					autogenerate: { directory: 'gamemastering' },
				},
				{
					label: 'Sorcery',
					autogenerate: { directory: 'sorcery' },
				},
				{
					label: 'Alchemy',
					slug: 'alchemy',
				},
				{
					label: 'Dungeon Denizens',
					autogenerate: { directory: 'dungeon-denizens' },
				},
				{
					label: 'City Creation',
					autogenerate: { directory: 'city-creation' },
				},
				{
					label: 'Underworld Creation',
					autogenerate: { directory: 'underworld-creation' },
				}
			],
			plugins: [starlightAutoSidebar()],
			customCss: ['./src/styles/custom.css'],
		}),
	],
});
