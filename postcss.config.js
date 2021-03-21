const path = require('path');
const cssnano = require('cssnano')

module.exports = (ctx) => ({
    plugins: [
        require('tailwindcss')(path.resolve(__dirname, 'tailwind.config.js')),
        require('autoprefixer'),
        process.env.NODE_ENV === 'production' ? cssnano({ preset: 'default' }) : null,
        ctx.env === 'production' && require('@fullhuman/postcss-purgecss')({
            content: [
                path.resolve(__dirname, 'templates/**/*.html')
            ],
            defaultExtractor: content => content.match(/[A-Za-z0-9-_:/]+/g) || []
        })
    ]
})