const {resolve} = require('path');

export default {
    base: '/static/',
    server: {
        host: 'localhost',
        port: 3000,
        open: false,
        watch: {
            usePolling: true,
            disableGlobbing: false,
        },
    },

    build: {
        outDir: resolve('./dist'),
        emptyOutDir: true,
        manifest: true,
        rollupOptions: {
            input: {
                'main.js': 'src/main.ts',
                // 'style.css': 'src/style.css',
            }
        },
    }
}
