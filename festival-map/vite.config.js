import { defineConfig } from 'vite';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const ICON_DIR = fileURLToPath(new URL('./public/icons', import.meta.url));

// 관리자 편집 화면이 public/icons 폴더에 있는 아이콘 파일 목록을 알 수 있게 해 주는 개발 서버 전용 기능입니다.
// - 폴더 안의 PNG·SVG 파일 이름만 알려 줍니다(읽기 전용, 파일을 만들거나 지우지 않음).
// - npm run dev 때만 동작하고, 실제 배포(npm run build) 결과에는 들어가지 않습니다.
function iconListPlugin() {
  return {
    name: 'festival-icon-list',
    apply: 'serve',
    configureServer(server) {
      server.middlewares.use('/__festival/icons', (req, res) => {
        let files = [];
        try {
          files = fs
            .readdirSync(ICON_DIR, { withFileTypes: true })
            .filter((d) => d.isFile() && /\.(svg|png)$/i.test(d.name))
            .map((d) => `icons/${d.name}`)
            .sort((a, b) => a.localeCompare(b, 'ko'));
        } catch (err) {
          files = [];
        }
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.setHeader('Cache-Control', 'no-store');
        res.end(JSON.stringify({ folder: 'public/icons', files }));
      });
    },
  };
}

// 카카오 개발자 사이트에 등록한 주소(http://localhost:5173)와 맞추기 위해 포트를 5173으로 고정합니다.
export default defineConfig({
  plugins: [iconListPlugin()],
  server: {
    port: 5173,
    strictPort: true,
    open: false,
  },
});
