module.exports = {
    mode: 'jit',
    purge: ['../**/*.html', '../**/*.ts'],
    darkMode: false, // or 'media' or 'class'
    theme: {
        extend: {
            container: {
                center: true,
            },
        },
    },
    variants: {
        extend: {},
    },
    plugins: [],
}
